"""Block-level inference for the manuscript change profiles.

Two groups of tests are run:

* typology tests (chi-square and Cramér's V on the variant-type
  distributions) need only the variant CSV in ``data/``;
* embedding tests (Cohen's d of inter- vs intra-manuscript cosine distances,
  k-means ARI, split-half replicability, chapter stability, cumulative ARI)
  need the change vectors produced by ``profile_scribes.py``.

The statistics themselves are in ``src/stats_core.py``, which is shared with
the multi-corpus pipeline: uncertainty is quantified with a chapter-level
block bootstrap, significance with chapter-restricted label permutations,
p = (k + 1) / (B + 1). Every resampling procedure has its own seeded random
generator.
"""
import argparse
import logging
import os

import numpy as np
import pandas as pd

from src import stats_core as sc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

COMMON_VERSES_PATH = "data/common_extant_verses.txt"


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


def common_verses(path=COMMON_VERSES_PATH):
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as fh:
        return set(line.strip() for line in fh if line.strip())


def odd_even_split_replicability(df, common_verses_path=None):
    """Spearman rho of the inter-witness centroid distances, odd vs even chapters."""
    verses = common_verses(common_verses_path) if common_verses_path else None
    rho, p = sc.split_half_rho(sc.restrict_to_verses(df, verses))
    return rho, p, len(verses or [])


def run_typology_tests(df, suffix):
    lines, metrics, nulls = sc.typology_tests(df)
    os.makedirs('outputs', exist_ok=True)
    with open(f"outputs/typology_report_{suffix}.txt", "w", encoding='utf-8') as f:
        f.write(f"Variant-type tests ({suffix}) - N={len(df)} variants\n" + "\n".join(lines) + "\n")
    table = pd.DataFrame(metrics, columns=sc.METRIC_COLUMNS)
    table['Chi2_P'] = [float(l.split('p: ')[1]) for l in lines if l.startswith('Chi2')]
    table.to_csv(f"outputs/typology_results_{suffix}.csv", index=False)
    return lines, metrics, nulls


def run_tests(base_ms='B', ablation_type=None, typology_only=False):
    suffix = suffix_for(base_ms, ablation_type)
    pkl_path = f"outputs/variants_full_with_vectors_{suffix}.pkl"
    os.makedirs('outputs', exist_ok=True)

    if typology_only or not os.path.exists(pkl_path):
        if not typology_only:
            logger.warning(f"{pkl_path} not found: running the variant-type tests only. "
                           f"Run profile_scribes.py to enable the embedding tests.")
        df = load_variant_csv(base_ms, ablation_type)
        lines, _, _ = run_typology_tests(df, suffix)
        logger.info(f"Variant-type tests ({suffix}, N={len(df)})\n" + "\n".join(lines))
        return

    df, _, _ = load_data(base_ms, ablation_type)
    logger.info(f"Running block-inference statistics for {suffix} (N={len(df)})...")
    emb_lines, emb_metrics, emb_nulls, tables = sc.embedding_tests(df, common_verses())
    typ_lines, typ_metrics, typ_nulls = run_typology_tests(df, suffix)

    if tables['split_half_centroids'] is not None:
        tables['split_half_centroids'].to_csv(f"outputs/split_half_centroids_{suffix}.csv", float_format='%.6f')
        tables['split_half_pairs'].to_csv(f"outputs/split_half_pairs_{suffix}.csv", index=False, float_format='%.6f')
    tables['chapter_stability'].to_csv(f"outputs/chapter_stability_{suffix}.csv", index=False)
    tables['cumulative_analysis'].to_csv(f"outputs/cumulative_analysis_{suffix}.csv", index=False)
    np.savez(f"outputs/null_distributions_{suffix}.npz", **emb_nulls, **typ_nulls)

    report = [f"Summary for John 1-21 Analysis ({suffix}) - N={len(df)} variants"] + emb_lines + typ_lines
    with open(f"outputs/pilot_report_full_{suffix}.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(report) + "\n")
    metrics = emb_metrics[:4] + typ_metrics + emb_metrics[4:]
    pd.DataFrame(metrics, columns=sc.METRIC_COLUMNS).to_csv(f"outputs/pilot_results_full_{suffix}.csv", index=False)
    logger.info("\n" + "\n".join(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None,
                        help='Ablation dataset (matched, func_words, masked, random_masked, random_masked_s1..s4)')
    parser.add_argument('--typology-only', action='store_true',
                        help='Run only the variant-type tests (no embeddings needed)')
    args = parser.parse_args()
    run_tests(base_ms=args.baseline, ablation_type=args.ablation, typology_only=args.typology_only)
