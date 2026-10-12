"""Fetch ITSEE TEI XML transcriptions of John and extract classified variants.

Pipeline
--------
1. Parse each transcription into verse -> token list, reading only the
   first-hand text (``<rdg type="orig">`` inside ``<app>``), joining words that
   are split across line breaks, expanding nomina sacra, resolving the
   supralinear stroke for nu, and dropping marginal sigla, punctuation and
   editorial notes.  Tokens that contain editorially supplied text or a gap
   are flagged so that variants resting on reconstruction can be excluded.
2. Align every manuscript verse against the baseline verse with
   ``difflib.SequenceMatcher`` on *orthographically normalised* tokens, so
   that itacism, movable nu, elision and consonant gemination neither break
   the alignment nor surface as variants.
3. Classify every non-equal alignment block as addition, omission,
   word-order shift, morphological substitution or lexical substitution.
   Word-order shifts are recovered by pairing an omission with an addition
   (or two substitutions) of the same words inside one verse.
"""
import argparse
import difflib
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter

import pandas as pd
import requests

ITSEE_URLS = {
    'P66': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_P66_John.xml',
    'aleph': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_01_John.xml',
    'A': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_02_John.xml',
    'B': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_03_John.xml',
    'D': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_05_John.xml',
}

TARGET_MSS = ['P66', 'aleph', 'A', 'B', 'D']
TEI_NS = 'http://www.tei-c.org/ns/1.0'
GAP = '[GAP]'

# Verses per chapter in the standard versification of John (used for the
# coverage report only).
EXPECTED_VERSES = {
    1: 51, 2: 25, 3: 36, 4: 54, 5: 47, 6: 71, 7: 53, 8: 59, 9: 41, 10: 42,
    11: 57, 12: 50, 13: 38, 14: 31, 15: 27, 16: 33, 17: 26, 18: 40, 19: 42,
    20: 31, 21: 25,
}

VARIANT_TYPES = ['substitution_morphological', 'substitution_lexical',
                 'substitution_word_order', 'addition', 'omission']

# Nomina sacra as they appear inside <abbr type="nomSac"> in the ITSEE
# transcriptions (after lower-casing and diacritic stripping), mapped to the
# full form.  Only forms attested in the five transcriptions are listed;
# anything not in the table is left as transcribed.
NOMINA_SACRA = {
    # θεος
    'θς': 'θεος', 'θυ': 'θεου', 'θω': 'θεω', 'θν': 'θεον', 'θε': 'θεε',
    # κυριος
    'κς': 'κυριος', 'κυ': 'κυριου', 'κω': 'κυριω', 'κν': 'κυριον', 'κε': 'κυριε',
    # ιησους (two- and three-letter systems)
    'ις': 'ιησους', 'ιυ': 'ιησου', 'ιν': 'ιησουν',
    'ιης': 'ιησους', 'ιηυ': 'ιησου', 'ιην': 'ιησουν',
    # χριστος
    'χς': 'χριστος', 'χυ': 'χριστου', 'χω': 'χριστω', 'χν': 'χριστον',
    'χρς': 'χριστος', 'χρυ': 'χριστου', 'χρω': 'χριστω', 'χρν': 'χριστον',
    # πνευμα
    'πνα': 'πνευμα', 'πνς': 'πνευματος', 'πνι': 'πνευματι',
    'πνατος': 'πνευματος', 'πνατι': 'πνευματι', 'πντα': 'πνευματα',
    'πντων': 'πνευματων',
    # πατηρ
    'πηρ': 'πατηρ', 'πρς': 'πατρος', 'πρι': 'πατρι', 'πρα': 'πατερα',
    'περ': 'πατερ', 'πρες': 'πατερες', 'πρων': 'πατερων', 'πρας': 'πατερας',
    # υιος
    'υς': 'υιος', 'υυ': 'υιου', 'υω': 'υιω', 'υν': 'υιον', 'υε': 'υιε',
    # ανθρωπος
    'ανος': 'ανθρωπος', 'ανου': 'ανθρωπου', 'ανω': 'ανθρωπω', 'ανον': 'ανθρωπον',
    'ανε': 'ανθρωπε', 'ανοι': 'ανθρωποι', 'ανων': 'ανθρωπων',
    'ανοις': 'ανθρωποις', 'ανους': 'ανθρωπους',
    # ουρανος
    'ουνος': 'ουρανος', 'ουνου': 'ουρανου', 'ουνω': 'ουρανω', 'ουνον': 'ουρανον',
    'ουνοι': 'ουρανοι', 'ουνων': 'ουρανων', 'ουνοις': 'ουρανοις',
    'ουνους': 'ουρανους',
    # μητηρ, σωτηρ
    'μηρ': 'μητηρ', 'μρς': 'μητρος', 'μρι': 'μητρι', 'μρα': 'μητερα',
    'σηρ': 'σωτηρ', 'σωρ': 'σωτηρ', 'σρς': 'σωτηρος', 'σρι': 'σωτηρι',
    'σρα': 'σωτηρα',
    # names
    'ιηλ': 'ισραηλ', 'ισλ': 'ισραηλ', 'ιλημ': 'ιερουσαλημ', 'δαδ': 'δαυιδ',
    # σταυρος / σταυροω (staurogram forms)
    'στρος': 'σταυρος', 'στρου': 'σταυρου', 'στρω': 'σταυρω', 'στρον': 'σταυρον',
    'στρθη': 'σταυρωθη', 'στραν': 'σταυρωσαν', 'εστραν': 'εσταυρωσαν',
    'στρατε': 'σταυρωσατε', 'στρωσον': 'σταυρωσον',
}

