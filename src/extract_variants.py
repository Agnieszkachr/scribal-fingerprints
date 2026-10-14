"""
Extract Variants
================

Parses the ITSEE TEI XML transcriptions, aligns each witness against the
Vaticanus (B) baseline verse by verse on orthographically normalised tokens,
and classifies every non-equal alignment block into the five-part typology:
addition, omission, word-order shift, morphological substitution, lexical
substitution.

TEI handling (per <w>):
  - first-hand text only: inside <app>, the <rdg type="orig"> reading
  - outermost <w> only (nested <w> are not counted twice)
  - words carried over a line, column or page break are joined
    (<lb break="no"/> inside <w>; <w part="I"> + <w part="F"> across <ab>)
  - nomina sacra (<abbr type="nomSac">) expanded from the attested-forms table
  - supralinear stroke resolved to ν; punctuation, daggers, apostrophes and
    diacritics dropped; <note>, <pc>, <fw> and marginal <seg> skipped
  - tokens containing <supplied> text are flagged as reconstructed; tokens
    containing <unclear> text are flagged as uncertain; a <gap> becomes a gap
    token, and variant blocks containing or adjoining one are always excluded
    (lost text has no reading to compare)

Alignment runs on normalised tokens (itacism, ω/ο, movable ν and ς, elision,
gemination folded), so orthographic alternation never surfaces as a variant.
Word-order shifts are recovered by pairing an omission with an addition (or
two substitutions) of the same words within a verse, at most
MAX_TRANSPOSITION_GAP baseline tokens apart.

Attestation policy:
  default            reconstructed and uncertain tokens count as attested
  --exclude-supplied variant blocks resting on supplied text are dropped
  --exclude-unclear  variant blocks resting on an uncertain token are dropped

Corpus-specific flag columns:
  - Mark:      disputed_ending (bool)
  - Matthew:   harmonisation_candidate (bool, placeholder)
  - Luke-Acts: western_non_interpolation (bool), volume, bezae_high_divergence (bool)

Usage:
    python -m src.extract_variants --corpus john [--baseline B]
        [--exclude-supplied] [--exclude-unclear]
"""

from __future__ import annotations

import argparse
import difflib
import logging
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd

from src.config import (
    RAW_DIR, VARIANTS_DIR, OUTPUTS_DIR, CORPORA,
    BASELINE_MANUSCRIPT, ensure_dirs,
)
from src.corpus_registry import CORPUS_REGISTRY, ITSEE_FILE_TEMPLATES
from src.download_itsee_data import parse_verse_id, parse_book_code, expected_book_codes
from src.utils.nomina_sacra import expand as expand_nomen_sacrum
from src.utils.lemma_lexicon import is_morphological
from src.utils.token_normalizer import clean_surface, normalize_orthography

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
GAP = "[GAP]"
CONTEXT_WORDS = 5
MAX_TRANSPOSITION_GAP = 8

VARIANT_TYPES = [
    "substitution_morphological", "substitution_lexical",
    "substitution_word_order", "addition", "omission",
]

# Elements whose text never belongs to a word: editorial notes, punctuation
# characters, running headers / folio numbers, marginal segments.
_SKIP_TAGS = {"note", "pc", "fw"}

VOL_PREFIX = {"mark": "Mk", "matthew": "Mt", "john": "J", "luke": "Lk", "acts": "Ac"}

# Attestation policy (set from the command line).
EXCLUDE_SUPPLIED = False
EXCLUDE_UNCLEAR = False


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

class Token:
    __slots__ = ("surface", "norm", "reconstructed", "uncertain")

    def __init__(self, surface: str, reconstructed: bool = False, uncertain: bool = False):
        self.surface = surface
        self.norm = normalize_orthography(surface) if surface != GAP else GAP
        self.reconstructed = reconstructed
        self.uncertain = uncertain

    def __repr__(self) -> str:
        return self.surface


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_skipped(el) -> bool:
    tag = _local(el.tag)
    return tag in _SKIP_TAGS or (tag == "seg" and el.get("type") == "margin")


def word_text(w) -> Tuple[str, bool, bool]:
    """Surface text of one <w>, plus (reconstructed, uncertain) flags."""
    parts: List[str] = []
    flags = {"reconstructed": False, "uncertain": False}

    def rec(el) -> None:
        tag = _local(el.tag)
        if _is_skipped(el):
            return
        if tag == "gap":
            flags["reconstructed"] = True
            return
        if tag == "supplied":
            flags["reconstructed"] = True
        if tag == "unclear":
            flags["uncertain"] = True
        if tag == "abbr" and el.get("type") == "nomSac":
            raw = clean_surface("".join(el.itertext()))
            parts.append(expand_nomen_sacrum(raw))
            return
        if el.text:
            parts.append(el.text)
        for child in el:
            rec(child)
            if child.tail:
                parts.append(child.tail)

    rec(w)
    return clean_surface("".join(parts)), flags["reconstructed"], flags["uncertain"]


