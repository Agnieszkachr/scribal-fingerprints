"""Block-level inference shared by the pilot (scribal-fingerprints) and the
multi-corpus pipeline (SCRIPTA). The file is identical in both repositories,
so that the same data give the same numbers in both.

Every resampling procedure draws from its own random generator, seeded with
``SEED``. Its result therefore depends only on its input (the data and their
row order), not on which other procedures ran before it.

Uncertainty: chapter-level block bootstrap. Significance: permutation of the
witness labels within chapters, p = (k + 1) / (B + 1) (Phipson and Smyth 2010).
Effect sizes are point estimates on all observations; the bootstrap supplies
their intervals.
"""
from itertools import combinations

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.spatial.distance import cdist, cosine, pdist, squareform
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

SEED = 42
N_BOOT = 2000          # block bootstrap replicates (Cohen's d, Cramér's V)
N_PERM_D = 2000        # block permutations, Cohen's d
N_PERM = 200           # block permutations, Cramér's V and ARI
N_PERM_SPLIT = 500     # block permutations, split-half geometry
D_BOOT_MAX_N = 1000    # vectors per bootstrap replicate of Cohen's d
D_MAX_N = 4500         # vectors for the point estimate and permutation of Cohen's d
ARI_MAX_N = 3000       # vectors for k-means / ARI
CLASS_MAX_N = 1000     # vectors per variant class
PAIR_MAX_N = 600       # vectors per witness in pairwise d
CUMULATIVE_MAX_N = 2000

VARIANT_TYPES = ["substitution_morphological", "substitution_lexical",
                 "substitution_word_order", "addition", "omission"]
BROAD = ["sub_total", "addition", "omission"]
SUB = ["substitution_morphological", "substitution_lexical", "substitution_word_order"]


def rng(seed=SEED):
    return np.random.RandomState(seed)


def type_column(df):
    return "variant_type" if "variant_type" in df.columns else "type"


def perm_p(null_values, observed):
    null_values = np.asarray(null_values, dtype=float)
    if len(null_values) == 0:
        return 1.0
    return float((np.sum(null_values >= observed) + 1) / (len(null_values) + 1))


def calc_cohens_d(group1, group2):
    g1, g2 = np.asarray(group1, dtype=float), np.asarray(group2, dtype=float)
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    if pooled_var == 0 or np.isnan(pooled_var):
        return 0.0
    val = (np.mean(g1) - np.mean(g2)) / np.sqrt(pooled_var)
    return 0.0 if np.isnan(val) else float(val)


def calc_cramers_v(table):
    table = table.loc[table.sum(axis=1) > 0, table.sum(axis=0) > 0]
    n = table.values.sum()
    min_dim = min(table.shape) - 1
    if n == 0 or min_dim == 0:
        return 0.0
    return float(np.sqrt(stats.chi2_contingency(table)[0] / (n * min_dim)))


def contingency(df, columns, label_col="manuscript"):
    tcol = type_column(df)
    rows = []
    for ms in sorted(df[label_col].unique()):
        counts = df.loc[df[label_col] == ms, tcol].value_counts()
        row = {"manuscript": ms}
        if "sub_total" in columns:
            row["sub_total"] = sum(counts.get(t, 0) for t in SUB)
            row["addition"] = counts.get("addition", 0)
            row["omission"] = counts.get("omission", 0)
        else:
            row.update({t: counts.get(t, 0) for t in SUB})
        rows.append(row)
    table = pd.DataFrame(rows).set_index("manuscript")
    return table.loc[:, (table != 0).any(axis=0)]


def shuffle_labels_within_chapters(df, r, label_col="manuscript"):
    shuffled = df[label_col].to_numpy().copy()
    chapters = df["chapter"].to_numpy()
    for ch in np.unique(chapters):
        idx = np.where(chapters == ch)[0]
        shuffled[idx] = r.permutation(shuffled[idx])
    return shuffled


def vectors(df):
    return np.array(df["change_vector"].tolist())


def inter_intra_cosine(vecs, labels, ids=None):
    """Inter- and intra-witness cosine distances; pairs of two copies of the same
    observation (produced by drawing a chapter twice) are excluded."""
    dists = pdist(vecs, metric="cosine")
    labels = np.asarray(labels)
    iu = np.triu_indices(len(labels), k=1)
    same = labels[iu[0]] == labels[iu[1]]
    valid = ~np.isnan(dists)
    if ids is not None:
        ids = np.asarray(ids)
        valid &= ids[iu[0]] != ids[iu[1]]
    return dists[valid & ~same], dists[valid & same]


