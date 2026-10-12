"""Block-level inference for the manuscript change profiles.

Two groups of tests are run:

* typology tests (chi-square and Cramér's V on the variant-type
  distributions) need only the variant CSV in ``data/``;
* embedding tests (Cohen's d of inter- vs intra-manuscript cosine distances,
  k-means ARI, split-half replicability, chapter stability, cumulative ARI)
  need the change vectors produced by ``profile_scribes.py``.

Uncertainty is quantified with a chapter-level block bootstrap; significance
with chapter-restricted label permutations.  Permutation p-values are
reported as (k + 1) / (B + 1), the smallest attainable value being 1/(B + 1).
"""
import argparse
import logging
import os
import random
from itertools import combinations

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.spatial.distance import cdist, cosine, pdist, squareform
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VARIANT_TYPES = ['substitution_morphological', 'substitution_lexical',
                 'substitution_word_order', 'addition', 'omission']
BROAD = ['sub_total', 'addition', 'omission']
SUB = ['substitution_morphological', 'substitution_lexical', 'substitution_word_order']
COMMON_VERSES_PATH = "data/common_extant_verses.txt"


def set_reproducible_seeds(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass
    logger.info(f"Random seeds fixed to {seed}")


def perm_p(null_values, observed):
    """Permutation p-value with the +1 correction (Phipson & Smyth 2010)."""
    null_values = np.asarray(null_values)
    return (np.sum(null_values >= observed) + 1) / (len(null_values) + 1)


def suffix_for(base_ms='B', ablation_type=None):
    return f"ablation_{ablation_type}" if ablation_type else base_ms


def load_variant_csv(base_ms='B', ablation_type=None):
    path = (f"data/variants_ablation_{ablation_type}.csv" if ablation_type
            else f"data/variants_full_john_{base_ms}.csv")
    return pd.read_csv(path)


def load_data(base_ms='B', ablation_type=None):
    """Load the embedding pickle and derive manuscript and chapter centroids."""
    suffix = suffix_for(base_ms, ablation_type)
    df = pd.read_pickle(f"outputs/variants_full_with_vectors_{suffix}.pkl")
    profiles, ch_profiles = {}, {}
    for ms in sorted(df['manuscript'].unique()):
        ms_df = df[df['manuscript'] == ms]
        profiles[ms] = np.mean(np.array(ms_df['change_vector'].tolist()), axis=0)
        for ch in sorted(ms_df['chapter'].unique()):
            ch_df = ms_df[ms_df['chapter'] == ch]
            ch_profiles[f"{ms}_ch{ch}"] = np.mean(np.array(ch_df['change_vector'].tolist()), axis=0)
    return df, profiles, ch_profiles


# --------------------------------------------------------------------------
# Effect sizes
# --------------------------------------------------------------------------

def calc_cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    if pooled_var == 0 or np.isnan(pooled_var):
        return 0.0
    val = (np.mean(group1) - np.mean(group2)) / np.sqrt(pooled_var)
    return 0.0 if np.isnan(val) else float(val)


def calc_cramers_v(contingency_table):
    chi2 = stats.chi2_contingency(contingency_table)[0]
    n = contingency_table.values.sum()
    min_dim = min(contingency_table.shape) - 1
    if n == 0 or min_dim == 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def inter_intra_cosine(vecs, labels, ids=None):
    """Pairwise cosine distances split into inter- and intra-manuscript sets.

    ``ids`` are the identities of the observations; a pair of two copies of the
    same observation (which a block bootstrap produces when it draws a chapter
    twice) has distance zero by construction and is excluded."""
    dists = pdist(vecs, metric='cosine')
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


def contingency(df, columns, label_col='manuscript'):
    rows = []
    for ms in sorted(df[label_col].unique()):
        counts = df.loc[df[label_col] == ms, 'type'].value_counts()
        row = {'manuscript': ms}
        if 'sub_total' in columns:
            row['sub_total'] = sum(counts.get(t, 0) for t in SUB)
            row['addition'] = counts.get('addition', 0)
            row['omission'] = counts.get('omission', 0)
        else:
            row.update({t: counts.get(t, 0) for t in SUB})
        rows.append(row)
    table = pd.DataFrame(rows).set_index('manuscript')
    return table.loc[:, (table != 0).any(axis=0)]


def shuffle_labels_within_chapters(df):
    """Permute manuscript labels inside each chapter block."""
    shuffled = df['manuscript'].to_numpy().copy()
    chapters = df['chapter'].to_numpy()
    for ch in np.unique(chapters):
        idx = np.where(chapters == ch)[0]
        shuffled[idx] = np.random.permutation(shuffled[idx])
    return shuffled


# --------------------------------------------------------------------------
# Typology tests (variant CSV only)
# --------------------------------------------------------------------------

def block_bootstrap_cramers_v(df, columns, n_bootstraps=200):
    chapters = df['chapter'].unique()
    vs = []
    for _ in range(n_bootstraps):
        sampled = np.random.choice(chapters, size=len(chapters), replace=True)
        boot_df = pd.concat([df[df['chapter'] == ch] for ch in sampled])
        table = contingency(boot_df, columns)
        if not table.empty and table.shape[1] > 1:
            vs.append(calc_cramers_v(table))
    if not vs:
        return 0.0, 0.0, 0.0, []
    return np.mean(vs), np.percentile(vs, 2.5), np.percentile(vs, 97.5), vs


def block_permutation_test_cramers_v(df, columns, n_permutations=200):
    table = contingency(df, columns)
    true_v = calc_cramers_v(table) if not table.empty and table.shape[1] > 1 else 0.0
    perm_vs = []
    work = df[['chapter', 'manuscript', 'type']].copy()
    for _ in range(n_permutations):
        work['perm'] = shuffle_labels_within_chapters(work)
        p_table = contingency(work, columns, label_col='perm')
        perm_vs.append(calc_cramers_v(p_table) if not p_table.empty and p_table.shape[1] > 1 else 0.0)
    return true_v, perm_p(perm_vs, true_v), perm_vs


def run_typology_tests(df, suffix, n_bootstraps=200, n_permutations=200):
    """Chi-square and Cramér's V (broad and substitution sub-types)."""
    results = {}
    for name, columns in (('Broad', BROAD), ('SubTypes', SUB)):
        table = contingency(df, columns)
        chi_p = stats.chi2_contingency(table)[1] if table.shape[1] > 1 else 1.0
        v_mean, v_low, v_high, v_boot = block_bootstrap_cramers_v(df, columns, n_bootstraps)
        v_true, v_pval, v_perm = block_permutation_test_cramers_v(df, columns, n_permutations)
        results[name] = dict(chi_p=chi_p, v=v_mean, v_low=v_low, v_high=v_high, v_boot=v_boot,
                             v_true=v_true, v_pval=v_pval, v_perm=v_perm, table=table)
    lines = []
    for name, r in results.items():
        lines.append(f"Chi2 ({name}) p: {r['chi_p']:.2e}")
        lines.append(f"Cramér's V ({name}) Block Bootstrap CI: {r['v']:.4f} [95% CI: {r['v_low']:.4f} - {r['v_high']:.4f}]")
        lines.append(f"Cramér's V ({name}) Null Permutation: Mean={np.mean(r['v_perm']):.4f}, "
                     f"SD={np.std(r['v_perm']):.4f} (p={r['v_pval']:.3e})")
    os.makedirs('outputs', exist_ok=True)
    with open(f"outputs/typology_report_{suffix}.txt", "w", encoding='utf-8') as f:
        f.write(f"Variant-type tests ({suffix}) - N={len(df)} variants\n")
        f.write("\n".join(lines) + "\n")
    pd.DataFrame({
        'Metric': ["Cramer's V Broad", "Cramer's V Sub"],
        'Value': [results['Broad']['v'], results['SubTypes']['v']],
        'CI_Low': [results['Broad']['v_low'], results['SubTypes']['v_low']],
        'CI_High': [results['Broad']['v_high'], results['SubTypes']['v_high']],
        'Null_Mean': [np.mean(results['Broad']['v_perm']), np.mean(results['SubTypes']['v_perm'])],
        'Null_SD': [np.std(results['Broad']['v_perm']), np.std(results['SubTypes']['v_perm'])],
        'Perm_P': [results['Broad']['v_pval'], results['SubTypes']['v_pval']],
        'Chi2_P': [results['Broad']['chi_p'], results['SubTypes']['chi_p']],
    }).to_csv(f"outputs/typology_results_{suffix}.csv", index=False)
    return results, lines


# --------------------------------------------------------------------------
# Embedding tests
# --------------------------------------------------------------------------

def block_permutation_test_ari(df, n_permutations=200, max_n=3000):
    df_sample = df.sample(n=max_n, random_state=42) if len(df) > max_n else df
    true_labels = df_sample['manuscript'].to_numpy()
    vecs = np.array(df_sample['change_vector'].tolist())
    k = len(np.unique(true_labels))
    pred_labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(vecs)
    true_ari = adjusted_rand_score(true_labels, pred_labels)
    perm_aris = [adjusted_rand_score(shuffle_labels_within_chapters(df_sample), pred_labels)
                 for _ in range(n_permutations)]
    return true_ari, perm_p(perm_aris, true_ari), perm_aris


def block_bootstrap_cohens_d(df, n_bootstraps=100, max_n=1000):
    chapters = df['chapter'].unique()
    d_values = []
    for _ in range(n_bootstraps):
        sampled = np.random.choice(chapters, size=len(chapters), replace=True)
        boot_df = pd.concat([df[df['chapter'] == ch] for ch in sampled])
        subset = boot_df.sample(n=min(len(boot_df), max_n), replace=False)
        d_values.append(inter_intra_d(np.array(subset['change_vector'].tolist()),
                                      subset['manuscript'].to_numpy(),
                                      ids=subset.index.to_numpy()))
    if not d_values:
        return 0.0, 0.0, 0.0, []
    return np.mean(d_values), np.percentile(d_values, 2.5), np.percentile(d_values, 97.5), d_values


def block_permutation_test_cohens_d(df, n_permutations=100, max_n=1000):
    subset = df.sample(n=min(len(df), max_n), replace=False, random_state=42)
    vecs = np.array(subset['change_vector'].tolist())
    true_d = inter_intra_d(vecs, subset['manuscript'].to_numpy())
    perm_ds = [inter_intra_d(vecs, shuffle_labels_within_chapters(subset)) for _ in range(n_permutations)]
    return true_d, perm_p(perm_ds, true_d), perm_ds


def cohens_d_point(df, max_n=4500):
    """Cohen's d on the full set of change vectors (a random sample of ``max_n``
    when the corpus is larger), without resampling: the point estimate the
    bootstrap interval is centred on."""
    sub = df.sample(n=max_n, random_state=42) if len(df) > max_n else df
    return inter_intra_d(np.array(sub['change_vector'].tolist()), sub['manuscript'].to_numpy()), len(sub)


def cohens_d_by_type(df, min_n=100, max_n=1000):
    """Inter/intra Cohen's d computed separately inside each variant class, so
    that the separation is not driven by the differing type composition of
    the manuscripts."""
    out = {}
    for vtype in VARIANT_TYPES:
        sub = df[df['type'] == vtype]
        if len(sub) < min_n or sub['manuscript'].nunique() < 2:
            continue
        sub = sub.sample(n=min(len(sub), max_n), random_state=42)
        out[vtype] = (inter_intra_d(np.array(sub['change_vector'].tolist()),
                                    sub['manuscript'].to_numpy()), len(sub))
    return out


def cohens_d_verse_level(df):
    """Aggregate change vectors to one mean vector per verse and manuscript
    before computing inter/intra Cohen's d, removing the dependence between
    overlapping context windows inside one verse."""
    grouped = df.groupby(['manuscript', 'verse'])['change_vector'].apply(
        lambda s: np.mean(np.array(s.tolist()), axis=0))
    labels = grouped.index.get_level_values('manuscript').to_numpy()
    vecs = np.array(grouped.tolist())
    return inter_intra_d(vecs, labels), len(vecs)


def pairwise_centroid_d(df, max_n=600):
    """Cohen's d for every pair of manuscripts (inter vs intra within the pair)."""
    out = {}
    for ms1, ms2 in combinations(sorted(df['manuscript'].unique()), 2):
        sub = df[df['manuscript'].isin([ms1, ms2])]
        sub = sub.sample(n=min(len(sub), 2 * max_n), random_state=42)
        out[f"{ms1}-{ms2}"] = inter_intra_d(np.array(sub['change_vector'].tolist()),
                                            sub['manuscript'].to_numpy())
    return out


def _half_centroids(df):
    odd_df, even_df = df[df['chapter'] % 2 != 0], df[df['chapter'] % 2 == 0]
    odd, even = {}, {}
    for ms in sorted(df['manuscript'].unique()):
        o, e = odd_df[odd_df['manuscript'] == ms], even_df[even_df['manuscript'] == ms]
        if len(o) and len(e):
            odd[ms] = np.mean(np.array(o['change_vector'].tolist()), axis=0)
            even[ms] = np.mean(np.array(e['change_vector'].tolist()), axis=0)
    return odd, even


def _restrict_to_common_verses(df, common_verses_path):
    if common_verses_path and os.path.exists(common_verses_path):
        with open(common_verses_path, encoding='utf-8') as fh:
            common = set(line.strip() for line in fh if line.strip())
        return df[df['verse'].isin(common)], len(common)
    return df, 0


def odd_even_split_replicability(df, common_verses_path=None):
    """Spearman correlation between the six inter-manuscript centroid
    distances computed on odd chapters and on even chapters.

    Returns (rho, p, n_common_verses); n_common_verses is 0 when no
    attested-loci filter was applied."""
    df, n_filtered = _restrict_to_common_verses(df, common_verses_path)
    if n_filtered:
        logger.info(f"Split-half restricted to {len(df)} variants over {n_filtered} attested loci.")
    odd, even = _half_centroids(df)
    mss = sorted(set(odd) & set(even))
    if len(mss) < 3:
        return 0.0, 1.0, n_filtered
    odd_dist, even_dist = [], []
    for ms1, ms2 in combinations(mss, 2):
        d_o, d_e = cosine(odd[ms1], odd[ms2]), cosine(even[ms1], even[ms2])
        if not np.isnan(d_o) and not np.isnan(d_e):
            odd_dist.append(d_o)
            even_dist.append(d_e)
    if len(odd_dist) < 3:
        return 0.0, 1.0, n_filtered
    rho, p_val = stats.spearmanr(odd_dist, even_dist)
    return (0.0, 1.0, n_filtered) if np.isnan(rho) else (float(rho), float(p_val), n_filtered)


def split_half_centroid_matrix(df, suffix, common_verses_path=None):
    """Cosine-distance matrix between all odd-half and even-half centroids
    (2m x 2m) and a same-witness vs cross-witness summary.  Also writes the
    six paired odd/even inter-manuscript distances."""
    df, _ = _restrict_to_common_verses(df, common_verses_path)
    odd, even = _half_centroids(df)
    mss = sorted(set(odd) & set(even))
    if len(mss) < 2:
        return None
    names = [f"{ms}_odd" for ms in mss] + [f"{ms}_even" for ms in mss]
    mat = np.array([odd[ms] for ms in mss] + [even[ms] for ms in mss])
    dist = squareform(pdist(mat, metric='cosine'))
    pd.DataFrame(dist, index=names, columns=names).to_csv(
        f"outputs/split_half_centroids_{suffix}.csv", float_format='%.6f')
    cross = cdist(np.array([odd[ms] for ms in mss]), np.array([even[ms] for ms in mss]), metric='cosine')
    same = np.diag(cross)
    other = cross[~np.eye(len(mss), dtype=bool)]
    nearest = int(np.sum(np.argmin(cross, axis=1) == np.arange(len(mss))))
    pairs = pd.DataFrame([{'pair': f"{a}-{b}", 'odd_distance': cosine(odd[a], odd[b]),
                           'even_distance': cosine(even[a], even[b])}
                          for a, b in combinations(mss, 2)])
    pairs.to_csv(f"outputs/split_half_pairs_{suffix}.csv", index=False, float_format='%.6f')
    return dict(same_mean=float(same.mean()), cross_mean=float(other.mean()),
                nearest_self=nearest, n=len(mss))


def chapter_stability(df, profiles, ch_profiles, suffix):
    rows = []
    for ms in sorted(df['manuscript'].unique()):
        for ch in range(1, 22):
            key = f"{ms}_ch{ch}"
            if key in ch_profiles:
                dist = cosine(profiles[ms], ch_profiles[key])
                if not np.isnan(dist):
                    rows.append({'manuscript': ms, 'chapter': ch, 'distance_to_global': dist})
    pd.DataFrame(rows).to_csv(f"outputs/chapter_stability_{suffix}.csv", index=False)


def cumulative_ari(df, suffix, max_n=2000):
    rows = []
    chapters = sorted(df['chapter'].unique())
    for i in range(1, len(chapters) + 1):
        sub_df = df[df['chapter'].isin(chapters[:i])]
        if len(sub_df) > max_n:
            sub_df = sub_df.sample(n=max_n, random_state=42)
        labels = sub_df['manuscript'].to_numpy()
        k = len(np.unique(labels))
        if k > 1:
            pred = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(
                np.array(sub_df['change_vector'].tolist()))
            rows.append({'chapters': i, 'ari': adjusted_rand_score(labels, pred)})
    pd.DataFrame(rows).to_csv(f"outputs/cumulative_analysis_{suffix}.csv", index=False)


def run_tests(base_ms='B', ablation_type=None, typology_only=False):
    set_reproducible_seeds(42)
    suffix = suffix_for(base_ms, ablation_type)
    pkl_path = f"outputs/variants_full_with_vectors_{suffix}.pkl"
    os.makedirs('outputs', exist_ok=True)

    if typology_only or not os.path.exists(pkl_path):
        if not typology_only:
            logger.warning(f"{pkl_path} not found: running the variant-type tests only. "
                           f"Run profile_scribes.py to enable the embedding tests.")
        df = load_variant_csv(base_ms, ablation_type)
        _, lines = run_typology_tests(df, suffix)
        logger.info(f"Variant-type tests ({suffix}, N={len(df)})\n" + "\n".join(lines))
        return

    df, profiles, ch_profiles = load_data(base_ms, ablation_type)
    logger.info(f"Running block-inference statistics for {suffix} (N={len(df)})...")

    d_point, n_point = cohens_d_point(df)
    d_mean, d_low, d_high, d_boot = block_bootstrap_cohens_d(df, n_bootstraps=100)
    d_true, d_pval, d_perm = block_permutation_test_cohens_d(df, n_permutations=100)

    static = df.sample(n=min(len(df), 1500), random_state=42)
    inter_static, intra_static = inter_intra_cosine(np.array(static['change_vector'].tolist()),
                                                    static['manuscript'].to_numpy())
    try:
        p_value_mw = stats.mannwhitneyu(intra_static, inter_static, alternative='less')[1]
    except ValueError:
        p_value_mw = 1.0

    ari_val, ari_pval, ari_perm = block_permutation_test_ari(df, n_permutations=200)
    typology, typology_lines = run_typology_tests(df, suffix)

    split_rho, split_p, _ = odd_even_split_replicability(df)
    split_rho_filt, split_p_filt, n_common = odd_even_split_replicability(df, COMMON_VERSES_PATH)
    half_geom = split_half_centroid_matrix(df, suffix, COMMON_VERSES_PATH)

    d_by_type = cohens_d_by_type(df)
    d_verse, n_verse_units = cohens_d_verse_level(df)
    d_pairs = pairwise_centroid_d(df)

    chapter_stability(df, profiles, ch_profiles, suffix)
    cumulative_ari(df, suffix)

    np.savez(f"outputs/null_distributions_{suffix}.npz",
             ari_perm=ari_perm, cohens_d_perm=d_perm, cohens_d_boot=d_boot,
             v_broad_perm=typology['Broad']['v_perm'], v_broad_boot=typology['Broad']['v_boot'],
             v_sub_perm=typology['SubTypes']['v_perm'], v_sub_boot=typology['SubTypes']['v_boot'])

    report = [f"Summary for John 1-21 Analysis ({suffix}) - N={len(df)} variants",
              f"MW-U p: {p_value_mw:.2e}",
              f"Cohen's d (Inter-Intra), all N={n_point}: {d_point:.4f}",
              f"Cohen's d (Inter-Intra) Block Bootstrap CI: {d_mean:.4f} [95% CI: {d_low:.4f} - {d_high:.4f}]",
              f"Cohen's d Null Permutation: observed (sample of {min(len(df), 1000)})={d_true:.4f}, "
              f"Mean={np.mean(d_perm):.4f}, SD={np.std(d_perm):.4f} (p={d_pval:.3e})",
              f"Cohen's d (verse-level aggregation, N_units={n_verse_units}): {d_verse:.4f}",
              f"ARI (Block Permutation Test): {ari_val:.4f} (p={ari_pval:.3e})",
              f"ARI Null Permutation: Mean={np.mean(ari_perm):.4f}, SD={np.std(ari_perm):.4f}"]
    report += typology_lines
    report.append(f"Odd/Even Rank Correlation (full attested): Spearman rho = {split_rho:.4f} (p={split_p:.4f})")
    report.append(f"Odd/Even Rank Correlation (attested-loci filter, N_verses={n_common}): "
                  f"Spearman rho = {split_rho_filt:.4f} (p={split_p_filt:.4f})")
    if half_geom:
        report.append(f"Split-half centroids: same-witness odd/even distance = {half_geom['same_mean']:.4f}, "
                      f"cross-witness = {half_geom['cross_mean']:.4f}, "
                      f"{half_geom['nearest_self']}/{half_geom['n']} witnesses nearest to their own other half")
    for vtype, (d_val, n) in d_by_type.items():
        report.append(f"Cohen's d within {vtype} (n={n}): {d_val:.4f}")
    for pair, d_val in d_pairs.items():
        report.append(f"Cohen's d pair {pair}: {d_val:.4f}")

    with open(f"outputs/pilot_report_full_{suffix}.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(report) + "\n")

    metrics = [('ARI', ari_val, None, None, np.mean(ari_perm), np.std(ari_perm), ari_pval),
               ("Cohen's d", d_point, d_low, d_high, np.mean(d_perm), np.std(d_perm), d_pval),
               ("Cohen's d Bootstrap Mean", d_mean, d_low, d_high, None, None, None),
               ("Cohen's d Permutation Sample", d_true, None, None, np.mean(d_perm), np.std(d_perm), d_pval),
               ("Cohen's d Verse", d_verse, None, None, None, None, None),
               ("Cramer's V Broad", typology['Broad']['v'], typology['Broad']['v_low'], typology['Broad']['v_high'],
                np.mean(typology['Broad']['v_perm']), np.std(typology['Broad']['v_perm']), typology['Broad']['v_pval']),
               ("Cramer's V Sub", typology['SubTypes']['v'], typology['SubTypes']['v_low'], typology['SubTypes']['v_high'],
                np.mean(typology['SubTypes']['v_perm']), np.std(typology['SubTypes']['v_perm']), typology['SubTypes']['v_pval']),
               ('Odd_Even_Split_Rho_Full', split_rho, None, None, None, None, split_p),
               ('Odd_Even_Split_Rho_AttestLoci', split_rho_filt, None, None, None, None, split_p_filt)]
    metrics += [(f"Cohen's d {vtype}", d_val, None, None, None, None, None) for vtype, (d_val, _) in d_by_type.items()]
    metrics += [(f"Cohen's d {pair}", d_val, None, None, None, None, None) for pair, d_val in d_pairs.items()]
    pd.DataFrame(metrics, columns=['Metric', 'Value', 'CI_Low', 'CI_High', 'Null_Mean', 'Null_SD', 'Perm_P']
                 ).to_csv(f"outputs/pilot_results_full_{suffix}.csv", index=False)
    logger.info("\n" + "\n".join(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None, help='Ablation dataset (matched, func_words, masked, random_masked)')
    parser.add_argument('--typology-only', action='store_true',
                        help='Run only the variant-type tests (no embeddings needed)')
    args = parser.parse_args()
    run_tests(base_ms=args.baseline, ablation_type=args.ablation, typology_only=args.typology_only)