_NOMINA_SACRA_BY_KEY = {}  # filled after clean_surface is defined

# Elided forms mapped to their full form (whole-token matches only).
ELISION = {
    'αλλ': 'αλλα', 'δ': 'δε', 'τ': 'τε', 'απ': 'απο', 'αφ': 'απο',
    'επ': 'επι', 'εφ': 'επι', 'υπ': 'υπο', 'υφ': 'υπο', 'μετ': 'μετα',
    'μεθ': 'μετα', 'κατ': 'κατα', 'καθ': 'κατα', 'παρ': 'παρα', 'δι': 'δια',
    'αντ': 'αντι', 'ανθ': 'αντι', 'ουδ': 'ουδε', 'μηδ': 'μηδε',
    'τουτ': 'τουτο',
}

# Forms with a movable final sigma (folded to the form without sigma).
MOVABLE_SIGMA = {'ουτωσ', 'αχρισ', 'μεχρισ'}

# Words whose final nu is not a movable nu and must never be stripped.
NU_EXCEPTIONS = {'εν', 'μεν', 'ην', 'ουδεν', 'μηδεν', 'ουν', 'συν', 'ειπον',
                 'εστιν'}


def _local(tag):
    return tag.split('}', 1)[1] if '}' in tag else tag


def strip_diacritics(text):
    """Remove accents, breathings, diaeresis and iota subscript."""
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')


def clean_surface(text):
    """Canonical surface form of a transcribed token: lower-case, diacritics
    stripped, supralinear stroke resolved to nu, no internal whitespace or
    punctuation."""
    text = strip_diacritics(text.lower())
    text = text.replace('¯', 'ν').replace('̄', 'ν')  # supralinear nu
    text = re.sub(r'[^\wα-ω]', '', text)  # drop †, ·, apostrophes, spaces
    text = re.sub(r'[0-9_]', '', text)
    return text


def _sigma_key(text):
    """Surface form with final sigma folded, used for dictionary look-ups."""
    return clean_surface(text).replace('ς', 'σ')