def inter_intra_d(vecs, labels, ids=None):
    inter, intra = inter_intra_cosine(vecs, labels, ids)
    return calc_cohens_d(inter, intra) if len(inter) and len(intra) else 0.0


# ── Cramér's V ─────────────────────────────────────────────────────

def cramers_v_tests(df, columns, n_boot=N_BOOT, n_perm=N_PERM):
    """Point estimate, block-bootstrap interval and block-permutation null."""
    table = contingency(df, columns)
    v = calc_cramers_v(table) if table.shape[1] > 1 else 0.0
    chi_p = stats.chi2_contingency(table)[1] if table.shape[1] > 1 else 1.0
    r = rng()
    chapters = df["chapter"].unique()
    boot = []
    for _ in range(n_boot):
        sampled = r.choice(chapters, size=len(chapters), replace=True)
        t = contingency(pd.concat([df[df["chapter"] == ch] for ch in sampled]), columns)
        if t.shape[1] > 1:
            boot.append(calc_cramers_v(t))
    r = rng()
    work = df[["chapter", "manuscript", type_column(df)]].copy()
    perm = []
    for _ in range(n_perm):
        work["perm"] = shuffle_labels_within_chapters(work, r)
        t = contingency(work, columns, label_col="perm")
        perm.append(calc_cramers_v(t) if t.shape[1] > 1 else 0.0)
    return dict(v=v, chi_p=chi_p, boot_mean=float(np.mean(boot)), low=float(np.percentile(boot, 2.5)),
                high=float(np.percentile(boot, 97.5)), boot=boot, perm=perm,
                null_mean=float(np.mean(perm)), null_sd=float(np.std(perm)), p=perm_p(perm, v))


# ── Cohen's d ──────────────────────────────────────────────────────

def cohens_d_point(df, max_n=D_MAX_N):
    sub = df.sample(n=max_n, random_state=SEED) if len(df) > max_n else df
    return inter_intra_d(vectors(sub), sub["manuscript"].to_numpy()), len(sub)


def block_bootstrap_cohens_d(df, n_boot=N_BOOT, max_n=D_BOOT_MAX_N):
    r = rng()
    chapters = df["chapter"].unique()
    vals = []
    for _ in range(n_boot):
        sampled = r.choice(chapters, size=len(chapters), replace=True)
        boot_df = pd.concat([df[df["chapter"] == ch] for ch in sampled])
        sub = boot_df.sample(n=min(len(boot_df), max_n), replace=False, random_state=r)
        vals.append(inter_intra_d(vectors(sub), sub["manuscript"].to_numpy(), ids=sub.index.to_numpy()))
    return float(np.mean(vals)), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), vals


def block_permutation_cohens_d(df, n_perm=N_PERM_D, max_n=D_MAX_N):
    """Null for Cohen's d on the same observations as the point estimate.
    The distance matrix is computed once; for each relabelling the inter- and
    intra-witness sums of distances and squared distances are obtained from
    group sums (L' D L), which gives the same d as the pairwise computation."""
    sub = df.sample(n=max_n, replace=False, random_state=SEED) if len(df) > max_n else df
    labels = sub["manuscript"].to_numpy()
    condensed = pdist(vectors(sub), metric="cosine")
    valid = squareform((~np.isnan(condensed)).astype(float))   # pairs with a defined distance
    dist = squareform(np.nan_to_num(condensed))
    dist2 = dist ** 2
    total_n, total_s, total_s2 = valid.sum() / 2, dist.sum() / 2, dist2.sum() / 2
    groups = np.unique(labels)

    def d_for(lbl):
        onehot = (lbl[:, None] == groups[None, :]).astype(float)
        intra_n = float(np.sum(onehot * (valid @ onehot))) / 2
        intra_s = float(np.sum(onehot * (dist @ onehot))) / 2
        intra_s2 = float(np.sum(onehot * (dist2 @ onehot))) / 2
        inter_n, inter_s, inter_s2 = total_n - intra_n, total_s - intra_s, total_s2 - intra_s2
        if intra_n < 2 or inter_n < 2:
            return 0.0
        m1, m2 = inter_s / inter_n, intra_s / intra_n
        v1 = (inter_s2 - inter_n * m1 ** 2) / (inter_n - 1)
        v2 = (intra_s2 - intra_n * m2 ** 2) / (intra_n - 1)
        pooled = ((inter_n - 1) * v1 + (intra_n - 1) * v2) / (inter_n + intra_n - 2)
        return 0.0 if pooled <= 0 else float((m1 - m2) / np.sqrt(pooled))

    true_d = d_for(labels)
    r = rng()
    perm = [d_for(shuffle_labels_within_chapters(sub, r)) for _ in range(n_perm)]
    return true_d, perm_p(perm, true_d), perm


