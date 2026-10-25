"""Supplementary checks on the John results.

1. Cohen's d within each variant class, under the anchors B, A and ℵ, with a
   chapter-level block-bootstrap interval and a within-chapter permutation p
   (the point estimate and the permutation use the same sample of up to 1,000
   vectors per class as ``stats_core.cohens_d_by_type``).
2. Content masking against random masking. Both conditions keep the same
   4,365 variants (rows aligned), so their difference can be bootstrapped in
   pairs: every replicate resamples chapters, draws one sample of rows, and
   computes d under content masking and under each of the five random draws on
   those rows. Reported: the difference (content masked minus mean of the
   random draws), its 95 % interval, and the share of replicates <= 0.
3. Split halves of the typology. Odd and even chapters: Cramér's V in each
   half; each witness's five-type profile (shares) in each half; the distance
   between profiles is the total-variation distance (half the sum of absolute
   differences of the shares, i.e. the share of variants that would have to
   change type); same-witness against cross-witness distance and the
   nearest-self count, each tested by permuting witness labels within
   chapters. Full attested text and the 532 verses attested in all five
   witnesses; anchors B, A and ℵ.
4. Sinaiticus and Bezae chapter by chapter: for each chapter, the share of
   Bezae's variants that are also variants of Sinaiticus (same verse, same
   anchor reading, same witness reading), anchor B; plus a figure.
    python supplementary_checks.py   ->  outputs/supplementary_checks.json,
                                         outputs/fig8_aleph_D_by_chapter.png
"""
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from src import stats_core as sc
from john_text_checks import load

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
ANCHORS = {"B": "B", "A": "A", "aleph": "aleph"}
N_BOOT = sc.N_BOOT
N_PERM_D = sc.N_PERM_D
N_PERM_SPLIT = sc.N_PERM_SPLIT
RANDOM_DRAWS = ["random_masked", "random_masked_s1", "random_masked_s2", "random_masked_s3", "random_masked_s4"]


def fast_inter_intra_d(vecs, labels, ids=None):
    """Same quantity as stats_core.inter_intra_d (cosine distances; pairs of two
    copies of one observation excluded), computed from matrix sums."""
    x = np.asarray(vecs, dtype=float)
    norms = np.linalg.norm(x, axis=1)
    ok = norms > 0
    xn = np.where(ok[:, None], x / np.where(ok, norms, 1)[:, None], 0.0)
    dist = 1.0 - xn @ xn.T
    ids = np.arange(len(x)) if ids is None else np.asarray(ids)
    valid = (ids[:, None] != ids[None, :]) & ok[:, None] & ok[None, :]
    labels = np.asarray(labels)
    same = labels[:, None] == labels[None, :]
    def stats_for(mask):
        n = mask.sum() / 2
        dm = dist[mask]
        return n, dm.sum() / 2, (dm ** 2).sum() / 2
    n1, s1, q1 = stats_for(valid & ~same)
    n2, s2, q2 = stats_for(valid & same)
    if n1 < 2 or n2 < 2:
        return 0.0
    m1, m2 = s1 / n1, s2 / n2
    v1 = (q1 - n1 * m1 ** 2) / (n1 - 1)
    v2 = (q2 - n2 * m2 ** 2) / (n2 - 1)
    pooled = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
    return 0.0 if pooled <= 0 else float((m1 - m2) / np.sqrt(pooled))


def fast_block_bootstrap_d(df, n_boot=sc.N_BOOT, max_n=sc.D_BOOT_MAX_N):
    """stats_core.block_bootstrap_cohens_d with the same random stream, fast distances."""
    r = sc.rng()
    chapters = df["chapter"].unique()
    vecs, labels, chap = sc.vectors(df), df["manuscript"].to_numpy(), df["chapter"].to_numpy()
    by_ch = {c: np.flatnonzero(chap == c) for c in chapters}
    vals = []
    for _ in range(n_boot):
        sampled = r.choice(chapters, size=len(chapters), replace=True)
        rows = np.concatenate([by_ch[c] for c in sampled])
        pick = r.choice(len(rows), size=min(len(rows), max_n), replace=False)
        rows = rows[pick]
        vals.append(fast_inter_intra_d(vecs[rows], labels[rows], ids=rows))
    return float(np.mean(vals)), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), vals


