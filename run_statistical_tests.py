import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from scipy.spatial.distance import cosine
from itertools import combinations
import os
import argparse
import logging
import random
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def set_reproducible_seeds(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Random seeds fixed to {seed}")

def load_data(base_ms='B', ablation_type=None):
    if ablation_type:
        suffix = f"ablation_{ablation_type}"
    else:
        suffix = base_ms
        
    df = pd.read_pickle(f"outputs/variants_full_with_vectors_{suffix}.pkl")
    profiles = {}
    ch_profiles = {}
    
    for ms in df['manuscript'].unique():
        ms_df = df[df['manuscript'] == ms]
        if not ms_df.empty:
            profiles[ms] = np.mean(ms_df['change_vector'].tolist(), axis=0)
            
        for ch in ms_df['chapter'].unique():
            ch_df = ms_df[ms_df['chapter'] == ch]
            if not ch_df.empty:
                ch_profiles[f"{ms}_ch{ch}"] = np.mean(ch_df['change_vector'].tolist(), axis=0)
                
    return df, profiles, ch_profiles

def calc_cohens_d(group1, group2):
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    if pooled_var == 0 or np.isnan(pooled_var): return 0.0
    val = (np.mean(group1) - np.mean(group2)) / np.sqrt(pooled_var)
    if np.isnan(val): return 0.0
    return val

def calc_cramers_v(contingency_table):
    chi2 = stats.chi2_contingency(contingency_table)[0]
    n = contingency_table.sum().sum()
    min_dim = min(contingency_table.shape) - 1
    if n == 0 or min_dim == 0: return 0.0
    return np.sqrt(chi2 / (n * min_dim))

def block_bootstrap_cramers_v(df, columns, n_bootstraps=200):
    chapters = df['chapter'].unique()
    vs = []
    for _ in range(n_bootstraps):
        sampled_chapters = np.random.choice(chapters, size=len(chapters), replace=True)
        boot_df = pd.concat([df[df['chapter'] == ch] for ch in sampled_chapters])
        
        counts = []
        for ms in boot_df['manuscript'].unique():
            ms_df = boot_df[boot_df['manuscript'] == ms]
            ms_counts = ms_df['type'].value_counts()
            
            if 'sub_total' in columns:
                sub_total = ms_counts.get('substitution_morphological', 0) + ms_counts.get('substitution_lexical', 0) + ms_counts.get('substitution_word_order', 0)
                add = ms_counts.get('addition', 0)
                om = ms_counts.get('omission', 0)
                counts.append({'manuscript': ms, 'sub_total': sub_total, 'addition': add, 'omission': om})
            else:
                counts.append({
                    'manuscript': ms,
                    'substitution_morphological': ms_counts.get('substitution_morphological', 0),
                    'substitution_lexical': ms_counts.get('substitution_lexical', 0),
                    'substitution_word_order': ms_counts.get('substitution_word_order', 0)
                })
        
        c_df = pd.DataFrame(counts).set_index('manuscript')
        c_df = c_df.loc[:, (c_df != 0).any(axis=0)]
        if not c_df.empty and c_df.shape[1] > 1:
            vs.append(calc_cramers_v(c_df))
    
    if not vs: return 0.0, 0.0, 0.0, []
    return np.mean(vs), np.percentile(vs, 2.5), np.percentile(vs, 97.5), vs

def block_permutation_test_ari(df, n_permutations=200):
    clusters = KMeans(n_clusters=len(df['manuscript'].unique()), random_state=42, n_init=1)
    
    if len(df) > 3000:
        df_sample = df.sample(n=3000, random_state=42)
    else:
        df_sample = df.copy()
        
    true_labels = df_sample['manuscript'].tolist()
    vecs = np.array(df_sample['change_vector'].tolist())
    pred_labels = clusters.fit_predict(vecs)
    true_ari = adjusted_rand_score(true_labels, pred_labels)
    
    perm_aris = []
    chapters = df_sample['chapter'].unique()
    
    for _ in range(n_permutations):
        shuffled_df = df_sample.copy()
        for ch in chapters:
            mask = shuffled_df['chapter'] == ch
            if mask.sum() > 0:
                shuffled_df.loc[mask, 'shuffled_ms'] = np.random.permutation(shuffled_df.loc[mask, 'manuscript'].values)
        
        perm_labels = shuffled_df['shuffled_ms'].tolist()
        perm_aris.append(adjusted_rand_score(perm_labels, pred_labels))
        
    p_val = np.sum(np.array(perm_aris) >= true_ari) / n_permutations
    return true_ari, p_val, perm_aris

def block_bootstrap_cohens_d(df, n_bootstraps=100):
    chapters = df['chapter'].unique()
    d_values = []
    from scipy.spatial.distance import pdist
    
    for _ in range(n_bootstraps):
        sampled_chapters = np.random.choice(chapters, size=len(chapters), replace=True)
        boot_df = pd.concat([df[df['chapter'] == ch] for ch in sampled_chapters])
        
        sample_size = min(len(boot_df), 1000)
        subset = boot_df.sample(n=sample_size, replace=False)
        vecs = np.array(subset['change_vector'].tolist())
        labels = np.array(subset['manuscript'].tolist())
        
        dists = pdist(vecs, metric='cosine')
        labels_grid_1, labels_grid_2 = np.meshgrid(labels, labels)
        triu_mask = np.triu(np.ones((len(labels), len(labels)), dtype=bool), k=1)
        
        same_mask = (labels_grid_1 == labels_grid_2)[triu_mask]
        valid = ~np.isnan(dists)
        dists_valid = dists[valid]
        same_mask = same_mask[valid]
        
        intra = dists_valid[same_mask]
        inter = dists_valid[~same_mask]
        
        if len(intra) and len(inter):
            val = calc_cohens_d(inter, intra)
            if not np.isnan(val):
                d_values.append(val)
            
    if not d_values: return 0.0, 0.0, 0.0, []
    return np.mean(d_values), np.percentile(d_values, 2.5), np.percentile(d_values, 97.5), d_values

def block_permutation_test_cohens_d(df, n_permutations=100):
    chapters = df['chapter'].unique()
    from scipy.spatial.distance import pdist
    
    sample_size = min(len(df), 1000)
    subset = df.sample(n=sample_size, replace=False, random_state=42)
    vecs = np.array(subset['change_vector'].tolist())
    labels = np.array(subset['manuscript'].tolist())
    
    dists = pdist(vecs, metric='cosine')
    triu_mask = np.triu(np.ones((len(labels), len(labels)), dtype=bool), k=1)
    
    valid = ~np.isnan(dists)
    dists_valid = dists[valid]
    triu_mask_valid = triu_mask
    
    labels_grid_1, labels_grid_2 = np.meshgrid(labels, labels)
    same_mask = (labels_grid_1 == labels_grid_2)[triu_mask][valid]
    
    intra = dists_valid[same_mask]
    inter = dists_valid[~same_mask]
    true_d = calc_cohens_d(inter, intra) if len(intra) and len(inter) else 0.0
    
    perm_ds = []
    for _ in range(n_permutations):
        shuffled_df = subset.copy()
        for ch in chapters:
            mask = shuffled_df['chapter'] == ch
            if mask.sum() > 0:
                shuffled_df.loc[mask, 'shuffled_ms'] = np.random.permutation(shuffled_df.loc[mask, 'manuscript'].values)
                
        perm_labels = np.array(shuffled_df['shuffled_ms'].tolist())
        pl_grid_1, pl_grid_2 = np.meshgrid(perm_labels, perm_labels)
        p_same_mask = (pl_grid_1 == pl_grid_2)[triu_mask][valid]
        
        p_intra = dists_valid[p_same_mask]
        p_inter = dists_valid[~p_same_mask]
        
        val = calc_cohens_d(p_inter, p_intra) if len(p_intra) and len(p_inter) else 0.0
        perm_ds.append(val)
        
    p_val = np.sum(np.array(perm_ds) >= true_d) / n_permutations if perm_ds else 1.0
    return true_d, p_val, perm_ds

def block_permutation_test_cramers_v(df, columns, n_permutations=200):
    chapters = df['chapter'].unique()
    
    counts = []
    for ms in df['manuscript'].unique():
        ms_df = df[df['manuscript'] == ms]
        ms_counts = ms_df['type'].value_counts()
        
        if 'sub_total' in columns:
            sub_total = ms_counts.get('substitution_morphological', 0) + ms_counts.get('substitution_lexical', 0) + ms_counts.get('substitution_word_order', 0)
            add = ms_counts.get('addition', 0)
            om = ms_counts.get('omission', 0)
            counts.append({'manuscript': ms, 'sub_total': sub_total, 'addition': add, 'omission': om})
        else:
            counts.append({
                'manuscript': ms,
                'substitution_morphological': ms_counts.get('substitution_morphological', 0),
                'substitution_lexical': ms_counts.get('substitution_lexical', 0),
                'substitution_word_order': ms_counts.get('substitution_word_order', 0)
            })
            
    c_df = pd.DataFrame(counts).set_index('manuscript')
    c_df = c_df.loc[:, (c_df != 0).any(axis=0)]
    true_v = calc_cramers_v(c_df) if not c_df.empty and c_df.shape[1] > 1 else 0.0
    
    perm_vs = []
    for _ in range(n_permutations):
        shuffled_df = df.copy()
        for ch in chapters:
            mask = shuffled_df['chapter'] == ch
            if mask.sum() > 0:
                shuffled_df.loc[mask, 'shuffled_ms'] = np.random.permutation(shuffled_df.loc[mask, 'manuscript'].values)
                
        p_counts = []
        for ms in shuffled_df['manuscript'].unique():
            ms_df = shuffled_df[shuffled_df['shuffled_ms'] == ms]
            ms_counts = ms_df['type'].value_counts()
            
            if 'sub_total' in columns:
                sub_total = ms_counts.get('substitution_morphological', 0) + ms_counts.get('substitution_lexical', 0) + ms_counts.get('substitution_word_order', 0)
                add = ms_counts.get('addition', 0)
                om = ms_counts.get('omission', 0)
                p_counts.append({'manuscript': ms, 'sub_total': sub_total, 'addition': add, 'omission': om})
            else:
                p_counts.append({
                    'manuscript': ms,
                    'substitution_morphological': ms_counts.get('substitution_morphological', 0),
                    'substitution_lexical': ms_counts.get('substitution_lexical', 0),
                    'substitution_word_order': ms_counts.get('substitution_word_order', 0)
                })
                
        p_c_df = pd.DataFrame(p_counts).set_index('manuscript')
        p_c_df = p_c_df.loc[:, (p_c_df != 0).any(axis=0)]
        val = calc_cramers_v(p_c_df) if not p_c_df.empty and p_c_df.shape[1] > 1 else 0.0
        perm_vs.append(val)
        
    p_val = np.sum(np.array(perm_vs) >= true_v) / n_permutations if perm_vs else 1.0
    return true_v, p_val, perm_vs

def odd_even_split_replicability(df):
    manuscripts = df['manuscript'].unique()
    odd_df = df[df['chapter'] % 2 != 0]
    even_df = df[df['chapter'] % 2 == 0]
    
    if len(odd_df) == 0 or len(even_df) == 0:
        return 0.0, 1.0
        
    odd_centroids = {}
    even_centroids = {}
    
    for ms in manuscripts:
        odd_ms = odd_df[odd_df['manuscript'] == ms]
        even_ms = even_df[even_df['manuscript'] == ms]
        
        if len(odd_ms) == 0 or len(even_ms) == 0: continue
            
        odd_centroids[ms] = np.mean(np.array(odd_ms['change_vector'].tolist()), axis=0)
        even_centroids[ms] = np.mean(np.array(even_ms['change_vector'].tolist()), axis=0)
        
    common_ms = list(set(odd_centroids.keys()).intersection(set(even_centroids.keys())))
    if len(common_ms) < 3: return 0.0, 1.0
    
    odd_dist = []
    even_dist = []
    
    for i in range(len(common_ms)):
        for j in range(i+1, len(common_ms)):
            ms1, ms2 = common_ms[i], common_ms[j]
            d_o = cosine(odd_centroids[ms1], odd_centroids[ms2])
            d_e = cosine(even_centroids[ms1], even_centroids[ms2])
            if not np.isnan(d_o) and not np.isnan(d_e):
                odd_dist.append(d_o)
                even_dist.append(d_e)
            
    if len(odd_dist) < 3: return 0.0, 1.0
    rho, p_val = stats.spearmanr(odd_dist, even_dist)
    if np.isnan(rho): return 0.0, 1.0
    return rho, p_val

def run_tests(base_ms='B', ablation_type=None):
    set_reproducible_seeds(42)
    if ablation_type:
        suffix = f"ablation_{ablation_type}"
    else:
        suffix = base_ms
        
    pkl_path = f"outputs/variants_full_with_vectors_{suffix}.pkl"
    if not os.path.exists(pkl_path):
        logger.error(f"File {pkl_path} not found.")
        return

    df, profiles_npz, ch_profiles_npz = load_data(base_ms, ablation_type)
    manuscripts = df['manuscript'].unique()
    
    logger.info(f"Running block-inference statistics for {suffix} (N={len(df)})...")

    d_mean, d_low, d_high, d_boot = block_bootstrap_cohens_d(df, n_bootstraps=100)
    d_true, d_pval, d_perm = block_permutation_test_cohens_d(df, n_permutations=100)
    
    sample_vecs = np.array(df.sample(n=min(len(df), 1500), random_state=42)['change_vector'].tolist())
    sample_labels = df.sample(n=min(len(df), 1500), random_state=42)['manuscript'].tolist()
    intra_static, inter_static = [], []
    for i in range(len(sample_vecs)):
        for j in range(i+1, len(sample_vecs)):
            dist = cosine(sample_vecs[i], sample_vecs[j])
            if not np.isnan(dist):
                if sample_labels[i] == sample_labels[j]: intra_static.append(dist)
                else: inter_static.append(dist)
    
    try:
        p_value_mw = stats.mannwhitneyu(intra_static, inter_static, alternative='less')[1]
    except ValueError:
        p_value_mw = 1.0

    ari_val, ari_pval, ari_perm = block_permutation_test_ari(df, n_permutations=200)

    counts_df = pd.read_csv(f"outputs/type_counts_full_{suffix}.csv").set_index('manuscript')
    counts_df['sub_total'] = counts_df[['substitution_morphological', 'substitution_lexical', 'substitution_word_order']].sum(axis=1)
    
    broad_table = counts_df[['sub_total', 'addition', 'omission']].loc[:, (counts_df[['sub_total', 'addition', 'omission']] != 0).any(axis=0)]
    p_val_chi = stats.chi2_contingency(broad_table)[1] if broad_table.shape[1] > 1 else 1.0
    
    sub_table = counts_df[['substitution_morphological', 'substitution_lexical', 'substitution_word_order']].loc[:, (counts_df[['substitution_morphological', 'substitution_lexical', 'substitution_word_order']] != 0).any(axis=0)]
    p_val_sub = stats.chi2_contingency(sub_table)[1] if sub_table.shape[1] > 1 else 1.0
    
    v_broad, v_broad_low, v_broad_high, v_broad_boot = block_bootstrap_cramers_v(df, ['sub_total', 'addition', 'omission'], n_bootstraps=200)
    v_sub, v_sub_low, v_sub_high, v_sub_boot = block_bootstrap_cramers_v(df, ['substitution_morphological', 'substitution_lexical', 'substitution_word_order'], n_bootstraps=200)
    
    v_broad_true, v_broad_pval, v_broad_perm = block_permutation_test_cramers_v(df, ['sub_total', 'addition', 'omission'], n_permutations=200)
    v_sub_true, v_sub_pval, v_sub_perm = block_permutation_test_cramers_v(df, ['substitution_morphological', 'substitution_lexical', 'substitution_word_order'], n_permutations=200)

    split_rho, split_p = odd_even_split_replicability(df)

    stability_data = []
    for ms in manuscripts:
        global_p = profiles_npz[ms]
        for ch in range(1, 22):
            key = f"{ms}_ch{ch}"
            if key in ch_profiles_npz:
                dist = cosine(global_p, ch_profiles_npz[key])
                if not np.isnan(dist):
                    stability_data.append({'manuscript': ms, 'chapter': ch, 'distance_to_global': dist})
    
    stab_df = pd.DataFrame(stability_data)
    stab_df.to_csv(f"outputs/chapter_stability_{suffix}.csv", index=False)

    cumulative_results = []
    sorted_chapters = sorted(df['chapter'].unique())
    for i in range(1, len(sorted_chapters) + 1):
        subset_ch = sorted_chapters[:i]
        sub_df = df[df['chapter'].isin(subset_ch)]
        
        sub_labels = sub_df['manuscript'].tolist()
        sub_vecs = sub_df['change_vector'].tolist()
        if len(sub_vecs) > 2000:
            indices = np.random.choice(len(sub_vecs), 2000, replace=False)
            sub_vecs = [sub_vecs[idx] for idx in indices]
            sub_labels = [sub_labels[idx] for idx in indices]
            
        if len(set(sub_labels)) > 1:
            ari = adjusted_rand_score(sub_labels, KMeans(n_clusters=len(set(sub_labels)), random_state=42, n_init=1).fit_predict(sub_vecs))
            cumulative_results.append({'chapters': i, 'ari': ari})
        
    pd.DataFrame(cumulative_results).to_csv(f"outputs/cumulative_analysis_{suffix}.csv", index=False)

    np.savez(f"outputs/null_distributions_{suffix}.npz", 
             ari_perm=ari_perm, 
             cohens_d_perm=d_perm, cohens_d_boot=d_boot,
             v_broad_perm=v_broad_perm, v_broad_boot=v_broad_boot,
             v_sub_perm=v_sub_perm, v_sub_boot=v_sub_boot)

    report = [f"Summary for John 1-21 Analysis ({suffix}) - N={len(df)} variants"]
    report.append(f"MW-U p: {p_value_mw:.2e}")
    report.append(f"Cohen's d (Inter-Intra) Block Bootstrap CI: {d_mean:.4f} [95% CI: {d_low:.4f} - {d_high:.4f}]")
    report.append(f"Cohen's d Null Permutation: Mean={np.mean(d_perm):.4f}, SD={np.std(d_perm):.4f} (p={d_pval:.3e})")
    report.append(f"ARI (Block Permutation Test): {ari_val:.4f} (p={ari_pval:.3e})")
    report.append(f"ARI Null Permutation: Mean={np.mean(ari_perm):.4f}, SD={np.std(ari_perm):.4f}")
    report.append(f"Chi2 (Broad) p: {p_val_chi:.2e}")
    report.append(f"Cramér's V (Broad) Block Bootstrap CI: {v_broad:.4f} [95% CI: {v_broad_low:.4f} - {v_broad_high:.4f}]")
    report.append(f"Cramér's V (Broad) Null Permutation: Mean={np.mean(v_broad_perm):.4f}, SD={np.std(v_broad_perm):.4f} (p={v_broad_pval:.3e})")
    report.append(f"Chi2 (SubTypes) p: {p_val_sub:.2e}")
    report.append(f"Cramér's V (SubTypes) Block Bootstrap CI: {v_sub:.4f} [95% CI: {v_sub_low:.4f} - {v_sub_high:.4f}]")
    report.append(f"Cramér's V (SubTypes) Null Permutation: Mean={np.mean(v_sub_perm):.4f}, SD={np.std(v_sub_perm):.4f} (p={v_sub_pval:.3e})")
    report.append(f"Odd/Even Rank Correlation: Spearman rho = {split_rho:.4f} (p={split_p:.4f})")
    
    with open(f"outputs/pilot_report_full_{suffix}.txt", "w") as f:
        f.write("\n".join(report))
    
    pd.DataFrame({
        'Metric': ['ARI', 'Cohen\'s d', 'Cramer\'s V Broad', 'Cramer\'s V Sub', 'Odd_Even_Split_Rho'], 
        'Value': [ari_val, d_mean, v_broad, v_sub, split_rho],
        'CI_Low': [None, d_low, v_broad_low, v_sub_low, None],
        'CI_High': [None, d_high, v_broad_high, v_sub_high, None],
        'Null_Mean': [np.mean(ari_perm), np.mean(d_perm), np.mean(v_broad_perm), np.mean(v_sub_perm), None],
        'Null_SD': [np.std(ari_perm), np.std(d_perm), np.std(v_broad_perm), np.std(v_sub_perm), None],
        'Perm_P': [ari_pval, d_pval, v_broad_pval, v_sub_pval, None]
    }).to_csv(f"outputs/pilot_results_full_{suffix}.csv", index=False)
    
    logger.info("\n" + "\n".join(report))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None, help='Ablation type (func_words, masked)')
    args = parser.parse_args()
    run_tests(base_ms=args.baseline, ablation_type=args.ablation)
