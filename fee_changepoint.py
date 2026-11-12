"""Locating the change in Sinaiticus in John without being given Fee's boundary.

Fee (1968) placed the change in the text of Sinaiticus at John 8:38. Here the
boundary is not supplied. The verses that both Sinaiticus and Vaticanus preserve
are taken in canonical order, and the number of Sinaiticus's variants against B
in each verse is modelled as a Poisson count whose rate per word of B changes
once. Every split that leaves at least 20 verses on each side is scored by the
log-likelihood ratio against a single constant rate. The best split is reported
together with every split whose score lies within 2 log-likelihood units of the
maximum, an approximate 95 % interval for the position of the change. Whether a
change of this size could arise from differences between chapters alone is tested
by shuffling the order of the chapters, keeping the verses of each chapter
together (2,000 permutations), and recording the largest score each time; the
p-value includes the +1 correction.

    python fee_changepoint.py   ->  outputs/fee_changepoint.json
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src import extract_variants as ev

ROOT = Path(__file__).resolve().parent
N_PERM = 2000
SEED = 42
MIN_SIDE = 20
WITNESS = "aleph"


def verse_key(label):
    m = re.search(r"(\d+):(\d+)", label)
    return int(m.group(1)), int(m.group(2))


def best_split(k, e, min_side=MIN_SIDE):
    """Log-likelihood ratio of a one-change Poisson model at every admissible split."""
    ck, ce = np.cumsum(k), np.cumsum(e)
    K, E = ck[-1], ce[-1]

    def ll(kk, ee):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(kk > 0, kk * np.log(kk / ee), 0.0)

    i = np.arange(min_side - 1, len(k) - min_side)   # split after position i
    score = ll(ck[i], ce[i]) + ll(K - ck[i], E - ce[i]) - ll(np.array(K), np.array(E))
    return i, score


def main():
    texts = ev.load_corpus("john", ROOT / "data" / "raw" / "john")
    words = {verse_key(lab): sum(1 for t in toks if t.surface != ev.GAP) for lab, toks in texts["B"].items()}
    shared = sorted(set(words) & {verse_key(lab) for lab in texts[WITNESS]})
    shared = [v for v in shared if words[v] > 0]

    var = pd.read_csv(ROOT / "data" / "variants_full_john_B.csv")
    counts = var[var.manuscript == WITNESS].verse.map(verse_key).value_counts()
    k = np.array([counts.get(v, 0) for v in shared], float)
    e = np.array([words[v] for v in shared], float)

    idx, score = best_split(k, e)
    j = int(np.argmax(score))
    s_max, cut = float(score[j]), int(idx[j])
    within = [shared[int(i)] for i, s in zip(idx, score) if s >= s_max - 2]

    rng = np.random.default_rng(SEED)
    chapters = np.array([v[0] for v in shared])
    blocks = [np.flatnonzero(chapters == c) for c in np.unique(chapters)]
    null = []
    for _ in range(N_PERM):
        order = np.concatenate([blocks[b] for b in rng.permutation(len(blocks))])
        null.append(float(best_split(k[order], e[order])[1].max()))
    p = (1 + sum(n >= s_max for n in null)) / (N_PERM + 1)

    fmt = lambda v: f"{v[0]}:{v[1]}"
    res = {
        "witness": WITNESS, "baseline": "B",
        "verses": len(shared), "variants": int(k.sum()), "words_of_B": int(e.sum()),
        "best_split_after": fmt(shared[cut]),
        "interval_2_loglik": [fmt(within[0]), fmt(within[-1])],
        "rate_per_100_words_before": round(100 * k[:cut + 1].sum() / e[:cut + 1].sum(), 2),
        "rate_per_100_words_after": round(100 * k[cut + 1:].sum() / e[cut + 1:].sum(), 2),
        "loglik_ratio": round(s_max, 2),
        "chapter_shuffle_null_mean": round(float(np.mean(null)), 2),
        "perm_p": round(p, 6), "n_perm": N_PERM, "min_verses_per_side": MIN_SIDE,
    }
    (ROOT / "outputs" / "fee_changepoint.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