def cohens_d_by_type(df, min_n=100, max_n=CLASS_MAX_N):
    tcol = type_column(df)
    out = {}
    for vtype in VARIANT_TYPES:
        sub = df[df[tcol] == vtype]
        if len(sub) < min_n or sub["manuscript"].nunique() < 2:
            continue
        sub = sub.sample(n=min(len(sub), max_n), random_state=SEED)
        out[vtype] = (inter_intra_d(vectors(sub), sub["manuscript"].to_numpy()), len(sub))
    return out


def cohens_d_verse_level(df):
    grouped = df.groupby(["manuscript", "verse"])["change_vector"].apply(
        lambda s: np.mean(np.array(s.tolist()), axis=0))
    labels = grouped.index.get_level_values("manuscript").to_numpy()
    return inter_intra_d(np.array(grouped.tolist()), labels), len(grouped)


def pairwise_d(df, max_n=PAIR_MAX_N):
    out = {}
    for a, b in combinations(sorted(df["manuscript"].unique()), 2):
        sub = df[df["manuscript"].isin([a, b])]
        sub = sub.sample(n=min(len(sub), 2 * max_n), random_state=SEED)
        out[f"{a}-{b}"] = inter_intra_d(vectors(sub), sub["manuscript"].to_numpy())
    return out


def mann_whitney_p(df, n=1500):
    sub = df.sample(n=min(len(df), n), random_state=SEED)
    inter, intra = inter_intra_cosine(vectors(sub), sub["manuscript"].to_numpy())
    try:
        return float(stats.mannwhitneyu(intra, inter, alternative="less")[1])
    except ValueError:
        return 1.0


# ── Clustering ─────────────────────────────────────────────────────

def block_permutation_ari(df, n_perm=N_PERM, max_n=ARI_MAX_N):
    sub = df.sample(n=max_n, random_state=SEED) if len(df) > max_n else df
    labels = sub["manuscript"].to_numpy()
    pred = KMeans(n_clusters=len(np.unique(labels)), random_state=SEED, n_init=10).fit_predict(vectors(sub))
    true_ari = adjusted_rand_score(labels, pred)
    r = rng()
    perm = [adjusted_rand_score(shuffle_labels_within_chapters(sub, r), pred) for _ in range(n_perm)]
    return true_ari, perm_p(perm, true_ari), perm


def cumulative_ari(df, max_n=CUMULATIVE_MAX_N):
    rows = []
    chapters = sorted(df["chapter"].unique())
    for i in range(1, len(chapters) + 1):
        sub = df[df["chapter"].isin(chapters[:i])]
        if len(sub) > max_n:
            sub = sub.sample(n=max_n, random_state=SEED)
        labels = sub["manuscript"].to_numpy()
        k = len(np.unique(labels))
        if k > 1:
            pred = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit_predict(vectors(sub))
            rows.append({"chapters": i, "ari": adjusted_rand_score(labels, pred)})
    return pd.DataFrame(rows)


# ── Split halves ───────────────────────────────────────────────────

def restrict_to_verses(df, verses):
    return df[df["verse"].isin(verses)] if verses else df


def half_centroids(df):
    odd_df, even_df = df[df["chapter"] % 2 != 0], df[df["chapter"] % 2 == 0]
    odd, even = {}, {}
    for ms in sorted(df["manuscript"].unique()):
        o, e = odd_df[odd_df["manuscript"] == ms], even_df[even_df["manuscript"] == ms]
        if len(o) and len(e):
            odd[ms] = vectors(o).mean(axis=0)
            even[ms] = vectors(e).mean(axis=0)
    return odd, even


def split_half_rho(df):
    odd, even = half_centroids(df)
    mss = sorted(set(odd) & set(even))
    if len(mss) < 3:
        return 0.0, 1.0
    o = [cosine(odd[a], odd[b]) for a, b in combinations(mss, 2)]
    e = [cosine(even[a], even[b]) for a, b in combinations(mss, 2)]
    rho, p = stats.spearmanr(o, e)
    return (0.0, 1.0) if np.isnan(rho) else (float(rho), float(p))


