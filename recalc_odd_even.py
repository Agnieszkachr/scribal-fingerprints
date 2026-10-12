"""Legacy utility: recompute the split-half (odd/even chapter) correlations
from the existing embedding pickles and patch the report files in place.
``run_statistical_tests.py`` writes the same values; use this only to refresh
the split-half lines without re-running the full inference."""
import os

import pandas as pd

from run_statistical_tests import load_data, odd_even_split_replicability

COMMON_VERSES = "data/common_extant_verses.txt"


def update_report_and_csv(suffix, rho, pval, rho_f, pval_f, n_common):
    report_path = f"outputs/pilot_report_full_{suffix}.txt"
    csv_path = f"outputs/pilot_results_full_{suffix}.csv"

    if os.path.exists(report_path):
        with open(report_path, encoding='utf-8') as f:
            lines = f.readlines()
        with open(report_path, "w", encoding='utf-8') as f:
            for line in lines:
                if line.startswith("Odd/Even Rank Correlation (full attested)"):
                    f.write(f"Odd/Even Rank Correlation (full attested): Spearman rho = {rho:.4f} (p={pval:.4f})\n")
                elif line.startswith("Odd/Even Rank Correlation (attested-loci"):
                    f.write(f"Odd/Even Rank Correlation (attested-loci filter, N_verses={n_common}): "
                            f"Spearman rho = {rho_f:.4f} (p={pval_f:.4f})\n")
                else:
                    f.write(line)

    if os.path.exists(csv_path):
        res = pd.read_csv(csv_path)
        for metric, value, p in (('Odd_Even_Split_Rho_Full', rho, pval),
                                 ('Odd_Even_Split_Rho_AttestLoci', rho_f, pval_f)):
            if metric in res['Metric'].values:
                res.loc[res['Metric'] == metric, 'Value'] = value
                if 'Perm_P' in res.columns:
                    res.loc[res['Metric'] == metric, 'Perm_P'] = p
            else:
                row = {c: None for c in res.columns}
                row.update({'Metric': metric, 'Value': value})
                if 'Perm_P' in res.columns:
                    row['Perm_P'] = p
                res.loc[len(res)] = row
        res.to_csv(csv_path, index=False)


def evaluate_all(suffixes=('B', 'A', 'aleph', 'ablation_matched', 'ablation_func_words', 'ablation_masked')):
    for s in suffixes:
        base_ms = 'B' if s.startswith('ablation') else s
        ablation = s.split('_', 1)[1] if s.startswith('ablation') else None
        try:
            df, _, _ = load_data(base_ms, ablation)
        except FileNotFoundError:
            print(f"Skipping {s}: embeddings not found")
            continue
        rho, pval, _ = odd_even_split_replicability(df)
        rho_f, pval_f, n_common = odd_even_split_replicability(df, common_verses_path=COMMON_VERSES)
        print(f"{s}: rho={rho:.4f} (p={pval:.4f}); attested-loci rho={rho_f:.4f} (p={pval_f:.4f})")
        update_report_and_csv(s, rho, pval, rho_f, pval_f, n_common)


if __name__ == "__main__":
    evaluate_all()
