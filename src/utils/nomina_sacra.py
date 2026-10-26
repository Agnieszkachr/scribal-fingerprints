"""Expansion table for nomina sacra in the ITSEE transcriptions.

The transcriptions encode a nomen sacrum as

    <w><abbr type="nomSac"><hi rend="overline">theta-nu</hi></abbr></w>

i.e. as markup, not as a combining overline character. Left unexpanded, a
witness that abbreviates and a baseline that writes the word out would be
recorded as differing, and nearly all such pairs would be annotated as
morphological substitutions. The parser therefore expands every nomen sacrum
before alignment (article, § 3.3).

The table below is built from the 124 distinct forms actually attested in
data/raw/, not from a general list of nomina sacra. Forms are keyed in the
normalised shape the parser sees: lowercase, accents and breathings stripped,
trailing apostrophe removed.

Expansion is by case, which the abbreviation itself encodes (theta-sigma =
nominative, theta-upsilon = genitive, and so on), so a static table is correct
and needs no context.

DELIBERATELY NOT EXPANDED: Greek numerals. An overline also marks a numeral
(omicron-beta = 72, koppa-theta = 99), and those forms carry type="nomSac" in
these files too. Expanding them would be wrong. They fall through unmapped,
which is the intended behaviour -- see UNMAPPED_EXPECTED.

    python -m src.utils.nomina_sacra --report   # coverage against data/raw/
"""

from __future__ import annotations

import re
import unicodedata

_APOSTROPHES = "’'ʼ᾽`´"
_APOS_RE = re.compile(f"[{_APOSTROPHES}]")


