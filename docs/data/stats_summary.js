window.DATA_STATS = {
  "configs": {
    "Baseline B": {
      "ARI": 0.048729801339460414,
      "Cohen's d": 0.11856184609798205,
      "Cohen's d_CI_Low": 0.08271642885117321,
      "Cohen's d_CI_High": 0.14992737773595993,
      "Cramer's V Broad": 0.08629334364682827,
      "Cramer's V Broad_CI_Low": 0.07299076805980213,
      "Cramer's V Broad_CI_High": 0.10076885671368736,
      "Cramer's V Sub": 0.09451843299385604,
      "Cramer's V Sub_CI_Low": 0.06945871261040273,
      "Cramer's V Sub_CI_High": 0.12216385961582567,
      "Odd_Even_Split_Rho": 0.8285714285714287
    },
    "Baseline A": {
      "ARI": 0.04643685357834051,
      "Cohen's d": 0.12709994614124298,
      "Cohen's d_CI_Low": 0.09381260722875595,
      "Cohen's d_CI_High": 0.15476566553115845,
      "Cramer's V Broad": 0.09975988806550525,
      "Cramer's V Broad_CI_Low": 0.08767494938725034,
      "Cramer's V Broad_CI_High": 0.1119386334864782,
      "Cramer's V Sub": 0.09479466360199418,
      "Cramer's V Sub_CI_Low": 0.07459192218462336,
      "Cramer's V Sub_CI_High": 0.1157818936543421,
      "Odd_Even_Split_Rho": 1.0
    },
    "Verse-matched": {
      "ARI": 0.04905749545302646,
      "Cohen's d": 0.1367265284061432,
      "Cohen's d_CI_Low": 0.11159644275903702,
      "Cohen's d_CI_High": 0.17542226612567902,
      "Cramer's V Broad": 0.09255283735553793,
      "Cramer's V Broad_CI_Low": 0.07476213577551968,
      "Cramer's V Broad_CI_High": 0.11158562956838118,
      "Cramer's V Sub": 0.108697998626435,
      "Cramer's V Sub_CI_Low": 0.08963520798203052,
      "Cramer's V Sub_CI_High": 0.12949603137202265,
      "Odd_Even_Split_Rho": 0.942857142857143
    },
    "Function words only": {
      "ARI": 0.0170476727500986,
      "Cohen's d": 0.0904592871665954,
      "Cohen's d_CI_Low": 0.0661037117242813,
      "Cohen's d_CI_High": 0.1267489343881607,
      "Cramer's V Broad": 0.0879505141265415,
      "Cramer's V Broad_CI_Low": 0.0604673854950461,
      "Cramer's V Broad_CI_High": 0.1200013045830087,
      "Cramer's V Sub": 0.219992288968445,
      "Cramer's V Sub_CI_Low": 0.096939323315723,
      "Cramer's V Sub_CI_High": 0.3764190003440602,
      "Odd_Even_Split_Rho": 0.4285714285714286
    },
    "Content masked": {
      "ARI": 0.0041913639373499,
      "Cohen's d": 0.0321929417550563,
      "Cohen's d_CI_Low": 0.0163033977150917,
      "Cohen's d_CI_High": 0.0527620427310466,
      "Cramer's V Broad": 0.0859611188259523,
      "Cramer's V Broad_CI_Low": 0.0718682198404851,
      "Cramer's V Broad_CI_High": 0.1023880283092666,
      "Cramer's V Sub": 0.0952502590883586,
      "Cramer's V Sub_CI_Low": 0.0710040796007906,
      "Cramer's V Sub_CI_High": 0.1172865210972826,
      "Odd_Even_Split_Rho": 1.0
    }
  },
  "ablation_panel": [
    {
      "label": "Baseline B",
      "cohens_d": 0.1186,
      "ari": 0.0487,
      "d_pct_drop": 0.0,
      "ari_pct_drop": 0.0
    },
    {
      "label": "Verse-matched",
      "cohens_d": 0.1367,
      "ari": 0.0491,
      "d_pct_drop": -15.3,
      "ari_pct_drop": -0.7
    },
    {
      "label": "Function words only",
      "cohens_d": 0.0905,
      "ari": 0.017,
      "d_pct_drop": 23.7,
      "ari_pct_drop": 65.0
    },
    {
      "label": "Content masked",
      "cohens_d": 0.0322,
      "ari": 0.0042,
      "d_pct_drop": 72.8,
      "ari_pct_drop": 91.4
    }
  ]
};
