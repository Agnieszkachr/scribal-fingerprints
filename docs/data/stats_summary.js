window.DATA_STATS = {
  "configs": {
    "Baseline B": {
      "ARI": 0.048729801339460414,
      "Cohen's d": 0.11856184609798205,
      "Cohen's d_CI_Low": 0.08271642885117321,
      "Cohen's d_CI_High": 0.14992737773595993,
      "Cramer's V Broad": 0.09035427150308482,
      "Cramer's V Broad_CI_Low": 0.07046477415268615,
      "Cramer's V Broad_CI_High": 0.10875892003344984,
      "Cramer's V Sub": 0.07431367918477866,
      "Cramer's V Sub_CI_Low": 0.05086953451611871,
      "Cramer's V Sub_CI_High": 0.11170466878537373,
      "Odd_Even_Split_Rho_Full": 0.8285714285714287,
      "Odd_Even_Split_Rho_AttestLoci": 0.942857142857143,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 12460,
      "N_current": 4460,
      "stale": true
    },
    "Baseline A": {
      "ARI": 0.04643685357834051,
      "Cohen's d": 0.12709994614124298,
      "Cohen's d_CI_Low": 0.09381260722875595,
      "Cohen's d_CI_High": 0.15476566553115845,
      "Cramer's V Broad": 0.07536596167150644,
      "Cramer's V Broad_CI_Low": 0.057036962513831994,
      "Cramer's V Broad_CI_High": 0.0928194989488817,
      "Cramer's V Sub": 0.07012048399376061,
      "Cramer's V Sub_CI_Low": 0.04430982584160687,
      "Cramer's V Sub_CI_High": 0.1073373444587309,
      "Odd_Even_Split_Rho": 1.0,
      "N": 10481,
      "N_current": 4199,
      "stale": true
    },
    "Baseline aleph": {
      "Cramer's V Broad": 0.0539860024348997,
      "Cramer's V Broad_CI_Low": 0.039302653105993034,
      "Cramer's V Broad_CI_High": 0.07455755895785346,
      "Cramer's V Sub": 0.06423823904370562,
      "Cramer's V Sub_CI_Low": 0.04275977708981715,
      "Cramer's V Sub_CI_High": 0.09351588385714862,
      "N": null,
      "N_current": 5270,
      "stale": false
    },
    "Verse-matched": {
      "ARI": 0.04905749545302646,
      "Cohen's d": 0.1367265284061432,
      "Cohen's d_CI_Low": 0.11159644275903702,
      "Cohen's d_CI_High": 0.17542226612567902,
      "Cramer's V Broad": 0.09939168256262204,
      "Cramer's V Broad_CI_Low": 0.0767402465966511,
      "Cramer's V Broad_CI_High": 0.12290987522721884,
      "Cramer's V Sub": 0.0915559028132277,
      "Cramer's V Sub_CI_Low": 0.0634612914442828,
      "Cramer's V Sub_CI_High": 0.16345432776906282,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 8381,
      "N_current": 2994,
      "stale": true
    },
    "Function words only": {
      "ARI": 0.017047672750098674,
      "Cohen's d": 0.0865753731277394,
      "Cohen's d_CI_Low": 0.06599158831911855,
      "Cohen's d_CI_High": 0.11008519020354626,
      "Cramer's V Broad": 0.11144917313340655,
      "Cramer's V Broad_CI_Low": 0.08406848057679257,
      "Cramer's V Broad_CI_High": 0.14518863015497085,
      "Cramer's V Sub": 0.10120572219263428,
      "Cramer's V Sub_CI_Low": 0.050932539660302895,
      "Cramer's V Sub_CI_High": 0.15122225341085743,
      "Odd_Even_Split_Rho_Full": 0.4285714285714286,
      "Odd_Even_Split_Rho_AttestLoci": 0.2,
      "Odd_Even_Split_Rho": 0.2,
      "N": 1008,
      "N_current": 1779,
      "stale": true
    },
    "Content masked": {
      "ARI": 0.004191363937349921,
      "Cohen's d": 0.030587706491428602,
      "Cohen's d_CI_Low": 0.016185679585974142,
      "Cohen's d_CI_High": 0.05088109488085883,
      "Cramer's V Broad": 0.09035427150308482,
      "Cramer's V Broad_CI_Low": 0.07046477415268615,
      "Cramer's V Broad_CI_High": 0.10875892003344984,
      "Cramer's V Sub": 0.07431367918477866,
      "Cramer's V Sub_CI_Low": 0.05086953451611871,
      "Cramer's V Sub_CI_High": 0.11170466878537373,
      "Odd_Even_Split_Rho_Full": 1.0,
      "Odd_Even_Split_Rho_AttestLoci": 0.942857142857143,
      "Odd_Even_Split_Rho": 0.942857142857143,
      "N": 12460,
      "N_current": 4460,
      "stale": true
    },
    "Random masked (control)": {
      "error": "data not found"
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
    },
    {
      "label": "Random masked (control)",
      "cohens_d": 0.0,
      "ari": 0.0,
      "d_pct_drop": 100.0,
      "ari_pct_drop": 100.0,
      "stale": false
    }
  ]
};
