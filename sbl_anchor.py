"""Robustness check: John with the SBL edition (MorphGNT SBLGNT, Tauber 2017) as anchor.

The SBL text of John (data/morphgnt/64-Jn-morphgnt.txt, CC BY-SA 3.0) is read verse by
verse, reduced to the same surface forms as the transcriptions, and used in place of
Vaticanus as the anchor; every witness, Vaticanus included, is aligned and annotated
against it with the rules of src/extract_variants.py. Reported: the witness-type
association (as in run_statistical_tests.py) and, for each witness, the deviation of
its type shares from those of all other witnesses with a within-chapter permutation null.

Usage:
    python sbl_anchor.py
Writes data/variants_full_john_SBL.csv and outputs/sbl_anchor_john.json.
"""
import json
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

from src import stats_core as sc
from src.extract_variants import Token, load_corpus, extract_rows
from src.utils.token_normalizer import clean_surface

TYPES = list(sc.VARIANT_TYPES)


def sbl_text(path="data/morphgnt/64-Jn-morphgnt.txt"):
    verses = defaultdict(list)
    for line in open(path, encoding="utf-8"):
        bcv, _pos, _parse, _text, word, _norm, _lemma = line.split()
        surface = clean_surface(word)
        if surface:
            verses[f"J {int(bcv[2:4])}:{int(bcv[4:6])}"].append(Token(surface))
    return dict(verses)


def deviation_test(df, witness, n_perm=1000):
    type_idx = df["variant_type"].map({t: i for i, t in enumerate(TYPES)}).to_numpy()

    def stats_for(is_w):
        table = np.zeros((2, len(TYPES)))
        np.add.at(table, (is_w.astype(int), type_idx), 1)
        shares = table / np.clip(table.sum(axis=1, keepdims=True), 1, None)
        t = table[:, table.sum(axis=0) > 0]
        v = float(np.sqrt(stats.chi2_contingency(t)[0] / t.sum()))
        return v, shares[1] - shares[0], shares[1]

    is_w = (df["manuscript"] == witness).to_numpy()
    v, dev, prof = stats_for(is_w)
    r = sc.rng()
    null = [stats_for(sc.shuffle_labels_within_chapters(df, r) == witness) for _ in range(n_perm)]
    null_v = [x[0] for x in null]
    null_dev = np.array([x[1] for x in null])
    return dict(n=int(is_w.sum()), v=v, p=sc.perm_p(null_v, v),
                shares={t: float(prof[i]) for i, t in enumerate(TYPES)},
                deviation={t: float(dev[i]) for i, t in enumerate(TYPES)},
                deviation_p={t: sc.perm_p(np.abs(null_dev[:, i]), abs(dev[i])) for i, t in enumerate(TYPES)})


def main():
    texts = load_corpus("john")
    texts["SBL"] = sbl_text()
    rows, _ = extract_rows("john", texts, "SBL")
    df = pd.DataFrame(rows)
    df.to_csv("data/variants_full_john_SBL.csv", index=False)
    lines, metrics, _ = sc.typology_tests(df)
    out = {"n": len(df), "per_witness": df["manuscript"].value_counts().to_dict(),
           "association": {m[0]: dict(v=m[1], ci_low=m[2], ci_high=m[3], null_mean=m[4], perm_p=m[6]) for m in metrics},
           "witnesses": {w: deviation_test(df, w) for w in sorted(df["manuscript"].unique())}}
    json.dump(out, open("outputs/sbl_anchor_john.json", "w", encoding="utf-8"), indent=1)
    print("\n".join(lines))
    for w, r in out["witnesses"].items():
        print(w, r["n"], round(r["v"], 3), {t: round(100 * x, 1) for t, x in r["deviation"].items()})


if __name__ == "__main__":
    main()