def pkl(suffix):
    return pd.read_pickle(OUT / f"variants_full_with_vectors_{suffix}.pkl")


def common_verses():
    with open(ROOT / "data" / "common_extant_verses.txt", encoding="utf-8") as fh:
        return set(line.strip() for line in fh if line.strip())


# 1 ─ within-class d ────────────────────────────────────────────────

def within_class(df):
    tcol = sc.type_column(df)
    out = {}
    for vtype in sc.VARIANT_TYPES:
        cls = df[df[tcol] == vtype]
        if len(cls) < 100 or cls["manuscript"].nunique() < 2:
            continue
        sub = cls.sample(n=min(len(cls), sc.CLASS_MAX_N), random_state=sc.SEED)
        d, p, perm = sc.block_permutation_cohens_d(sub, n_perm=N_PERM_D, max_n=len(sub))
        _, low, high, _ = fast_block_bootstrap_d(cls, n_boot=N_BOOT, max_n=sc.CLASS_MAX_N)
        out[vtype] = dict(n=len(sub), d=round(d, 4), ci_low=round(low, 4), ci_high=round(high, 4),
                          null_mean=round(float(np.mean(perm)), 4), perm_p=round(p, 4))
    return out


# 2 ─ content masked minus random masked ─────────────────────────────

def masked_vs_random():
    masked = pkl("ablation_masked")
    draws = [pkl(f"ablation_{s}") for s in RANDOM_DRAWS]
    vm = sc.vectors(masked)
    vr = [sc.vectors(d) for d in draws]
    labels = masked["manuscript"].to_numpy()
    chapters = masked["chapter"].to_numpy()

    def d_on(rows, ids):
        dm = fast_inter_intra_d(vm[rows], labels[rows], ids)
        dr = [fast_inter_intra_d(v[rows], labels[rows], ids) for v in vr]
        return dm, float(np.mean(dr))

    # point estimate on the same 4,365 rows as Table 5
    full_rows = np.arange(len(masked))
    pm, pr = d_on(full_rows, None)
    r = sc.rng()
    uniq = np.unique(chapters)
    by_ch = {c: np.flatnonzero(chapters == c) for c in uniq}
    diffs, dms, drs = [], [], []
    for _ in range(N_BOOT):
        sampled = r.choice(uniq, size=len(uniq), replace=True)
        rows = np.concatenate([by_ch[c] for c in sampled])
        pick = r.choice(len(rows), size=min(len(rows), sc.D_BOOT_MAX_N), replace=False)
        rows = rows[pick]
        dm, dr = d_on(rows, rows)
        dms.append(dm); drs.append(dr); diffs.append(dm - dr)
    diffs = np.array(diffs)
    return dict(content_masked_d=round(pm, 4), random_masked_mean_d=round(pr, 4), difference=round(pm - pr, 4),
                boot_ci_low=round(float(np.percentile(diffs, 2.5)), 4),
                boot_ci_high=round(float(np.percentile(diffs, 97.5)), 4),
                boot_share_le_0=round(float(np.mean(diffs <= 0)), 4), n_boot=N_BOOT,
                sample_per_replicate=sc.D_BOOT_MAX_N)


# 3 ─ split halves of the typology ──────────────────────────────────

