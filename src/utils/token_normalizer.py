"""Token surface forms and orthographic normalisation for the ITSEE transcriptions.

Two layers are distinguished throughout the pipeline:

``clean_surface``
    The *surface* form of a transcribed token: lower-case, all combining marks
    removed (accents, breathings, diaeresis, iota subscript), the supralinear
    stroke resolved to the ν it abbreviates, and every non-letter character
    (daggers, dots, apostrophes, digits, stray whitespace) dropped. Surface forms
    are what the variant tables record and what the embedding model reads.

``normalize_orthography``
    The *alignment key* of a token: the surface form with orthographic
    alternations folded (itacism, ω/ο, movable ν, movable ς, elision, consonant
    gemination). Alignment runs on these keys, so a pair of tokens that differ
    only orthographically is aligned as equal and never surfaces as a variant.
"""

from __future__ import annotations

import re
import unicodedata

# Supralinear stroke for ν: the spacing macron, the combining macron and the
# combining overline all occur in the transcriptions.
_STROKE_RE = re.compile("[¯̄̅]")
_NON_LETTER_RE = re.compile(r"[^α-ω]")

# Elided forms mapped to their full form (whole-token matches only).
ELISION = {
    "αλλ": "αλλα", "δ": "δε", "τ": "τε", "απ": "απο", "αφ": "απο",
    "επ": "επι", "εφ": "επι", "υπ": "υπο", "υφ": "υπο", "μετ": "μετα",
    "μεθ": "μετα", "κατ": "κατα", "καθ": "κατα", "παρ": "παρα", "δι": "δια",
    "αντ": "αντι", "ανθ": "αντι", "ουδ": "ουδε", "μηδ": "μηδε",
    "τουτ": "τουτο",
}

# Forms with a movable final sigma, folded to the form without it.
MOVABLE_SIGMA = {"ουτωσ", "αχρισ", "μεχρισ"}

# Words whose final ν is not a movable ν and must never be stripped.
NU_EXCEPTIONS = {"εν", "μεν", "ην", "ουδεν", "μηδεν", "ουν", "συν", "ειπον",
                 "εστιν"}


def strip_diacritics(text: str) -> str:
    """Remove accents, breathings, diaeresis and iota subscript."""
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def clean_surface(text: str) -> str:
    """Canonical surface form of a transcribed token (see module docstring)."""
    text = unicodedata.normalize("NFD", text.lower())
    text = _STROKE_RE.sub("ν", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = _NON_LETTER_RE.sub("", text)
    return text


def normalize_orthography(word: str) -> str:
    """Alignment key of a token (see module docstring).

    Accepts either a raw transcribed form or an already cleaned surface form.
    """
    w = clean_surface(word).replace("ς", "σ")
    if w in ELISION:
        w = ELISION[w]
    # Movable ν: only in the endings -σι(ν) and -ε(ν), never in short words or
    # in the listed exceptions.
    if w not in NU_EXCEPTIONS and len(w) >= 4 and re.search(r"(σι|ε)ν$", w):
        w = w[:-1]
    if w in MOVABLE_SIGMA:
        w = w[:-1]
    w = w.replace("ου", "\x00")          # protect the ου digraph
    w = w.replace("ει", "ι").replace("οι", "ι").replace("υ", "ι")
    w = w.replace("η", "ι").replace("αι", "ε").replace("ω", "ο")
    w = w.replace("\x00", "ου")
    w = re.sub(r"([λνσρμτπκ])\1", r"\1", w)   # consonant gemination
    return w