def normalize_orthography(word):
    """Collapse orthographic alternations that are not substantive variants:
    itacism (ει/ι, η/ι, οι/υ/ι, αι/ε), ω/ο, movable nu, elision and
    consonant gemination."""
    w = _sigma_key(word)
    if w in ELISION:
        w = ELISION[w]
    # Movable nu: only in the endings -σι(ν) and -ε(ν), never in short words
    # or in the listed exceptions.
    if w not in NU_EXCEPTIONS and len(w) >= 4 and re.search(r'(σι|ε)ν$', w):
        w = w[:-1]
    # Movable sigma: ουτω(ς), αχρι(ς), μεχρι(ς).
    if w in MOVABLE_SIGMA:
        w = w[:-1]
    w = w.replace('ου', '\x00')          # protect the ου digraph
    w = w.replace('ει', 'ι').replace('οι', 'ι').replace('υ', 'ι')
    w = w.replace('η', 'ι').replace('αι', 'ε').replace('ω', 'ο')
    w = w.replace('\x00', 'ου')
    w = re.sub(r'([λνσρμτπκ])\1', r'\1', w)  # gemination
    return w


def parse_verse_id(n):
    """Return (chapter, verse) for ``John.1.1`` or ``B04K1V1`` style ids."""
    if n.startswith('John.'):
        parts = n.split('.')
        if len(parts) >= 3 and parts[1].isdigit() and parts[2].isdigit():
            return int(parts[1]), int(parts[2])
    elif n.startswith('B04K'):
        match = re.search(r'K(\d+)V(\d+)', n)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None, None


_NOMINA_SACRA_BY_KEY.update({_sigma_key(k): v for k, v in NOMINA_SACRA.items()})


class Token:
    __slots__ = ('surface', 'norm', 'reconstructed')

    def __init__(self, surface, reconstructed=False):
        self.surface = surface
        self.norm = normalize_orthography(surface)
        self.reconstructed = reconstructed

    def __repr__(self):
        return self.surface


def _word_text(w):
    """Text of a <w> element: expand nomina sacra, keep <ex>/<unclear>/
    <supplied> text, skip marginal sigla and notes, join across <lb/>."""
    parts = []
    reconstructed = False

    def rec(el):
        nonlocal reconstructed
        tag = _local(el.tag)
        if tag in ('note', 'pc', 'fw') or (tag == 'seg' and el.get('type') == 'margin'):
            return
        if tag == 'gap':
            reconstructed = True
            return
        if tag == 'supplied':
            reconstructed = True
        if tag == 'abbr' and el.get('type') == 'nomSac':
            raw = clean_surface(''.join(el.itertext()))
            parts.append(_NOMINA_SACRA_BY_KEY.get(_sigma_key(raw), raw))
            return
        if el.text:
            parts.append(el.text)
        for child in el:
            rec(child)
            if child.tail:
                parts.append(child.tail)

    rec(w)
    return clean_surface(''.join(parts)), reconstructed


def _walk(el, out):
    """Collect first-hand tokens of an <ab> in document order."""
    tag = _local(el.tag)
    if tag == 'w':
        text, reconstructed = _word_text(el)
        if text:
            out.append(Token(text, reconstructed))
        return
    if tag == 'app':
        rdgs = [r for r in el if _local(r.tag) == 'rdg']
        chosen = [r for r in rdgs if r.get('type') == 'orig'] or rdgs[:1]
        for r in chosen:
            _walk(r, out)
        return
    if tag in ('note', 'pc', 'fw') or (tag == 'seg' and el.get('type') == 'margin'):
        return
    if tag == 'gap':
        out.append(Token(GAP, True))
        return
    for child in el:
        _walk(child, out)


def process_xml(file_path, ms_name=None):
    """Parse a transcription.

    Returns
    -------
    verses : dict  "J ch:v" -> list[Token]   (only verses with attested text)
    coverage : dict  chapter -> number of verses with attested text
    """
    root = ET.parse(file_path).getroot()
    verses, coverage = {}, {}
    for ab in root.iter(f'{{{TEI_NS}}}ab'):
        ch, v = parse_verse_id(ab.get('n', ''))
        if ch is None:
            continue
        tokens = []
        _walk(ab, tokens)
        if not any(t.surface != GAP for t in tokens):
            continue
        verses[f"J {ch}:{v}"] = tokens
        coverage[ch] = coverage.get(ch, 0) + 1
    return verses, coverage