def split_half_geometry(df, n_perm=N_PERM_SPLIT):
    """Odd/even centroid matrix (2m x 2m), paired distances, same- vs
    cross-witness summary, and a block-permutation test of the gap and of the
    nearest-self count."""
    odd, even = half_centroids(df)
    mss = sorted(set(odd) & set(even))
    if len(mss) < 2:
        return None
    names = [f"{ms}_odd" for ms in mss] + [f"{ms}_even" for ms in mss]
    matrix = pd.DataFrame(squareform(pdist(np.array([odd[m] for m in mss] + [even[m] for m in mss]),
                                           metric="cosine")), index=names, columns=names)
    cross = cdist(np.array([odd[m] for m in mss]), np.array([even[m] for m in mss]), metric="cosine")
    off = ~np.eye(len(mss), dtype=bool)
    same, other = np.diag(cross), cross[off]
    nearest = int(np.sum(np.argmin(cross, axis=1) == np.arange(len(mss))))
    pairs = pd.DataFrame([{"pair": f"{a}-{b}", "odd_distance": cosine(odd[a], odd[b]),
                           "even_distance": cosine(even[a], even[b])} for a, b in combinations(mss, 2)])
    vecs_all = vectors(df)
    odd_mask = (df["chapter"].to_numpy() % 2) != 0

    def geometry(lbl):
        o = np.array([vecs_all[(lbl == m) & odd_mask].mean(axis=0) for m in mss])
        e = np.array([vecs_all[(lbl == m) & ~odd_mask].mean(axis=0) for m in mss])
        c = cdist(o, e, metric="cosine")
        return c[off].mean() - np.diag(c).mean(), int(np.sum(np.argmin(c, axis=1) == np.arange(len(mss))))

    gap = float(other.mean() - same.mean())
    r = rng()
    null = [geometry(shuffle_labels_within_chapters(df, r)) for _ in range(n_perm)]
    null_gap, null_near = np.array([g for g, _ in null]), np.array([k for _, k in null])
    return dict(matrix=matrix, pairs=pairs, same_mean=float(same.mean()), cross_mean=float(other.mean()),
                nearest_self=nearest, n=len(mss), gap=gap, gap_null_mean=float(null_gap.mean()),
                gap_null_sd=float(null_gap.std()), gap_p=perm_p(null_gap, gap), nearest_p=perm_p(null_near, nearest))


def chapter_stability(df):
    rows = []
    for ms in sorted(df["manuscript"].unique()):
        ms_df = df[df["manuscript"] == ms]
        global_p = vectors(ms_df).mean(axis=0)
        for ch in sorted(ms_df["chapter"].unique()):
            d = cosine(global_p, vectors(ms_df[ms_df["chapter"] == ch]).mean(axis=0))
            if not np.isnan(d):
                rows.append({"manuscript": ms, "chapter": ch, "distance_to_global": d})
    return pd.DataFrame(rows)


# ── Full battery ───────────────────────────────────────────────────

