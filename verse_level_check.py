"""Cohen's d on verse aggregates, with its own block-permutation null.

The change vectors of one witness in one verse are averaged into a single
vector (one witness-verse unit), as in ``stats_core.cohens_d_verse_level``.
The null distribution is then obtained by shuffling the witness labels of
whole witness-verse units within each chapter (2,000 permutations), so that
variants which share a verse, and hence overlapping context windows, are
moved together. Anchors B, A and aleph.

Needs the vector files written by profile_scribes.py
(outputs/variants_full_with_vectors_<anchor>.pkl).

    python verse_level_check.py   ->  outputs/verse_level_permutation.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src import stats_core as sc

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
ANCHORS = ["B", "A", "aleph"]


def verse_units(df):
    """One mean change vector per witness and verse, keeping the chapter for the blocks."""
    return (df.groupby(["manuscript", "verse", "chapter"])["change_vector"]
              .apply(lambda s: np.mean(np.array(s.tolist()), axis=0))
              .reset_index())


def main():
    out = {}
    for anchor in ANCHORS:
        df = pd.read_pickle(OUT / f"variants_full_with_vectors_{anchor}.pkl")
        units = verse_units(df)
        d, p, perm = sc.block_permutation_cohens_d(units)
        out[anchor] = {
            "n_variants": int(len(df)),
            "n_units": int(len(units)),
            "d": round(float(d), 4),
            "null_mean": round(float(np.mean(perm)), 4),
            "null_sd": round(float(np.std(perm)), 4),
            "p": round(float(p), 4),
            "n_perm": len(perm),
        }
        print(anchor, out[anchor])
    with open(OUT / "verse_level_permutation.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