def verse_text(tokens):
    return ' '.join(t.surface for t in tokens)


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

def _similarity(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def classify_substitution(base_tokens, ms_tokens, threshold=0.5):
    """Morphological vs lexical substitution.

    For equal-length blocks the character similarity is averaged over the
    positionally paired normalised tokens; for unequal blocks it is computed
    on the joined normalised strings.  A similarity above ``threshold`` is
    treated as morphological (same stem, different inflection)."""
    b = [t.norm for t in base_tokens]
    m = [t.norm for t in ms_tokens]
    if len(b) == len(m):
        score = sum(_similarity(x, y) for x, y in zip(b, m)) / len(b)
    else:
        score = _similarity(' '.join(b), ' '.join(m))
    return 'substitution_morphological' if score > threshold else 'substitution_lexical'


def align_verse(base_tokens, ms_tokens):
    """Return a list of variant blocks for one verse.

    Each block is a dict with keys type, i1, i2, j1, j2 (token spans in the
    baseline and manuscript), base (list of Token) and ms (list of Token)."""
    sm = difflib.SequenceMatcher(None, [t.norm for t in base_tokens],
                                 [t.norm for t in ms_tokens], autojunk=False)
    blocks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        b, m = base_tokens[i1:i2], ms_tokens[j1:j2]
        if tag == 'insert':
            vtype = 'addition'
        elif tag == 'delete':
            vtype = 'omission'
        elif sorted(t.norm for t in b) == sorted(t.norm for t in m):
            vtype = 'substitution_word_order'
        else:
            vtype = classify_substitution(b, m)
        blocks.append({'type': vtype, 'i1': i1, 'i2': i2, 'j1': j1, 'j2': j2,
                       'base': b, 'ms': m})
    return merge_transpositions(blocks, base_tokens, ms_tokens)


MAX_TRANSPOSITION_GAP = 8


def merge_transpositions(blocks, base_tokens, ms_tokens, max_gap=MAX_TRANSPOSITION_GAP):
    """Pair blocks that together form a word-order shift.

    difflib never emits a transposition as a single block: ``A B`` -> ``B A``
    becomes an omission of A plus an addition of A, and ``A x B`` ->
    ``B x A`` becomes two substitutions.  Two blocks p, q are merged when the
    baseline words of p equal the manuscript words of q and vice versa, and
    the blocks lie at most ``max_gap`` baseline tokens apart (a word omitted
    at one end of a verse and added at the other end is not a transposition
    but an omission plus an addition)."""
    used = [False] * len(blocks)
    merged = []
    for p in range(len(blocks)):
        if used[p]:
            continue
        bp, mp = blocks[p]['base'], blocks[p]['ms']
        partner = None
        for q in range(p + 1, len(blocks)):
            if used[q]:
                continue
            bq, mq = blocks[q]['base'], blocks[q]['ms']
            if blocks[q]['i1'] - blocks[p]['i2'] > max_gap:
                break
            if (sorted(t.norm for t in bp) == sorted(t.norm for t in mq) and
                    sorted(t.norm for t in mp) == sorted(t.norm for t in bq)):
                partner = q
                break
        if partner is None:
            merged.append(blocks[p])
            continue
        q = blocks[partner]
        used[p] = used[partner] = True
        merged.append({
            'type': 'substitution_word_order',
            'i1': blocks[p]['i1'], 'i2': q['i2'],
            'j1': blocks[p]['j1'], 'j2': q['j2'],
            'base': base_tokens[blocks[p]['i1']:q['i2']],
            'ms': ms_tokens[blocks[p]['j1']:q['j2']],
        })
    return merged


def extract_variants(ms_texts, base_ms, target_mss=TARGET_MSS, context=5):
    """Align every manuscript against ``base_ms`` and return a DataFrame."""
    rows, dropped = [], Counter()
    for verse_id, base_tokens in ms_texts[base_ms].items():
        chapter = int(verse_id.split()[1].split(':')[0])
        for ms in target_mss:
            if ms == base_ms or verse_id not in ms_texts[ms]:
                continue
            ms_tokens = ms_texts[ms][verse_id]
            for k, blk in enumerate(align_verse(base_tokens, ms_tokens)):
                if any(t.surface == GAP or t.reconstructed for t in blk['base'] + blk['ms']):
                    dropped[ms] += 1
                    continue
                base_reading = ' '.join(t.surface for t in blk['base']) or '[ADD]'
                ms_reading = ' '.join(t.surface for t in blk['ms']) or '[OMIT]'
                if not re.search(r'[α-ω]', base_reading + ms_reading):
                    continue
                b_ctx = base_tokens[max(0, blk['i1'] - context):blk['i2'] + context]
                m_ctx = ms_tokens[max(0, blk['j1'] - context):blk['j2'] + context]
                rows.append({
                    'chapter': chapter,
                    'verse': verse_id,
                    'manuscript': ms,
                    'base_reading': base_reading,
                    'ms_reading': ms_reading,
                    'type': blk['type'],
                    'base_context_10w': verse_text([t for t in b_ctx if t.surface != GAP]),
                    'ms_context_10w': verse_text([t for t in m_ctx if t.surface != GAP]),
                    'base_norm': ' '.join(t.norm for t in blk['base']),
                    'ms_norm': ' '.join(t.norm for t in blk['ms']),
                    'n_base_words': len(blk['base']),
                    'n_ms_words': len(blk['ms']),
                    'block_index': k,
                })
    df = pd.DataFrame(rows)
    if dropped:
        print("Variants dropped because they rest on supplied text or a gap: "
              + ', '.join(f"{ms}={n}" for ms, n in sorted(dropped.items())))
    return df


def write_type_counts(df, suffix, out_dir='outputs'):
    """Write per-manuscript counts of each variant type."""
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for ms in sorted(df['manuscript'].unique()):
        counts = df[df['manuscript'] == ms]['type'].value_counts()
        row = {'manuscript': ms}
        row.update({t: int(counts.get(t, 0)) for t in VARIANT_TYPES})
        row['total_variants'] = int(counts.sum())
        rows.append(row)
    path = f"{out_dir}/type_counts_full_{suffix}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def load_all_transcriptions(download=True):
    os.makedirs('data/xml', exist_ok=True)
    ms_texts, coverage_rows = {}, []
    for ms, url in ITSEE_URLS.items():
        filepath = f"data/xml/{ms}.xml"
        if not os.path.exists(filepath):
            if not download:
                raise FileNotFoundError(filepath)
            print(f"Downloading {ms}...")
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(r.content)
        texts, coverage = process_xml(filepath, ms)
        ms_texts[ms] = texts
        for ch in range(1, 22):
            v_count = coverage.get(ch, 0)
            total = EXPECTED_VERSES[ch]
            coverage_rows.append({
                'manuscript': ms, 'chapter': ch,
                'verses_available': v_count, 'verses_total': total,
                'coverage_pct': round(v_count / total * 100, 2),
            })
    return ms_texts, pd.DataFrame(coverage_rows)


def download_and_extract(base_ms='B'):
    print("Loading ITSEE XML transcriptions...")
    ms_texts, coverage_df = load_all_transcriptions()
    os.makedirs('outputs', exist_ok=True)
    coverage_df.to_csv('outputs/coverage_report.csv', index=False)
    print("Coverage report saved to outputs/coverage_report.csv")

    print(f"Extracting variants for John 1-21 against {base_ms}...")
    df = extract_variants(ms_texts, base_ms)
    output_target = f'data/variants_full_john_{base_ms}.csv'
    df.to_csv(output_target, index=False)
    print(f"Extracted {len(df)} substantive variants against {base_ms} to {output_target}")
    print(df['type'].value_counts().to_string())
    print("Type counts written to", write_type_counts(df, base_ms))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract scribal variants against a baseline MS.')
    parser.add_argument('--baseline', type=str, default='B', help='Baseline manuscript (P66, aleph, A, B, D)')
    args = parser.parse_args()
    download_and_extract(base_ms=args.baseline)
