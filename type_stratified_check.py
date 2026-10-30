"""Cohen's d against a null that keeps each witness's mixture of variant types.

The corpus-wide d compares inter- and intra-witness cosine distances between
change vectors. If the witnesses were separated only because they differ in
the mixture of variant types they contain, a null that preserves that mixture
would reproduce the observed d. Here the witness labels are shuffled within
each cell of chapter x variant type (2,000 permutations), so that every
chapter keeps, for each witness, its number of variants of each type; the
observed d is compared with that null. Anchors B, A and aleph, and the
content-masked dataset of the feature-isolation study (anchor B).

Needs the vector files written by profile_scribes.py
(outputs/variants_full_with_vectors_<configuration>.pkl).

    python type_stratified_check.py   ->  outputs/type_stratified_permutation.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src import stats_core as sc

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
CONFIGS = ["B", "A", "aleph", "ablation_masked"]


def main():
    configs = sys.argv[1:] or CONFIGS
    out = {}
    for anchor in configs:
        df = pd.read_pickle(OUT / f"variants_full_with_vectors_{anchor}.pkl")
        tcol = sc.type_column(df)
        # block_permutation_cohens_d shuffles labels within the values of the
        # "chapter" column; giving it chapter x type as the block keeps the
        # type mixture of every witness in every chapter
        strat = df.copy()
        strat["chapter"] = df["chapter"].astype(str) + "|" + df[tcol].astype(str)
        d, p, perm = sc.block_permutation_cohens_d(strat)
        d_ch, p_ch, perm_ch = sc.block_permutation_cohens_d(df)
        out[anchor] = {
            "n": int(min(len(df), sc.D_MAX_N)),
            "d": round(float(d), 4),
            "chapter_null_mean": round(float(np.mean(perm_ch)), 4),
            "chapter_null_sd": round(float(np.std(perm_ch)), 4),
            "chapter_p": round(float(p_ch), 6),
            "type_stratified_null_mean": round(float(np.mean(perm)), 4),
            "type_stratified_null_sd": round(float(np.std(perm)), 4),
            "type_stratified_p": round(float(p), 6),
            "n_perm": len(perm),
        }
        print(anchor, out[anchor], flush=True)
    with open(OUT / "type_stratified_permutation.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
