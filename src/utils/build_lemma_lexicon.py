"""Rebuild ``data/morphgnt_form_lemmas.tsv`` from a local clone of MorphGNT SBLGNT.

    git clone https://github.com/morphgnt/sblgnt.git
    python -m src.utils.build_lemma_lexicon path/to/sblgnt
"""
import glob
import sys
from collections import defaultdict
from pathlib import Path

from src.utils.lemma_lexicon import LEXICON_PATH, key

HEADER = """# Word form -> lemma(s), accents and breathings removed, final sigma folded.
# Derived from MorphGNT SBLGNT (https://github.com/morphgnt/sblgnt), whose
# morphological parsing and lemmatisation is licensed CC BY-SA 3.0;
# this derived list is distributed under the same licence.
# Rebuild with: python -m src.utils.build_lemma_lexicon
"""


def main(src_dir: str) -> None:
    lex = defaultdict(set)
    for f in sorted(glob.glob(str(Path(src_dir) / "*-morphgnt.txt"))):
        for line in open(f, encoding="utf-8"):
            cols = line.split()
            lex[key(cols[4])].add(key(cols[6]))
    with open(LEXICON_PATH, "w", encoding="utf-8") as out:
        out.write(HEADER)
        for form in sorted(lex):
            out.write(form + "\t" + "|".join(sorted(lex[form])) + "\n")
    print(f"{len(lex)} forms -> {LEXICON_PATH}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sblgnt")