def fast_cramers(df, broad, n_boot=N_BOOT, n_perm=sc.N_PERM):
    """Cramér's V (broad classes or substitution sub-classes) with the chapter
    block bootstrap and the within-chapter permutation of stats_core, on count arrays."""
    t = df[sc.type_column(df)].to_numpy()
    mss = sorted(df["manuscript"].unique())
    lab = df["manuscript"].to_numpy()
    chap = df["chapter"].to_numpy()
    cols = ([[*sc.SUB], ["addition"], ["omission"]] if broad else [[x] for x in sc.SUB])
    col_of = {}
    for j, group in enumerate(cols):
        for x in group:
            col_of[x] = j
    tcode = np.array([col_of.get(x, -1) for x in t])

    def table(labels, rows):
        m = np.zeros((len(mss), len(cols)))
        sel = rows[tcode[rows] >= 0]
        li = np.searchsorted(mss, labels[sel])
        np.add.at(m, (li, tcode[sel]), 1)
        return m

    def v_of(m):
        m = m[m.sum(axis=1) > 0][:, m.sum(axis=0) > 0]
        if min(m.shape) < 2:
            return 0.0
        return float(np.sqrt(sc.stats.chi2_contingency(m)[0] / (m.sum() * (min(m.shape) - 1))))

    allrows = np.arange(len(df))
    v = v_of(table(lab, allrows))
    chapters = df["chapter"].unique()
    by_ch = {c: np.flatnonzero(chap == c) for c in chapters}
    r = sc.rng()
    boot = [v_of(table(lab, np.concatenate([by_ch[c] for c in r.choice(chapters, size=len(chapters), replace=True)])))
            for _ in range(n_boot)]
    r = sc.rng()
    perm = [v_of(table(sc.shuffle_labels_within_chapters(df, r), allrows)) for _ in range(n_perm)]
    return dict(v=v, low=float(np.percentile(boot, 2.5)), high=float(np.percentile(boot, 97.5)),
                p=sc.perm_p(perm, v))


def type_profiles(df, labels, odd_mask, mss):
    t = df[sc.type_column(df)].to_numpy()
    out = []
    for half in (odd_mask, ~odd_mask):
        rows = []
        for m in mss:
            sel = (labels == m) & half
            n = sel.sum()
            rows.append([np.mean(t[sel] == vt) if n else np.nan for vt in sc.VARIANT_TYPES])
        out.append(np.array(rows))
    return out


def tv(a, b):
    return 0.5 * np.abs(a[:, None, :] - b[None, :, :]).sum(axis=2)


def typology_split_half(df, n_perm=N_PERM_SPLIT):
    df = df.reset_index(drop=True)
    mss = sorted(df["manuscript"].unique())
    labels = df["manuscript"].to_numpy()
    odd_mask = (df["chapter"].to_numpy() % 2) != 0
    off = ~np.eye(len(mss), dtype=bool)

    def geometry(lbl):
        o, e = type_profiles(df, lbl, odd_mask, mss)
        c = tv(o, e)
        return c, c[off].mean() - np.diag(c).mean(), int(np.sum(np.argmin(c, axis=1) == np.arange(len(mss))))

    cross, gap, nearest = geometry(labels)
    r = sc.rng()
    null = [geometry(sc.shuffle_labels_within_chapters(df, r))[1:] for _ in range(n_perm)]
    ng, nn = np.array([g for g, _ in null]), np.array([k for _, k in null])
    o, e = type_profiles(df, labels, odd_mask, mss)
    halves = {}
    for name, part in (("odd", df[odd_mask]), ("even", df[~odd_mask])):
        vb = fast_cramers(part, True)
        vs = fast_cramers(part, False)
        halves[name] = dict(n=int(len(part)),
                            v_broad=round(vb["v"], 3), v_broad_ci=[round(vb["low"], 3), round(vb["high"], 3)],
                            v_broad_p=round(vb["p"], 4),
                            v_sub=round(vs["v"], 3), v_sub_ci=[round(vs["low"], 3), round(vs["high"], 3)],
                            v_sub_p=round(vs["p"], 4))
    profiles = {m: {"odd": dict(zip(sc.VARIANT_TYPES, np.round(100 * o[i], 1).tolist())),
                    "even": dict(zip(sc.VARIANT_TYPES, np.round(100 * e[i], 1).tolist()))}
                for i, m in enumerate(mss)}
    # largest-share witness per type in each half (the directional observations)
    leaders = {vt: {"odd": mss[int(np.nanargmax(o[:, j]))], "even": mss[int(np.nanargmax(e[:, j]))]}
               for j, vt in enumerate(sc.VARIANT_TYPES)}
    return dict(halves=halves,
                cross_half_tv=pd.DataFrame(cross, index=[f"{m}_odd" for m in mss],
                                           columns=[f"{m}_even" for m in mss]).round(4).to_dict(),
                same_mean=round(float(np.diag(cross).mean()), 4), cross_mean=round(float(cross[off].mean()), 4),
                gap=round(float(gap), 4), gap_null_mean=round(float(ng.mean()), 4),
                gap_null_sd=round(float(ng.std()), 4), gap_p=round(sc.perm_p(ng, gap), 4),
                nearest_self=nearest, n_witnesses=len(mss), nearest_p=round(sc.perm_p(nn, nearest), 4),
                profiles_percent=profiles, largest_share=leaders)