def _key(form: str) -> str:
    """Normalise a form to its table key: lowercase, unaccented, no apostrophe."""
    form = _APOS_RE.sub("", form)
    form = unicodedata.normalize("NFD", form.lower())
    return "".join(c for c in form if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# The table. Grouped by lexeme; each entry maps abbreviation -> expansion,
# both unaccented lowercase, matching the transcriptions' own orthography.
# ---------------------------------------------------------------------------

_TABLE_SOURCE: dict[str, dict[str, str]] = {
    "θεος": {
        "θς": "θεος", "θυ": "θεου", "θω": "θεω", "θν": "θεον", "θε": "θεε",
    },
    "κυριος": {
        "κς": "κυριος", "κυ": "κυριου", "κω": "κυριω", "κν": "κυριον",
        "κε": "κυριε",
    },
    "ιησους": {
        "ις": "ιησους", "ιυ": "ιησου", "ιω": "ιησω", "ιν": "ιησουν",
        "ιη": "ιησου", "ιης": "ιησους", "ιην": "ιησουν", "ιηυ": "ιησου",
        "ιηυς": "ιησους", "ιιης": "ιησους",
    },
    "χριστος": {
        "χς": "χριστος", "χυ": "χριστου", "χω": "χριστω", "χν": "χριστον",
        "χε": "χριστε", "χρς": "χριστος", "χρυ": "χριστου",
        "χρν": "χριστον", "χρε": "χριστε",
    },
    "πνευμα": {
        "πνα": "πνευμα", "πνς": "πνευματος", "πνι": "πνευματι",
        "πνατα": "πνευματα", "πνατων": "πνευματων", "πνασι": "πνευμασι",
        "πνασιν": "πνευμασιν", "πνων": "πνευματων", "πνος": "πνευματος",
        "πνη": "πνευματι", "πν": "πνευμα", "πνευν": "πνευμα",
        "πνευνα": "πνευμα",
    },
    "ανθρωπος": {
        "ανος": "ανθρωπος", "ανου": "ανθρωπου", "ανω": "ανθρωπω",
        "ανον": "ανθρωπον", "ανε": "ανθρωπε", "ανοι": "ανθρωποι",
        "ανων": "ανθρωπων", "ανοις": "ανθρωποις", "ανους": "ανθρωπους",
        "ανο": "ανθρωπο", "αννω": "ανθρωπω",
    },
    "πατηρ": {
        "πηρ": "πατηρ", "πρς": "πατρος", "πρι": "πατρι", "πρα": "πατερα",
        "περ": "πατερ", "πρες": "πατερες", "πρων": "πατερων",
        "πρας": "πατερας", "πρ": "πατηρ", "πρασιν": "πατρασιν",
    },
    "μητηρ": {
        "μηρ": "μητηρ", "μρς": "μητρος", "μρι": "μητρι", "μρα": "μητερα",
    },
    "υιος": {
        "υς": "υιος", "υυ": "υιου", "υω": "υιω", "υν": "υιον", "υε": "υιε",
        "υ": "υιου", "υυω": "υιω",
    },
    "ουρανος": {
        "ουνος": "ουρανος", "ουνου": "ουρανου", "ουνω": "ουρανω",
        "ουνον": "ουρανον", "ουνων": "ουρανων", "ουνοις": "ουρανοις",
        "ουνους": "ουρανους", "ουνοι": "ουρανοι",
    },
    "ισραηλ": {"ιηλ": "ισραηλ", "ισλ": "ισραηλ", "ισηλ": "ισραηλ"},
    "ιερουσαλημ": {"ιλημ": "ιερουσαλημ", "ιηλμ": "ιερουσαλημ"},
    "δαυιδ": {"δαδ": "δαυιδ"},
    "σταυρος": {
        "στρος": "σταυρος", "στρου": "σταυρου", "στρω": "σταυρω",
        "στρον": "σταυρον", "στρν": "σταυρον", "στρυ": "σταυρου",
        "στραν": "σταυρωσαν", "στη": "σταυρη", "στν": "σταυρον",
        "στρωθηναι": "σταυρωθηναι", "στρωσαν": "σταυρωσαν",
        "εστρωσαν": "εσταυρωσαν", "στρατε": "σταυρωσατε",
        "εστραν": "εσταυρωσαν", "στρθη": "σταυρωθη",
    },
    "σωτηρ": {
        "σηρ": "σωτηρ", "σωρ": "σωτηρ", "σρς": "σωτηρος", "σρι": "σωτηρι",
        "σρου": "σωτηρου", "σρν": "σωτηρα", "σρναι": "σωτηραι",
        "σης": "σωτηρος",
    },
    "παντα": {"πντα": "παντα", "πντων": "παντων"},
}

NOMINA_SACRA: dict[str, str] = {}
for _lexeme, _entries in _TABLE_SOURCE.items():
    for _abbr, _full in _entries.items():
        NOMINA_SACRA[_key(_abbr)] = _full

# Forms attested with type="nomSac" that are deliberately left alone.
# Greek numerals (an overline marks these too) and one run-together
# transcription artefact. Listed so --report can tell a known pass-through
# from a form the table has simply missed.
UNMAPPED_EXPECTED = {
    _key(f) for f in (
        "οβ", "ϙθ", "β", "βι",              # numerals under an overline
        "και", "προς", "παρ",               # already expanded in the source
        "σταυρωσον", "σταυρος",             # already expanded in the source
        "υμινοιανοιποιειτε",                # run-together transcription
    )
}


def expand(form: str) -> str:
    """Expand a nomen sacrum to its full form.

    Returns the input unchanged when the form is not in the table, so numerals
    and already-expanded forms pass through untouched.
    """
    if not form:
        return form
    return NOMINA_SACRA.get(_key(form), form)


def is_known(form: str) -> bool:
    return _key(form) in NOMINA_SACRA


def _report() -> None:
    import glob
    import io
    from collections import Counter

    w_re = re.compile(r"<w\b[^>]*>((?:(?!</w>).)*?)</w>", re.S)
    tag_re = re.compile(r"<[^>]+>")
    forms: Counter = Counter()
    for corpus in ("mark", "matthew", "luke_acts", "john"):
        for path in glob.glob(f"data/raw/{corpus}/*.xml"):
            source = io.open(path, encoding="utf-8").read()
            for m in w_re.finditer(source):
                inner = m.group(1)
                if 'type="nomSac"' not in inner:
                    continue
                text = re.sub(r"\s+", "", tag_re.sub("", inner))
                if text:
                    forms[_key(text)] += 1

    mapped = sum(n for f, n in forms.items() if f in NOMINA_SACRA)
    total = sum(forms.values())
    unexpected = {f: n for f, n in forms.items()
                  if f not in NOMINA_SACRA and f not in UNMAPPED_EXPECTED}
    print(f"attested nomSac tokens : {total}")
    print(f"expanded by this table : {mapped} ({100 * mapped / total:.2f}%)")
    print(f"known pass-throughs    : "
          f"{sum(n for f, n in forms.items() if f in UNMAPPED_EXPECTED)}")
    print(f"unmapped, unexpected   : {sum(unexpected.values())} "
          f"in {len(unexpected)} form(s)")
    for form, n in sorted(unexpected.items(), key=lambda kv: -kv[1]):
        print(f"    {n:5d}  {form}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Nomina sacra expansion table.")
    ap.add_argument("--report", action="store_true",
                    help="coverage of the table against data/raw/")
    if ap.parse_args().report:
        _report()
