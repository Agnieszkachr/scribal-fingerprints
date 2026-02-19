import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.spatial.distance import cosine
import os

from run_statistical_tests import load_data, odd_even_split_replicability

def update_report_and_csv(suffix, rho, pval):
    report_path = f"outputs/pilot_report_full_{suffix}.txt"
    csv_path = f"outputs/pilot_results_full_{suffix}.csv"
    
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            lines = f.readlines()
        with open(report_path, "w") as f:
            for line in lines:
                if line.startswith("Odd/Even Rank Correlation"):
                    f.write(f"Odd/Even Rank Correlation: Spearman rho = {rho:.4f} (p={pval:.4f})\n")
                else:
                    f.write(line)
                    
    if os.path.exists(csv_path):
        df_res = pd.read_csv(csv_path)
        if 'Odd_Even_Split_Rho' in df_res['Metric'].values:
            df_res.loc[df_res['Metric'] == 'Odd_Even_Split_Rho', 'Value'] = rho
        else:
            df_res.loc[len(df_res)] = ['Odd_Even_Split_Rho', rho, None, None]
        df_res.to_csv(csv_path, index=False)
        
def evaluate_all():
    suffixes = ['B', 'aleph', 'ablation_func_words', 'ablation_masked']
    for s in suffixes:
        base_ms = s if not s.startswith('ablation') else 'B'
        ablation = s.split('_', 1)[1] if s.startswith('ablation') else None
        try:
            df, _, _ = load_data(base_ms, ablation)
            rho, pval = odd_even_split_replicability(df)
            print(f"Fixed Odd/Even for {s}: rho={rho:.4f}, p={pval:.4f}")
            update_report_and_csv(s, rho, pval)
        except Exception as e:
            print(f"Failed for {s}: {e}")

if __name__ == "__main__":
    evaluate_all()