def _walk(el, out: List[Token], raw_words: List) -> None:
    """Collect first-hand tokens of an <ab> in document order."""
    tag = _local(el.tag)
    if tag == "w":
        text, reconstructed, uncertain = word_text(el)
        if text:
            out.append(Token(text, reconstructed, uncertain))
            raw_words.append(el)
        return                        # outermost <w> only
    if tag == "app":
        rdgs = [r for r in el if _local(r.tag) == "rdg"]
        chosen = [r for r in rdgs if r.get("type") == "orig"] or rdgs[:1]
        for r in chosen:
            _walk(r, out, raw_words)
        return
    if _is_skipped(el):
        return
    if tag == "gap":
        out.append(Token(GAP, True))
        raw_words.append(None)
        return
    for child in el:
        _walk(child, out, raw_words)


def _ends_mid_word(last_w) -> bool:
    """True if this <w> is the head of a word continued in the next <ab>."""
    if last_w is None:
        return False
    if last_w.get("part") == "I":
        return True
    children = list(last_w)
    return bool(children) and _local(children[-1].tag) == "lb" and children[-1].get("break") == "no"


def process_xml(file_path: Path, corpus: str) -> Dict[str, List[Token]]:
    """Parse a TEI transcription into {verse_label: [Token, ...]}.

    Only verses with at least one attested (non-gap) token are returned.
    Verse labels are ``{V} {ch}:{v}`` with V in Mk, Mt, Lk, Ac, J.
    """
    root = ET.parse(str(file_path)).getroot()
    verses: Dict[str, List[Token]] = {}
    pending: Dict[str, Token] = {}        # verse_label -> head of a word split across <ab>
    wanted = expected_book_codes(corpus)
    foreign = rejoined = 0

    for ab in root.findall(".//tei:ab", TEI_NS):
        n = ab.get("n", "")
        book = parse_book_code(n)
        if wanted and book is not None and book not in wanted:
            foreign += 1
            continue
        ch, v, volume = parse_verse_id(n, corpus)
        if ch is None:
            continue
        prefix = VOL_PREFIX.get(volume, volume[:2].capitalize())
        label = f"{prefix} {ch}:{v}"

        tokens: List[Token] = []
        raw_words: List = []
        _walk(ab, tokens, raw_words)

        # Tail of a word whose head closed the preceding <ab part="I">.
        if label in pending and tokens:
            first_w = raw_words[0]
            if first_w is not None and first_w.get("part") == "F":
                head = pending.pop(label)
                tail = tokens[0]
                tokens[0] = Token(head.surface + tail.surface,
                                  head.reconstructed or tail.reconstructed,
                                  head.uncertain or tail.uncertain)
            else:
                tokens.insert(0, pending.pop(label))

        if ab.get("part") == "I" and tokens and _ends_mid_word(raw_words[-1]):
            pending[label] = tokens.pop()

        if label in verses:
            verses[label].extend(tokens)
            rejoined += 1
        else:
            verses[label] = tokens

    for label, head in pending.items():
        verses.setdefault(label, []).append(head)

    verses = {k: v for k, v in verses.items() if any(t.surface != GAP for t in v)}

    if foreign:
        logger.warning("%s: skipped %d <ab> element(s) belonging to a different book than '%s'",
                       file_path.name, foreign, corpus)
    if rejoined:
        logger.info("%s: rejoined %d verse(s) split across a page/column boundary",
                    file_path.name, rejoined)
    return verses


# ---------------------------------------------------------------------------
# Alignment and classification
# ---------------------------------------------------------------------------

def classify_substitution(base: List[Token], ms: List[Token]) -> str:
    """Morphological vs lexical substitution.

    Morphological if every positionally paired word on the two sides is a form
    of the same lexeme (lemma lexicon, with a character-similarity fallback for
    forms it does not contain; see ``src.utils.lemma_lexicon``); lexical
    otherwise, including any block in which a word has no partner.
    """
    if is_morphological([t.surface for t in base], [t.surface for t in ms]):
        return "substitution_morphological"
    return "substitution_lexical"


