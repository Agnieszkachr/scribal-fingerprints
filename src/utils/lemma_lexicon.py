"""Same lexeme or different lexeme: the decision behind morphological vs
lexical substitution.

Two word forms are forms of the same lexeme when the lexicon assigns them a
common lemma. The lexicon (``data/morphgnt_form_lemmas.tsv``) maps every word
form of the MorphGNT SBLGNT to its lemma(s), so suppletive forms (ειπον/λεγω,
ηλθον/ερχομαι) resolve to one lexeme and compounds (επερωταω/ερωταω) to two.

A witness spelling that the lexicon does not contain is first looked up on
its orthographic alignment key (itacism, ω/ο and the other alternations of
``normalize_orthography`` folded), so that ερχωμαι is read as ερχομαι. A form
still not found is the same lexeme as its partner if it is close to some
attested form of the partner's lemma (character similarity of the alignment
keys at least ``FORM_MATCH_CUTOFF``): ηνυξεν against the forms of ανοιγω,
ματης against those of μαθητης. If neither word is found, the two are compared
with each other (same lexeme above ``FALLBACK_THRESHOLD``). Alternative
spellings of one proper name that the lexicon lemmatises separately
(Μαρια/Μαριαμ) count as one lexeme.

Before comparison, crasis is resolved (καγω -> και εγω, καν -> και εαν,
ουδεν -> ουδε εν). A replacement block is a morphological substitution only if
both sides have the same number of words and every positionally paired word
is the same lexeme; a word without a partner makes the block lexical.
"""

from __future__ import annotations

import difflib
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Set

from src.utils.token_normalizer import normalize_orthography

LEXICON_PATH = Path(__file__).resolve().parent / "data" / "morphgnt_form_lemmas.tsv"
FALLBACK_THRESHOLD = 0.5
FORM_MATCH_CUTOFF = 0.8

# Lemmas that are alternative spellings of one proper name.
NAME_VARIANTS = [{"μαρια", "μαριαμ"}, {"βηθσαιδα", "βηθσαιδαν"}, {"ιεροσολυμα", "ιερουσαλημ"}]

CRASIS = {
    "καγω": "και εγω", "καν": "και εαν", "καμε": "και εμε", "καμοι": "και εμοι",
    "κακει": "και εκει", "κακειθεν": "και εκειθεν", "κακεινοσ": "και εκεινοσ",
    "κακεινοι": "και εκεινοι", "κακεινον": "και εκεινον", "κακεινα": "και εκεινα",
    "κακεινη": "και εκεινη", "ουδεν": "ουδε εν", "μηδεν": "μηδε εν",
}

def key(word: str) -> str:
    """Lexicon key: lower case, no diacritics, letters only, final sigma folded."""
    word = "".join(c for c in unicodedata.normalize("NFD", word.lower())
                   if unicodedata.category(c) != "Mn")
    return "".join(c for c in word if "α" <= c <= "ω").replace("ς", "σ")


@lru_cache(maxsize=1)
def _lexicon() -> dict:
    lex = {}
    with open(LEXICON_PATH, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            form, lemmas = line.rstrip("\n").split("\t")
            lex[form] = set(lemmas.split("|"))
    return lex


@lru_cache(maxsize=1)
def _indexes():
    """Lemmas by orthographic key, and orthographic keys of the forms of each lemma."""
    by_norm, forms_of = {}, {}
    for form, lems in _lexicon().items():
        nk = normalize_orthography(form)
        by_norm.setdefault(nk, set()).update(lems)
        for lem in lems:
            forms_of.setdefault(lem, set()).add(nk)
    return by_norm, forms_of


def _with_name_variants(found: Set[str]) -> Set[str]:
    out = set(found)
    for group in NAME_VARIANTS:
        if out & group:
            out |= group
    return out


@lru_cache(maxsize=None)
def _lemmas_of_key(k: str) -> Optional[frozenset]:
    lex = _lexicon()
    for cand in (k, k + "ν", k[:-1] if k.endswith("ν") else None):
        if cand and cand in lex:
            return frozenset(_with_name_variants(lex[cand]))
    by_norm, _ = _indexes()
    nk = normalize_orthography(k)
    if nk in by_norm:
        return frozenset(_with_name_variants(by_norm[nk]))
    return None


def lemmas(word: str) -> Optional[Set[str]]:
    """Lemmas of a word form, or None if neither the form nor its orthographic key is attested."""
    found = _lemmas_of_key(key(word))
    return set(found) if found is not None else None


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def _close_to_lemma(word: str, lems: Set[str]) -> bool:
    _, forms_of = _indexes()
    nk = normalize_orthography(key(word))
    return any(_similarity(nk, f) >= FORM_MATCH_CUTOFF
               for lem in lems for f in forms_of.get(lem, ()))


def same_lexeme(x: str, y: str) -> bool:
    if key(x) == key(y):
        return True
    lx, ly = lemmas(x), lemmas(y)
    if lx and ly:
        return bool(lx & ly)
    if lx:
        return _close_to_lemma(y, lx)
    if ly:
        return _close_to_lemma(x, ly)
    return _similarity(normalize_orthography(key(x)), normalize_orthography(key(y))) > FALLBACK_THRESHOLD


def expand_crasis(words: Iterable[str]) -> List[str]:
    out: List[str] = []
    for w in words:
        out.extend(CRASIS.get(key(w), key(w)).split())
    return out


def is_morphological(base_words: Iterable[str], ms_words: Iterable[str]) -> bool:
    """True if a replacement block changes only the form, not the lexeme."""
    b, m = expand_crasis(base_words), expand_crasis(ms_words)
    if len(b) != len(m) or not b:
        return False
    return all(same_lexeme(x, y) for x, y in zip(b, m))
