"""Figures for the article that are not part of the per-configuration set:

* ``outputs/fig3_feature_isolation.png`` -- Cohen's d (point estimate on all
  N, block-bootstrap 95 % CI) for the full corpus and the three
  feature-isolation datasets, with the permutation null mean marked.
* ``outputs/fig5_split_half.png`` -- the six inter-witness profile distances
  computed on odd chapters against the same distances on even chapters
  (attested-loci subset), with the identity line.

    python create_article_figures.py [--baseline B]
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CONDITIONS = [
    ("Full context", "{base}"),
    ("Function words only", "ablation_func_words"),
    ("Content masked", "ablation_masked"),
]
RANDOM_DRAWS = ["ablation_random_masked"] + [f"ablation_random_masked_s{i}" for i in range(1, 5)]


def _metric(path, name):
    df = pd.read_csv(path).set_index("Metric")
    return df.loc[name]


def feature_isolation(base_ms):
    rows = []
    for label, suffix in CONDITIONS:
        res = f"outputs/pilot_results_full_{suffix.format(base=base_ms)}.csv"
        m = _metric(res, "Cohen's d")
        n = int(open(f"outputs/pilot_report_full_{suffix.format(base=base_ms)}.txt",
                     encoding="utf-8").readline().split("N=")[1].split()[0])
        rows.append(dict(label=f"{label}\n(N = {n:,})", d=m["Value"], lo=m["CI_Low"], hi=m["CI_High"],
                         null=m["Null_Mean"], p=m["Perm_P"],
                         ptext="p < 0.001" if m["Perm_P"] < 0.001 else f"p = {m['Perm_P']:.3f}"))
    draws = [_metric(f"outputs/pilot_results_full_{s}.csv", "Cohen's d") for s in RANDOM_DRAWS]
    n = int(open(f"outputs/pilot_report_full_{RANDOM_DRAWS[0]}.txt", encoding="utf-8").readline().split("N=")[1].split()[0])
    sig = sum(dr["Perm_P"] <= 0.05 for dr in draws)
    rows.append(dict(label=f"Random masked (control)\n(N = {n:,}, mean of {len(draws)} draws)",
                     d=sum(dr["Value"] for dr in draws) / len(draws),
                     lo=sum(dr["CI_Low"] for dr in draws) / len(draws),
                     hi=sum(dr["CI_High"] for dr in draws) / len(draws),
                     null=sum(dr["Null_Mean"] for dr in draws) / len(draws), p=None,
                     ptext=f"p <= 0.05 in {sig}/{len(draws)} draws",
                     draws=[dr["Value"] for dr in draws]))
    t = pd.DataFrame(rows)[::-1]
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    y = range(len(t))
    ax.hlines(y, t["lo"], t["hi"], color="#444", lw=1.6)
    ax.plot(t["d"], y, "o", color="#111", ms=6, zorder=3, label="Cohen's d (all N)")
    ax.plot(t["null"], y, "|", color="#999", ms=14, mew=1.6, zorder=2, label="permutation null mean")
    ax.axvline(0, color="#bbb", lw=0.8)
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.text(max(t["hi"]) + 0.003, yi, f"d = {r['d']:.3f}   {r['ptext']}", va="center", fontsize=9)
        if isinstance(r.get("draws"), list):
            ax.plot(r["draws"], [yi] * len(r["draws"]), "o", color="#999", ms=3.5, zorder=2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(t["label"])
    ax.set_xlabel("Cohen's d, inter- vs intra-manuscript cosine distance (95 % block-bootstrap CI)")
    ax.set_xlim(left=min(-0.01, t["lo"].min() - 0.005), right=max(t["hi"]) + 0.03)
    ax.legend(loc="lower right", fontsize=9, frameon=False, bbox_to_anchor=(1.0, 0.12))
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"Feature isolation (baseline {base_ms})", fontsize=11)
    fig.tight_layout()
    fig.savefig("outputs/fig3_feature_isolation.png", dpi=200)
    print("outputs/fig3_feature_isolation.png")


def split_half(base_ms):
    p = pd.read_csv(f"outputs/split_half_pairs_{base_ms}.csv")
    fig, ax = plt.subplots(figsize=(4.8, 4.8))
    lim = (min(p[["odd_distance", "even_distance"]].min()) - 0.05,
           max(p[["odd_distance", "even_distance"]].max()) + 0.05)
    ax.plot(lim, lim, color="#bbb", lw=0.8, zorder=1)
    ax.scatter(p["odd_distance"], p["even_distance"], color="#111", s=36, zorder=3)
    for _, r in p.iterrows():
        ax.annotate(r["pair"].replace("aleph", "Sin"), (r["odd_distance"], r["even_distance"]),
                    xytext=(5, 4), textcoords="offset points", fontsize=9)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("profile distance, odd chapters (cosine)")
    ax.set_ylabel("profile distance, even chapters (cosine)")
    ax.set_title(f"Split-half profile distances, attested loci (baseline {base_ms})", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig("outputs/fig5_split_half.png", dpi=200)
    print("outputs/fig5_split_half.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="B")
    a = ap.parse_args()
    feature_isolation(a.baseline)
    split_half(a.baseline)