# 4 ─ Sinaiticus and Bezae chapter by chapter ──────────────────────

def aleph_d_by_chapter():
    v = load("variants_full_john_B.csv")
    v = v.assign(key=v.verse + "|" + v.base_reading.astype(str) + "|" + v.ms_reading.astype(str))
    rows = []
    for ch in sorted(v.chapter.unique()):
        g = v[v.chapter == ch]
        for w in ["D", "P66", "A"]:
            kw = g[g.manuscript == w]
            if len(kw) == 0:
                continue
            s = int(kw.key.isin(set(g[g.manuscript == "aleph"].key)).sum())
            rows.append(dict(chapter=int(ch), witness=w, shared=s, variants=int(len(kw)),
                             percent=round(100 * s / len(kw), 1)))
    return rows


def plot_by_chapter(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"
    d = pd.DataFrame(rows)
    d = d[d.witness == "D"].sort_values("chapter")
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=300)
    colors = ["#3b6ea8" if c < 8 else ("#7f7f7f" if c == 8 else "#c8742b") for c in d.chapter]
    ax.bar(d.chapter, d.percent, color=colors, width=0.7)
    for _, r in d.iterrows():
        ax.text(r.chapter, r.percent + 0.8, f"n={r.variants}", ha="center", va="bottom", fontsize=6.5, color="#444")
    ax.set_xticks(range(1, 22))
    ax.set_xlim(0.4, 21.6)
    ax.set_xlabel("Chapter of John (chapters 2 and 19 are not extant in D's first hand)")
    ax.set_ylabel("Bezae's variants shared\nwith Sinaiticus (%)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#3b6ea8", label="chapters 1–7 (within 1:1–8:38)"),
                       Patch(color="#7f7f7f", label="chapter 8 (divided at 8:38)"),
                       Patch(color="#c8742b", label="chapters 9–21")],
              frameon=False, fontsize=7.5, loc="upper right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(parts=("within", "masking", "typology", "chapters")):
    path = OUT / "supplementary_checks.json"
    res = {}
    if "within" in parts:
        res["within_class_d"] = {a: within_class(pkl(s)) for a, s in ANCHORS.items()}
    if "masking" in parts:
        res["content_vs_random_masking"] = masked_vs_random()
    if "typology" in parts:
        cv = common_verses()
        res["typology_split_half"] = {}
        for a, s in ANCHORS.items():
            v = load(f"variants_full_john_{s}.csv")
            res["typology_split_half"][a] = {"full": typology_split_half(v),
                                              "attested_loci": typology_split_half(v[v.verse.isin(cv)])}
    if "chapters" in parts:
        rows = aleph_d_by_chapter()
        res["aleph_shared_by_chapter_anchor_B"] = rows
        plot_by_chapter(rows, OUT / "fig8_aleph_D_by_chapter.png")
    merged = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    merged.update(res)   # parts computed in separate runs are kept
    path.write_text(json.dumps(merged, indent=1, ensure_ascii=False), encoding="utf-8")
    print("done:", ", ".join(parts))


if __name__ == "__main__":
    import sys
    main(tuple(sys.argv[1:]) or ("within", "masking", "typology", "chapters"))