def align_verse(base: List[Token], ms: List[Token]) -> List[Dict[str, Any]]:
    """Variant blocks for one verse: dicts with type, i1, i2, j1, j2, base, ms."""
    sm = difflib.SequenceMatcher(None, [t.norm for t in base], [t.norm for t in ms], autojunk=False)
    blocks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        b, m = base[i1:i2], ms[j1:j2]
        if tag == "insert":
            vtype = "addition"
        elif tag == "delete":
            vtype = "omission"
        elif sorted(t.norm for t in b) == sorted(t.norm for t in m):
            vtype = "substitution_word_order"
        else:
            vtype = classify_substitution(b, m)
        blocks.append({"type": vtype, "i1": i1, "i2": i2, "j1": j1, "j2": j2, "base": b, "ms": m})
    return merge_transpositions(blocks, base, ms)


def merge_transpositions(blocks, base, ms, max_gap: int = MAX_TRANSPOSITION_GAP):
    """Pair blocks that together form a word-order shift.

    ``A B`` -> ``B A`` is emitted by difflib as an omission of A plus an
    addition of A; ``A x B`` -> ``B x A`` as two substitutions. Blocks p and q
    are merged when the baseline words of p equal the witness words of q and
    vice versa, and q starts at most ``max_gap`` baseline tokens after p ends.
    """
    used = [False] * len(blocks)
    merged = []
    for p in range(len(blocks)):
        if used[p]:
            continue
        bp, mp = blocks[p]["base"], blocks[p]["ms"]
        partner = None
        for q in range(p + 1, len(blocks)):
            if used[q]:
                continue
            if blocks[q]["i1"] - blocks[p]["i2"] > max_gap:
                break
            bq, mq = blocks[q]["base"], blocks[q]["ms"]
            if (sorted(t.norm for t in bp) == sorted(t.norm for t in mq)
                    and sorted(t.norm for t in mp) == sorted(t.norm for t in bq)):
                partner = q
                break
        if partner is None:
            merged.append(blocks[p])
            continue
        q = blocks[partner]
        used[p] = used[partner] = True
        merged.append({
            "type": "substitution_word_order",
            "i1": blocks[p]["i1"], "i2": q["i2"],
            "j1": blocks[p]["j1"], "j2": q["j2"],
            "base": base[blocks[p]["i1"]:q["i2"]],
            "ms": ms[blocks[p]["j1"]:q["j2"]],
        })
    return merged


def touches_gap(blk: Dict[str, Any], ms: List[Token]) -> bool:
    """True if a variant block contains or adjoins a physical gap in the witness.

    A ``<gap>`` is text the witness has lost; it has no reading to compare. A
    block containing a gap token, or an omission whose insertion point in the
    witness sits next to one, compares the baseline with missing text and is
    not a variant under any attestation policy. Editorially supplied text is a
    different case (it has a reading) and is governed by --exclude-supplied.
    """
    if any(t.surface == GAP for t in blk["base"] + blk["ms"]):
        return True
    j1, j2 = blk["j1"], blk["j2"]
    neighbours = []
    if j1 > 0:
        neighbours.append(ms[j1 - 1])
    if j2 < len(ms):
        neighbours.append(ms[j2])
    return any(t.surface == GAP for t in neighbours)


def _text(tokens: List[Token]) -> str:
    return " ".join(t.surface for t in tokens if t.surface != GAP)


# ---------------------------------------------------------------------------
# Corpus extraction
# ---------------------------------------------------------------------------

def _parse_label(verse_id: str, corpus: str) -> Tuple[str, int, int, Optional[str]]:
    m = re.match(r"(\w+)\s+(\d+):(\d+)", verse_id)
    prefix, chapter, verse_num = m.group(1), int(m.group(2)), int(m.group(3))
    volume = None
    if corpus == "luke_acts":
        volume = "luke" if prefix == "Lk" else "acts"
        if volume == "acts":
            chapter += 24
    return prefix, chapter, verse_num, volume


