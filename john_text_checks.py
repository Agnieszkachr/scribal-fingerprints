"""Two checks on the John tables that bear on what the profiles measure.

1. Bezae's lexical excess. A lexical substitution is either a one-for-one
   replacement or a replacement block of unequal length (a phrase recast into a
   longer or shorter one; section 4.1). For each witness, the share of its
   variants in each kind is compared with that of the other witnesses pooled;
   the difference is tested against witness labels permuted within chapters.

2. Sinaiticus in John 1:1-8:38. Fee (1968) found ℵ's text in John 1:1-8:38 to be
   "Western" rather than Alexandrian. For each other witness, the share of its
   variants that are also variants of ℵ (same verse, same anchor reading, same
   witness reading) is compared between 1:1-8:38 and 8:39-21:25 (Fisher's exact
   test), under the anchors B, A and SBL.

    python john_text_checks.py      ->  outputs/john_text_checks.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
N_PERM = 2000
SEED = 42


def lexical_kinds(v):
    lex = v.type == "substitution_lexical"
    unequal = v.n_base_words != v.n_ms_words
    return np.select([lex & unequal, lex & ~unequal], ["lexical_unequal", "lexical_one_for_one"], "other")


def deviation_test(v, witness, kind, rng):
    """Share of `kind` in `witness` minus share in the others; within-chapter permutation p."""
    is_w = (v.manuscript == witness).to_numpy()
    is_k = (v.kind == kind).to_numpy()
    chapters = v.chapter.to_numpy()

    def diff(lab):
        return 100 * (is_k[lab].mean() - is_k[~lab].mean())

    obs = diff(is_w)
    idx = [np.flatnonzero(chapters == c) for c in np.unique(chapters)]
    exceed = 0
    for _ in range(N_PERM):
        lab = is_w.copy()
        for i in idx:
            lab[i] = rng.permutation(lab[i])
        exceed += abs(diff(lab)) >= abs(obs)
    return obs, (exceed + 1) / (N_PERM + 1)


def load(name):
    """Read a John variant table, accepting both column conventions."""
    v = pd.read_csv(DATA / name)
    return v.rename(columns={"baseline_reading": "base_reading", "manuscript_reading": "ms_reading",
                             "variant_type": "type"})


def stretch(v):
    vnum = v.verse.str.extract(r":(\d+)")[0].astype(int)
    return np.where((v.chapter < 8) | ((v.chapter == 8) & (vnum <= 38)), "1:1-8:38", "8:39-21:25")


def shared_with_aleph(v):
    v = v.assign(part=stretch(v), key=v.verse + "|" + v.base_reading.astype(str) + "|" + v.ms_reading.astype(str))
    out = {}
    for w in sorted(set(v.manuscript) - {"aleph"}):
        tab, row = [], {}
        for part in ["1:1-8:38", "8:39-21:25"]:
            g = v[v.part == part]
            kw = g[g.manuscript == w]
            s = int(kw.key.isin(set(g[g.manuscript == "aleph"].key)).sum())
            tab.append([s, len(kw) - s])
            row[part] = {"shared": s, "variants": len(kw), "percent": round(100 * s / len(kw), 1)}
        row["fisher_p"] = float(stats.fisher_exact(tab)[1])
        out[w] = row
    return out


def main():
    rng = np.random.default_rng(SEED)
    v = load("variants_full_john_B.csv")
    v["kind"] = lexical_kinds(v)
    lexical = {}
    for w in ["D", "aleph", "A", "P66"]:
        lexical[w] = {}
        for k in ["lexical_unequal", "lexical_one_for_one"]:
            d, p = deviation_test(v, w, k, rng)
            share = 100 * (v[v.manuscript == w].kind == k).mean()
            lexical[w][k] = {"percent_of_variants": round(share, 1), "deviation_pp": round(d, 1), "perm_p": round(p, 4)}
    fee = {anchor: shared_with_aleph(load(f"variants_full_john_{anchor}.csv")) for anchor in ["B", "A", "SBL"]}
    res = {"lexical_kinds_anchor_B": lexical, "shared_with_aleph_by_stretch": fee}
    (ROOT / "outputs" / "john_text_checks.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
