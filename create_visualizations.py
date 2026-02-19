import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist, squareform
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
import os
import argparse

def load_data(base_ms='B'):
    df = pd.read_pickle(f"outputs/variants_full_with_vectors_{base_ms}.pkl")
    profiles = {}
    for ms in df['manuscript'].unique():
        ms_df = df[df['manuscript'] == ms]
        if not ms_df.empty:
            profiles[ms] = np.mean(ms_df['change_vector'].tolist(), axis=0)
    return df, profiles

def confidence_ellipse(x, y, ax, n_std=2.0, facecolor='none', **kwargs):
    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2, facecolor=facecolor, **kwargs)
    scale_x, scale_y = np.sqrt(cov[0, 0]) * n_std, np.sqrt(cov[1, 1]) * n_std
    mean_x, mean_y = np.mean(x), np.mean(y)
    transf = transforms.Affine2D().rotate_deg(45).scale(scale_x, scale_y).translate(mean_x, mean_y)
    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)

def main(base_ms='B'):
    if not os.path.exists(f"outputs/variants_full_with_vectors_{base_ms}.pkl"):
        print(f"File outputs/variants_full_with_vectors_{base_ms}.pkl not found.")
        return
        
    df, profiles_npz = load_data(base_ms)
    manuscripts = sorted(df['manuscript'].unique())
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    palette = sns.color_palette("husl", len(manuscripts))
    ms_colors = {ms: palette[i] for i, ms in enumerate(manuscripts)}
    
    # Fig 1: PCA with Ellipses
    all_vectors = np.array(list(df['change_vector']))
    pca = PCA(n_components=2, random_state=42)
    pca_res = pca.fit_transform(all_vectors)
    df['pca_x'], df['pca_y'] = pca_res[:, 0], pca_res[:, 1]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(x='pca_x', y='pca_y', hue='manuscript', data=df, alpha=0.3, s=20, ax=ax, palette=ms_colors)
    for ms in manuscripts:
        subset = df[df['manuscript'] == ms]
        if len(subset) > 5:
            confidence_ellipse(subset['pca_x'], subset['pca_y'], ax, n_std=2.0, edgecolor=ms_colors[ms], facecolor=ms_colors[ms], alpha=0.1)
    ax.set_title(f"Figure 1: PCA of Scribal Change Vectors against Baseline {base_ms}")
    plt.tight_layout()
    plt.savefig(f'outputs/fig1_pca_full_{base_ms}.png', dpi=300)
    plt.close()

    # Fig 2: Dendrogram
    ms_list = list(profiles_npz.keys())
    profile_matrix = np.array([profiles_npz[ms] for ms in ms_list])
    linkage_matrix = linkage(pdist(profile_matrix, metric='cosine'), method='ward')
    plt.figure(figsize=(10, 6))
    dendrogram(linkage_matrix, labels=ms_list)
    plt.title(f"Figure 2: Hierarchical Clustering of MS Profiles against Baseline {base_ms}")
    plt.savefig(f'outputs/fig2_dendrogram_full_{base_ms}.png', dpi=300)
    plt.close()

    # Fig 4: Variant Types Barplot
    counts_df = pd.read_csv(f"outputs/type_counts_full_{base_ms}.csv").set_index('manuscript')
    # Convert to proportions
    cols = ['substitution_morphological', 'substitution_lexical', 'substitution_word_order', 'addition', 'omission']
    for col in cols: counts_df[col] = counts_df[col] / counts_df['total_variants']
    counts_df[cols].plot(kind='bar', stacked=True, figsize=(10, 6))
    plt.title(f"Figure 4: Variant Type Distribution against Baseline {base_ms}")
    plt.savefig(f'outputs/fig4_types_full_{base_ms}.png', dpi=300)
    plt.close()

    # Fig 6: Cumulative Signal (IMPORTANT)
    cum_path = f"outputs/cumulative_analysis_{base_ms}.csv"
    if os.path.exists(cum_path):
        cum_df = pd.read_csv(cum_path)
        plt.figure(figsize=(10, 6))
        plt.plot(cum_df['chapters'], cum_df['ari'], marker='o', label='ARI (Clustering Signal)')
        plt.xlabel("Chapters (cumulative)")
        plt.ylabel("ARI Value")
        plt.title(f"Figure 6: Cumulative Signal Strength (Baseline {base_ms})")
        plt.grid(True)
        plt.savefig(f'outputs/fig6_cumulative_{base_ms}.png', dpi=300)
        plt.close()

    # Fig 7: Chapter Stability Heatmap
    stab_path = f"outputs/chapter_stability_{base_ms}.csv"
    if os.path.exists(stab_path):
        stab_df = pd.read_csv(stab_path)
        pivot_stab = stab_df.pivot(index='manuscript', columns='chapter', values='distance_to_global')
        plt.figure(figsize=(12, 6))
        sns.heatmap(pivot_stab, cmap="YlOrRd", annot=False)
        plt.title(f"Figure 7: Scribal Profile Stability (Distance to Global Profile - {base_ms})")
        plt.savefig(f'outputs/fig7_stability_heatmap_{base_ms}.png', dpi=300)
        plt.close()

    print(f"Full Gospel visualizations created for baseline {base_ms}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=str, default='B', help='Baseline MS')
    parser.add_argument('--ablation', type=str, default=None, help='Ablation suffix (func_words, masked, matched)')
    args = parser.parse_args()
    suffix = f"ablation_{args.ablation}" if args.ablation else args.baseline
    main(base_ms=suffix)
