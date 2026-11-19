"""The two instruments measured by the same statistics.

The typology is reported as an association (Cramér's V between witness and
variant type) and the embeddings as a separation (Cohen's d, and the ARI of a
k-means partition of the change vectors against the witness labels). Here each
partition measure is applied to the other instrument:

  * the ARI of the partition into the five variant types against the witness
    labels (the typology measured as the embeddings are);
  * Cramér's V between the k-means partition of the change vectors and the
    witness (the embeddings measured as the typology is).

For every anchor (B, A, aleph) the four values are computed twice: on all
variants, and on the sample of vectors that stats_core uses for the ARI of
the reports. The k-means partition has as many clusters as there are witnesses
(ten initialisations), as for that ARI. Each value is tested against the null
used for V and the ARI elsewhere: witness labels shuffled within chapters
(stats_core.N_PERM permutations).

Needs the vector files written by profile_scribes.py
(outputs/variants_full_with_vectors_<anchor>.pkl); the variant types are read
from the variant tables in data/, as in type_stratified_check.py.

    python like_for_like_check.py   ->  outputs/like_for_like_check.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

from src import stats_core as sc
from type_stratified_check import with_table_types

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
ANCHORS = ["B", "A", "aleph"]


def cramers_v(a, b):
    return sc.calc_cramers_v(pd.crosstab(pd.Series(np.asarray(a)), pd.Series(np.asarray(b))))


def partition_measures(df):
    """ARI and Cramér's V of the type partition and of the k-means partition
    against the witness labels, each with its within-chapter permutation null."""
    labels = df["manuscript"].to_numpy()
    types = df[sc.type_column(df)].to_numpy()
    clusters = KMeans(n_clusters=len(np.unique(labels)), random_state=sc.SEED,
                      n_init=10).fit_predict(sc.vectors(df))
    observed = {
        "ari_types": adjusted_rand_score(labels, types),
        "ari_kmeans": adjusted_rand_score(labels, clusters),
        "v_types": cramers_v(labels, types),
        "v_kmeans": cramers_v(labels, clusters),
    }
    r = sc.rng()
    null = {k: [] for k in observed}
    for _ in range(sc.N_PERM):
        shuffled = sc.shuffle_labels_within_chapters(df, r)
        null["ari_types"].append(adjusted_rand_score(shuffled, types))
        null["ari_kmeans"].append(adjusted_rand_score(shuffled, clusters))
        null["v_types"].append(cramers_v(shuffled, types))
        null["v_kmeans"].append(cramers_v(shuffled, clusters))
    res = {"n": int(len(df)), "n_perm": sc.N_PERM}
    for k, v in observed.items():
        res[k] = {"value": round(float(v), 6),
                  "null_mean": round(float(np.mean(null[k])), 4),
                  "null_sd": round(float(np.std(null[k])), 4),
                  "p": round(sc.perm_p(null[k], v), 6)}
    return res


def main():
    anchors = sys.argv[1:] or ANCHORS
    out = {}
    for anchor in anchors:
        df = with_table_types(pd.read_pickle(OUT / f"variants_full_with_vectors_{anchor}.pkl"), anchor)
        sample = df.sample(n=sc.ARI_MAX_N, random_state=sc.SEED) if len(df) > sc.ARI_MAX_N else df
        out[anchor] = {"all_variants": partition_measures(df), "ari_sample": partition_measures(sample)}
        for scope, res in out[anchor].items():
            print(anchor, scope, res, flush=True)
    with open(OUT / "like_for_like_check.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
