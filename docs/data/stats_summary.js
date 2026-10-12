window.DATA_STATS = {
  "configs": {
    "Baseline B": {
      "ARI": 0.048729801339460414,
      "Cohen's d": 0.11856184609798205,
      "Cohen's d_CI_Low": 0.08271642885117321,
      "Cohen's d_CI_High": 0.14992737773595993,
      "Cramer's V Broad": 0.08206280353590042,
      "Cramer's V Broad_CI_Low": 0.06442740518176708,
      "Cramer's V Broad_CI_High": 0.10433895696501148,
      "Cramer's V Sub": 0.094023017461839,
      "Cramer's V Sub_CI_Low": 0.07002019741631495,
      "Cramer's V Sub_CI_High": 0.11835833179322403,
      "Odd_Even_Split_Rho_Full": 0.8285714285714287,
      "Odd_Even_Split_Rho_AttestLoci": 0.942857142857143,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 12460,
      "N_current": 4250,
      "stale": true
    },
    "Baseline A": {
      "ARI": 0.04643685357834051,
      "Cohen's d": 0.12709994614124298,
      "Cohen's d_CI_Low": 0.09381260722875595,
      "Cohen's d_CI_High": 0.15476566553115845,
      "Cramer's V Broad": 0.07705045778271716,
      "Cramer's V Broad_CI_Low": 0.05775769254517961,
      "Cramer's V Broad_CI_High": 0.100769495926196,
      "Cramer's V Sub": 0.08963080427271466,
      "Cramer's V Sub_CI_Low": 0.05908549387522954,
      "Cramer's V Sub_CI_High": 0.1198627606795483,
      "Odd_Even_Split_Rho": 1.0,
      "N": 10481,
      "N_current": 3942,
      "stale": true
    },
    "Verse-matched": {
      "ARI": 0.04905749545302646,
      "Cohen's d": 0.1367265284061432,
      "Cohen's d_CI_Low": 0.11159644275903702,
      "Cohen's d_CI_High": 0.17542226612567902,
      "Cramer's V Broad": 0.08626219001698932,
      "Cramer's V Broad_CI_Low": 0.0653249003291971,
      "Cramer's V Broad_CI_High": 0.11278838682587222,
      "Cramer's V Sub": 0.09315407596611269,
      "Cramer's V Sub_CI_Low": 0.06720047534934062,
      "Cramer's V Sub_CI_High": 0.11806152392277328,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 8381,
      "N_current": 2840,
      "stale": true
    },
    "Function words only": {
      "ARI": 0.017047672750098674,
      "Cohen's d": 0.0865753731277394,
      "Cohen's d_CI_Low": 0.06599158831911855,
      "Cohen's d_CI_High": 0.11008519020354626,
      "Cramer's V Broad": 0.10713398940243664,
      "Cramer's V Broad_CI_Low": 0.08138602062507376,
      "Cramer's V Broad_CI_High": 0.14011668535763608,
      "Cramer's V Sub": 0.12021626723757221,
      "Cramer's V Sub_CI_Low": 0.06497682865396742,
      "Cramer's V Sub_CI_High": 0.16982798350044848,
      "Odd_Even_Split_Rho_Full": 0.4285714285714286,
      "Odd_Even_Split_Rho_AttestLoci": 0.2,
      "Odd_Even_Split_Rho": 0.2,
      "N": 1008,
      "N_current": 1744,
      "stale": true
    },
    "Content masked": {
      "ARI": 0.004191363937349921,
      "Cohen's d": 0.030587706491428602,
      "Cohen's d_CI_Low": 0.016185679585974142,
      "Cohen's d_CI_High": 0.05088109488085883,
      "Cramer's V Broad": 0.08206280353590042,
      "Cramer's V Broad_CI_Low": 0.06442740518176708,
      "Cramer's V Broad_CI_High": 0.10433895696501148,
      "Cramer's V Sub": 0.094023017461839,
      "Cramer's V Sub_CI_Low": 0.07002019741631495,
      "Cramer's V Sub_CI_High": 0.11835833179322403,
      "Odd_Even_Split_Rho_Full": 1.0,
      "Odd_Even_Split_Rho_AttestLoci": 0.942857142857143,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 12460,
      "N_current": 4250,
      "stale": true
    }
  },
  "ablation_panel": [
    {
      "label": "Baseline B",
      "cohens_d": 0.1186,
      "ari": 0.0487,
      "d_pct_drop": 0.0,
      "ari_pct_drop": 0.0,
      "stale": true
    },
    {
      "label": "Verse-matched",
      "cohens_d": 0.1367,
      "ari": 0.0491,
      "d_pct_drop": -15.3,
      "ari_pct_drop": -0.7,
      "stale": true
    },
    {
      "label": "Function words only",
      "cohens_d": 0.0866,
      "ari": 0.017,
      "d_pct_drop": 27.0,
      "ari_pct_drop": 65.0,
      "stale": true
    },
    {
      "label": "Content masked",
      "cohens_d": 0.0306,
      "ari": 0.0042,
      "d_pct_drop": 74.2,
      "ari_pct_drop": 91.4,
      "stale": true
    }
  ]
};