def embedding_tests(df, common_verses=None):
    """All embedding-level statistics; returns the report lines, the metrics
    table and the auxiliary tables."""
    d_point, n_point = cohens_d_point(df)
    d_mean, d_low, d_high, d_boot = block_bootstrap_cohens_d(df)
    _, d_p, d_perm = block_permutation_cohens_d(df)
    mw_p = mann_whitney_p(df)
    ari, ari_p, ari_perm = block_permutation_ari(df)
    rho, rho_p = split_half_rho(df)
    attested = restrict_to_verses(df, common_verses)
    rho_f, rho_f_p = split_half_rho(attested)
    geom = split_half_geometry(attested)
    by_type = cohens_d_by_type(df)
    d_verse, n_units = cohens_d_verse_level(df)
    pairs = pairwise_d(df)

    lines = [f"MW-U p: {mw_p:.2e}",
             f"Cohen's d (inter vs intra), all N={n_point}: {d_point:.4f}",
             f"Cohen's d block bootstrap ({N_BOOT}): mean {d_mean:.4f} [95% CI: {d_low:.4f} - {d_high:.4f}]",
             f"Cohen's d null ({N_PERM_D} permutations): mean={np.mean(d_perm):.4f}, SD={np.std(d_perm):.4f} (p={d_p:.3e})",
             f"Cohen's d (verse-level aggregation, N_units={n_units}): {d_verse:.4f}",
             f"ARI: {ari:.4f} (p={ari_p:.3e}); null mean={np.mean(ari_perm):.4f}, SD={np.std(ari_perm):.4f}",
             f"Odd/even Spearman rho (full attested): {rho:.4f} (p={rho_p:.4f})",
             f"Odd/even Spearman rho (attested loci, {len(common_verses or [])} verses): {rho_f:.4f} (p={rho_f_p:.4f})"]
    if geom:
        lines += [f"Split-half centroids: same-witness {geom['same_mean']:.4f}, cross-witness {geom['cross_mean']:.4f}, "
                  f"{geom['nearest_self']}/{geom['n']} nearest to their own other half",
                  f"Split-half permutation ({N_PERM_SPLIT}): gap = {geom['gap']:.4f}, null {geom['gap_null_mean']:.4f} "
                  f"+/- {geom['gap_null_sd']:.4f}, p = {geom['gap_p']:.4f}; nearest-self p = {geom['nearest_p']:.4f}"]
    lines += [f"Cohen's d within {t} (n={n}): {v:.4f}" for t, (v, n) in by_type.items()]
    lines += [f"Cohen's d pair {p}: {v:.4f}" for p, v in pairs.items()]

    metrics = [("ARI", ari, None, None, np.mean(ari_perm), np.std(ari_perm), ari_p),
               ("Cohen's d", d_point, d_low, d_high, np.mean(d_perm), np.std(d_perm), d_p),
               ("Cohen's d Bootstrap Mean", d_mean, d_low, d_high, None, None, None),
               ("Cohen's d Verse", d_verse, None, None, None, None, None),
               ("Odd_Even_Split_Rho_Full", rho, None, None, None, None, rho_p),
               ("Odd_Even_Split_Rho_AttestLoci", rho_f, None, None, None, None, rho_f_p)]
    if geom:
        metrics += [("Split_Half_Same_Witness_Distance", geom["same_mean"], None, None, None, None, None),
                    ("Split_Half_Cross_Witness_Distance", geom["cross_mean"], None, None, None, None, None),
                    ("Split_Half_Gap", geom["gap"], None, None, geom["gap_null_mean"], geom["gap_null_sd"], geom["gap_p"]),
                    ("Split_Half_Nearest_Self", geom["nearest_self"], None, None, None, None, geom["nearest_p"])]
    metrics += [(f"Cohen's d {t}", v, None, None, None, None, None) for t, (v, _) in by_type.items()]
    metrics += [(f"Cohen's d {p}", v, None, None, None, None, None) for p, v in pairs.items()]
    nulls = dict(ari_perm=ari_perm, cohens_d_perm=d_perm, cohens_d_boot=d_boot)
    tables = dict(split_half_centroids=geom["matrix"] if geom else None,
                  split_half_pairs=geom["pairs"] if geom else None,
                  chapter_stability=chapter_stability(df), cumulative_analysis=cumulative_ari(df))
    return lines, metrics, nulls, tables


def typology_tests(df):
    """Cramér's V on the broad classes and on the substitution sub-classes."""
    lines, metrics, nulls = [], [], {}
    for name, label, cols in (("Broad", "Cramer's V Broad", BROAD), ("SubTypes", "Cramer's V Sub", SUB)):
        r = cramers_v_tests(df, cols)
        lines += [f"Chi2 ({name}) p: {r['chi_p']:.2e}",
                  f"Cramér's V ({name}): {r['v']:.4f} [95% block-bootstrap CI ({N_BOOT}): {r['low']:.4f} - {r['high']:.4f}; "
                  f"bootstrap mean {r['boot_mean']:.4f}]",
                  f"Cramér's V ({name}) null ({N_PERM} permutations): mean={r['null_mean']:.4f}, "
                  f"SD={r['null_sd']:.4f} (p={r['p']:.3e})"]
        metrics.append((label, r["v"], r["low"], r["high"], r["null_mean"], r["null_sd"], r["p"]))
        key = "v_broad" if name == "Broad" else "v_sub"
        nulls[f"{key}_perm"], nulls[f"{key}_boot"] = r["perm"], r["boot"]
    return lines, metrics, nulls


METRIC_COLUMNS = ["Metric", "Value", "CI_Low", "CI_High", "Null_Mean", "Null_SD", "Perm_P"]