def extract_rows(corpus: str, ms_texts: Dict[str, Dict[str, List[Token]]],
                 base_ms: str) -> Tuple[List[Dict[str, Any]], Counter]:
    reg = CORPUS_REGISTRY.get(corpus, {})
    flags = reg.get("corpus_specific_flags", {})
    disputed_endings = set(flags.get("disputed_ending_verses", []))
    western_non_interps = set(flags.get("western_non_interpolations", []))

    if corpus == "luke_acts" and f"{base_ms}_acts" in ms_texts:
        passes = [
            (base_ms, {s: d for s, d in ms_texts.items() if not s.endswith("_acts")}),
            (f"{base_ms}_acts", {s: d for s, d in ms_texts.items() if s.endswith("_acts")}),
        ]
    else:
        passes = [(base_ms, {s: d for s, d in ms_texts.items() if s != base_ms})]

    rows: List[Dict[str, Any]] = []
    dropped: Counter = Counter()
    lacuna: Counter = Counter()

    for pass_base, witnesses in passes:
        for verse_id, base_tokens in ms_texts[pass_base].items():
            _, chapter, verse_num, volume = _parse_label(verse_id, corpus)
            for siglum, ms_dict in witnesses.items():
                if siglum == pass_base or verse_id not in ms_dict:
                    continue
                out_siglum = siglum[:-5] if siglum.endswith("_acts") else siglum
                ms_tokens = ms_dict[verse_id]
                for k, blk in enumerate(align_verse(base_tokens, ms_tokens)):
                    toks = blk["base"] + blk["ms"]
                    if touches_gap(blk, ms_tokens):
                        lacuna[out_siglum] += 1
                        continue
                    reconstructed = any(t.reconstructed for t in toks)
                    uncertain = any(t.uncertain for t in toks)
                    if (EXCLUDE_SUPPLIED and reconstructed) or (EXCLUDE_UNCLEAR and uncertain):
                        dropped[out_siglum] += 1
                        continue
                    base_reading = _text(blk["base"]) or "[ADD]"
                    ms_reading = _text(blk["ms"]) or "[OMIT]"
                    if not re.search(r"[α-ω]", base_reading + ms_reading):
                        continue
                    b_ctx = base_tokens[max(0, blk["i1"] - CONTEXT_WORDS):blk["i2"] + CONTEXT_WORDS]
                    m_ctx = ms_tokens[max(0, blk["j1"] - CONTEXT_WORDS):blk["j2"] + CONTEXT_WORDS]
                    row: Dict[str, Any] = {
                        "corpus": corpus,
                        "chapter": chapter,
                        "verse": verse_id,
                        "manuscript": out_siglum,
                        "variant_type": blk["type"],
                        "baseline_reading": base_reading,
                        "manuscript_reading": ms_reading,
                        "base_context_10w": _text(b_ctx),
                        "ms_context_10w": _text(m_ctx),
                        "cosine_distance": None,       # filled by embed_variants
                        "base_norm": " ".join(t.norm for t in blk["base"] if t.surface != GAP),
                        "ms_norm": " ".join(t.norm for t in blk["ms"] if t.surface != GAP),
                        "n_base_words": sum(t.surface != GAP for t in blk["base"]),
                        "n_ms_words": sum(t.surface != GAP for t in blk["ms"]),
                        "block_index": k,
                        "reconstructed": reconstructed,
                        "uncertain": uncertain,
                    }
                    if corpus == "mark":
                        row["disputed_ending"] = f"{chapter}:{verse_num}" in disputed_endings
                    elif corpus == "matthew":
                        row["harmonisation_candidate"] = False
                    elif corpus == "luke_acts":
                        row["volume"] = volume
                        row["western_non_interpolation"] = f"{chapter}:{verse_num}" in western_non_interps
                        row["bezae_high_divergence"] = (out_siglum == "D" and volume == "acts")
                    rows.append(row)
    if lacuna:
        logger.info("Blocks adjoining a physical gap in the witness (not variants, always excluded): %s",
                    ", ".join(f"{m}={n}" for m, n in sorted(lacuna.items())))
    return rows, dropped


def coverage_report(corpus: str, ms_texts: Dict[str, Dict[str, List[Token]]]) -> pd.DataFrame:
    """Verses with attested text per witness and chapter against the expected count."""
    reg = CORPUS_REGISTRY.get(corpus, {})
    expected = dict(reg.get("expected_verses_per_chapter", {}))
    if corpus == "luke_acts":
        expected = dict(reg.get("expected_verses_per_chapter_luke", {}))
        for k, v in reg.get("expected_verses_per_chapter_acts", {}).items():
            expected[k + 24] = v

    data = []
    for siglum in sorted({s[:-5] if s.endswith("_acts") else s for s in ms_texts}):
        ch_counts: Dict[int, int] = {}
        counted = set()
        for key in (siglum, f"{siglum}_acts"):
            for vid in ms_texts.get(key, {}):
                prefix, ch, _, _ = _parse_label(vid, corpus)
                if corpus == "luke_acts" and prefix not in ("Lk", "Ac"):
                    continue
                if vid in counted:
                    continue
                counted.add(vid)
                ch_counts[ch] = ch_counts.get(ch, 0) + 1
        for ch, exp in expected.items():
            avail = ch_counts.get(ch, 0)
            if exp and avail > exp:
                logger.error("coverage: %s chapter %d counts %d verses against %d expected",
                             siglum, ch, avail, exp)
            data.append({
                "manuscript": siglum, "chapter": ch,
                "verses_available": avail, "verses_total": exp,
                "coverage_pct": round(avail / exp * 100, 2) if exp else 0,
            })
    return pd.DataFrame(data)


