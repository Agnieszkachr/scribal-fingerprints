"""Figures for one analysis configuration (baseline or ablation suffix).

Figures that need the change vectors (PCA, dendrogram) are skipped when the
embedding pickle is absent; the type-distribution plot needs only the type
counts, and the cumulative/stability plots need the CSVs written by
``run_statistical_tests.py``.
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Ellipse
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA

TYPE_COLS = ['substitution_morphological', 'substitution_lexical',
             'substitution_word_order', 'addition', 'omission']


def confidence_ellipse(x, y, ax, n_std=2.0, facecolor='none', **kwargs):
    cov = np.cov(x, y)
    pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    ellipse = Ellipse((0, 0), width=2 * np.sqrt(1 + pearson), height=2 * np.sqrt(1 - pearson),
                      facecolor=facecolor, **kwargs)
    transf = (transforms.Affine2D().rotate_deg(45)
              .scale(np.sqrt(cov[0, 0]) * n_std, np.sqrt(cov[1, 1]) * n_std)
              .translate(np.mean(x), np.mean(y)))
    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def label_for(suffix):
    return f"ablation: {suffix[9:]}" if suffix.startswith('ablation_') else f"baseline {suffix}"


def plot_pca(df, ms_colors, suffix, per_ms=400):
    """PCA (2 components) of the change vectors.  A stratified subsample of
    at most ``per_ms`` variants per manuscript is drawn; centroids are
    computed on all variants and shown with 2-SD ellipses."""
    vectors = np.array(df['change_vector'].tolist())
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(vectors)
    df = df.assign(pca_x=coords[:, 0], pca_y=coords[:, 1])
    sample = pd.concat([g.sample(n=min(len(g), per_ms), random_state=42)
                        for _, g in df.groupby('manuscript')])

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(x='pca_x', y='pca_y', hue='manuscript', data=sample, alpha=0.35, s=14,
                    ax=ax, palette=ms_colors, linewidth=0, legend=False)
    for ms, g in df.groupby('manuscript'):
        if len(g) > 5:
            confidence_ellipse(g['pca_x'], g['pca_y'], ax, n_std=2.0, edgecolor=ms_colors[ms],
                               facecolor=ms_colors[ms], alpha=0.12, linewidth=1.5)
        ax.scatter(g['pca_x'].mean(), g['pca_y'].mean(), marker='X', s=180, color=ms_colors[ms],
                   edgecolor='black', linewidth=1.2, zorder=5, label=f"{ms} (n={len(g)})")
    ax.legend(title='Manuscript centroid', loc='best')
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    ax.set_title(f"Figure 1: PCA of change vectors ({label_for(suffix)}); "
                 f"points: {per_ms} per MS, ellipses: 2 SD")
    plt.tight_layout()
    plt.savefig(f'outputs/fig1_pca_full_{suffix}.png', dpi=200)
    plt.close()


def plot_dendrogram(profiles, suffix):
    ms_list = sorted(profiles)
    matrix = np.array([profiles[ms] for ms in ms_list])
    link = linkage(pdist(matrix, metric='cosine'), method='average')
    plt.figure(figsize=(10, 6))
    dendrogram(link, labels=ms_list)
    plt.ylabel("Cosine distance (average linkage)")
    plt.title(f"Figure 2: Hierarchical clustering of manuscript profiles ({label_for(suffix)})")
    plt.tight_layout()
    plt.savefig(f'outputs/fig2_dendrogram_full_{suffix}.png', dpi=200)
    plt.close()


def plot_types(suffix):
    path = f"outputs/type_counts_full_{suffix}.csv"
    if not os.path.exists(path):
        return
    counts = pd.read_csv(path).set_index('manuscript')
    props = counts[TYPE_COLS].div(counts['total_variants'], axis=0)
    ax = props.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='tab10')
    ax.set_ylabel("Proportion of variants")
    ax.set_xlabel("Manuscript")
    ax.set_xticklabels([f"{ms}\n(n={counts.loc[ms, 'total_variants']})" for ms in props.index], rotation=0)
    ax.legend(title='Variant type', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.title(f"Figure 4: Variant type distribution ({label_for(suffix)})")
    plt.tight_layout()
    plt.savefig(f'outputs/fig4_types_full_{suffix}.png', dpi=200)
    plt.close()


def plot_cumulative(suffix):
    path = f"outputs/cumulative_analysis_{suffix}.csv"
    if not os.path.exists(path):
        return
    cum = pd.read_csv(path)
    plt.figure(figsize=(10, 6))
    plt.plot(cum['chapters'], cum['ari'], marker='o', label='ARI (k-means vs manuscript labels)')
    plt.xlabel("Chapters (cumulative)")
    plt.ylabel("ARI")
    plt.title(f"Figure 6: Cumulative clustering signal ({label_for(suffix)})")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'outputs/fig6_cumulative_{suffix}.png', dpi=200)
    plt.close()


def plot_stability(suffix):
    path = f"outputs/chapter_stability_{suffix}.csv"
    if not os.path.exists(path):
        return
    stab = pd.read_csv(path).pivot(index='manuscript', columns='chapter', values='distance_to_global')
    plt.figure(figsize=(12, 6))
    sns.heatmap(stab, cmap="YlOrRd", annot=False, cbar_kws={'label': 'cosine distance to global profile'})
    plt.title(f"Figure 7: Chapter-level profile stability ({label_for(suffix)})")
    plt.tight_layout()
    plt.savefig(f'outputs/fig7_stability_heatmap_{suffix}.png', dpi=200)
    plt.close()


def main(suffix='B'):
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    os.makedirs('outputs', exist_ok=True)
    pkl = f"outputs/variants_full_with_vectors_{suffix}.pkl"
    if os.path.exists(pkl):
        df = pd.read_pickle(pkl)
        manuscripts = sorted(df['manuscript'].unique())
        palette = sns.color_palette("husl", len(manuscripts))
        ms_colors = {ms: palette[i] for i, ms in enumerate(manuscripts)}
        profiles = {ms: np.mean(np.array(df.loc[df['manuscript'] == ms, 'change_vector'].tolist()), axis=0)
                    for ms in manuscripts}
        plot_pca(df, ms_colors, suffix)
        plot_dendrogram(profiles, suffix)
    else:
        print(f"{pkl} not found: skipping the PCA and dendrogram figures.")
    plot_types(suffix)
    plot_cumulative(suffix)
    plot_stability(suffix)
    print(f"Visualizations written for {suffix}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None, help='Ablation suffix (matched, func_words, masked)')
    args = parser.parse_args()
    main(f"ablation_{args.ablation}" if args.ablation else args.baseline)