def type_counts(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ms in sorted(df["manuscript"].unique()):
        counts = df.loc[df["manuscript"] == ms, "variant_type"].value_counts()
        row = {"manuscript": ms}
        row.update({t: int(counts.get(t, 0)) for t in VARIANT_TYPES})
        row["total_variants"] = int(counts.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def load_corpus(corpus: str, raw_dir: Optional[Path] = None) -> Dict[str, Dict[str, List[Token]]]:
    raw_dir = raw_dir or RAW_DIR / corpus
    ms_texts: Dict[str, Dict[str, List[Token]]] = {}
    for siglum, filename in ITSEE_FILE_TEMPLATES.get(corpus, {}).items():
        path = raw_dir / filename
        if not path.exists():
            logger.warning("XML not found for %s: %s — skipping.", siglum, path)
            continue
        ms_texts[siglum] = process_xml(path, corpus)
        logger.info("Parsed %s: %d verses with attested text", siglum, len(ms_texts[siglum]))
    return ms_texts


def extract_for_corpus(corpus: str, base_ms: str = "B",
                       output_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    ensure_dirs()
    ms_texts = load_corpus(corpus)
    if not ms_texts:
        logger.error("No XML files found for '%s' in %s.", corpus, RAW_DIR / corpus)
        return None
    if base_ms not in ms_texts:
        logger.error("Baseline manuscript '%s' not available — aborting.", base_ms)
        return None

    rows, dropped = extract_rows(corpus, ms_texts, base_ms)
    df = pd.DataFrame(rows)
    output_path = output_path or VARIANTS_DIR / (
        f"{corpus}_variants.csv" if base_ms == BASELINE_MANUSCRIPT
        else f"{corpus}_variants_{base_ms}.csv")
    df.to_csv(output_path, index=False)
    logger.info("Extracted %d variants for '%s' against %s → %s", len(df), corpus, base_ms, output_path)
    if dropped:
        logger.info("Blocks dropped under the attestation policy: %s",
                    ", ".join(f"{m}={n}" for m, n in sorted(dropped.items())))

    out_dir = OUTPUTS_DIR / corpus
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if base_ms == BASELINE_MANUSCRIPT else f"_{base_ms}"
    if EXCLUDE_SUPPLIED:
        suffix += "_drop_supplied"
    if EXCLUDE_UNCLEAR:
        suffix += "_drop_unclear"
    coverage_report(corpus, ms_texts).to_csv(out_dir / f"coverage_report{suffix}.csv", index=False)
    if len(df):
        type_counts(df).to_csv(out_dir / f"type_counts_{corpus}{suffix}.csv", index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and classify variants for a corpus.")
    parser.add_argument("--corpus", required=True, choices=CORPORA)
    parser.add_argument("--baseline", default=BASELINE_MANUSCRIPT,
                        help="Baseline witness siglum (default: %(default)s)")
    parser.add_argument("--exclude-supplied", action="store_true",
                        help="Drop variant blocks resting on <supplied> text.")
    parser.add_argument("--exclude-unclear", action="store_true",
                        help="Drop variant blocks resting on <unclear> text.")
    parser.add_argument("--output", type=Path, default=None,
                        help="Variant CSV path (default: data/variants/{corpus}_variants.csv)")
    args = parser.parse_args()

    global EXCLUDE_SUPPLIED, EXCLUDE_UNCLEAR
    EXCLUDE_SUPPLIED = args.exclude_supplied
    EXCLUDE_UNCLEAR = args.exclude_unclear
    logger.info("Attestation policy: supplied=%s unclear=%s",
                "excluded" if EXCLUDE_SUPPLIED else "included",
                "excluded" if EXCLUDE_UNCLEAR else "included")
    extract_for_corpus(args.corpus, base_ms=args.baseline, output_path=args.output)


if __name__ == "__main__":
    main()
