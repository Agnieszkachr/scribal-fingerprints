window.DATA_ARTICLE = {
  "sbl": {
    "n": 4063,
    "per_witness": {
      "D": 1213,
      "aleph": 1034,
      "P66": 857,
      "A": 658,
      "B": 301
    },
    "association": {
      "Cramer's V Broad": {
        "v": 0.10548767553320675,
        "ci_low": 0.08948235488952191,
        "ci_high": 0.13005302735749513,
        "null_mean": 0.031356973236258474,
        "perm_p": 0.004975124378109453
      },
      "Cramer's V Sub": {
        "v": 0.10432727185158301,
        "ci_low": 0.07816428430507043,
        "ci_high": 0.145079956521613,
        "null_mean": 0.04244385648307088,
        "perm_p": 0.004975124378109453
      }
    },
    "shares": {
      "A": {
        "substitution_morphological": 0.2674772036474164,
        "substitution_lexical": 0.1899696048632219,
        "substitution_word_order": 0.09878419452887538,
        "addition": 0.2811550151975684,
        "omission": 0.16261398176291794
      },
      "B": {
        "substitution_morphological": 0.3588039867109635,
        "substitution_lexical": 0.12956810631229235,
        "substitution_word_order": 0.06312292358803986,
        "addition": 0.14285714285714285,
        "omission": 0.30564784053156147
      },
      "D": {
        "substitution_morphological": 0.20774938169826876,
        "substitution_lexical": 0.23907666941467437,
        "substitution_word_order": 0.07831821929101401,
        "addition": 0.2654575432811212,
        "omission": 0.20939818631492169
      },
      "P66": {
        "substitution_morphological": 0.2823803967327888,
        "substitution_lexical": 0.23803967327887982,
        "substitution_word_order": 0.073512252042007,
        "addition": 0.1750291715285881,
        "omission": 0.2310385064177363
      },
      "aleph": {
        "substitution_morphological": 0.2127659574468085,
        "substitution_lexical": 0.20889748549323017,
        "substitution_word_order": 0.086073500967118,
        "addition": 0.19439071566731142,
        "omission": 0.2978723404255319
      }
    }
  },
  "text_checks": {
    "lexical_kinds_anchor_B": {
      "D": {
        "lexical_unequal": {
          "percent_of_variants": 10.0,
          "deviation_pp": 2.7,
          "perm_p": 0.0045
        },
        "lexical_equal_length": {
          "percent_of_variants": 15.1,
          "deviation_pp": 1.4,
          "perm_p": 0.3148
        }
      },
      "aleph": {
        "lexical_unequal": {
          "percent_of_variants": 8.6,
          "deviation_pp": 0.6,
          "perm_p": 0.5792
        },
        "lexical_equal_length": {
          "percent_of_variants": 12.3,
          "deviation_pp": -2.5,
          "perm_p": 0.0405
        }
      },
      "A": {
        "lexical_unequal": {
          "percent_of_variants": 6.5,
          "deviation_pp": -2.1,
          "perm_p": 0.0615
        },
        "lexical_equal_length": {
          "percent_of_variants": 12.3,
          "deviation_pp": -2.3,
          "perm_p": 0.1379
        }
      },
      "P66": {
        "lexical_unequal": {
          "percent_of_variants": 6.6,
          "deviation_pp": -2.1,
          "perm_p": 0.03
        },
        "lexical_equal_length": {
          "percent_of_variants": 16.6,
          "deviation_pp": 3.2,
          "perm_p": 0.011
        }
      }
    },
    "shared_with_aleph_by_stretch": {
      "B": {
        "A": {
          "1:1-8:38": {
            "shared": 64,
            "variants": 237,
            "percent": 27.0
          },
          "8:39-21:25": {
            "shared": 152,
            "variants": 592,
            "percent": 25.7
          },
          "fisher_p": 0.7262941273418455
        },
        "D": {
          "1:1-8:38": {
            "shared": 116,
            "variants": 470,
            "percent": 24.7
          },
          "8:39-21:25": {
            "shared": 132,
            "variants": 875,
            "percent": 15.1
          },
          "fisher_p": 2.4307115294043484e-05
        },
        "P66": {
          "1:1-8:38": {
            "shared": 97,
            "variants": 367,
            "percent": 26.4
          },
          "8:39-21:25": {
            "shared": 116,
            "variants": 625,
            "percent": 18.6
          },
          "fisher_p": 0.0039533568432678825
        }
      },
      "A": {
        "B": {
          "1:1-8:38": {
            "shared": 99,
            "variants": 237,
            "percent": 41.8
          },
          "8:39-21:25": {
            "shared": 262,
            "variants": 591,
            "percent": 44.3
          },
          "fisher_p": 0.5353645897921657
        },
        "D": {
          "1:1-8:38": {
            "shared": 77,
            "variants": 278,
            "percent": 27.7
          },
          "8:39-21:25": {
            "shared": 159,
            "variants": 834,
            "percent": 19.1
          },
          "fisher_p": 0.0029810772842558198
        },
        "P66": {
          "1:1-8:38": {
            "shared": 94,
            "variants": 290,
            "percent": 32.4
          },
          "8:39-21:25": {
            "shared": 195,
            "variants": 697,
            "percent": 28.0
          },
          "fisher_p": 0.1675686574688666
        }
      },
      "SBL": {
        "A": {
          "1:1-8:38": {
            "shared": 32,
            "variants": 184,
            "percent": 17.4
          },
          "8:39-21:25": {
            "shared": 72,
            "variants": 474,
            "percent": 15.2
          },
          "fisher_p": 0.47757700011735293
        },
        "B": {
          "1:1-8:38": {
            "shared": 12,
            "variants": 114,
            "percent": 10.5
          },
          "8:39-21:25": {
            "shared": 19,
            "variants": 187,
            "percent": 10.2
          },
          "fisher_p": 1.0
        },
        "D": {
          "1:1-8:38": {
            "shared": 76,
            "variants": 417,
            "percent": 18.2
          },
          "8:39-21:25": {
            "shared": 70,
            "variants": 796,
            "percent": 8.8
          },
          "fisher_p": 2.8903315829861294e-06
        },
        "P66": {
          "1:1-8:38": {
            "shared": 56,
            "variants": 308,
            "percent": 18.2
          },
          "8:39-21:25": {
            "shared": 60,
            "variants": 549,
            "percent": 10.9
          },
          "fisher_p": 0.003523014534766588
        }
      }
    }
  },
  "within_class": {
    "B": {
      "substitution_morphological": {
        "n": 1000,
        "d": 0.0118,
        "ci_low": -0.0061,
        "ci_high": 0.0199,
        "null_mean": 0.0009,
        "perm_p": 0.002
      },
      "substitution_lexical": {
        "n": 975,
        "d": 0.0048,
        "ci_low": -0.0128,
        "ci_high": 0.0176,
        "null_mean": 0.0019,
        "perm_p": 0.2109
      },
      "substitution_word_order": {
        "n": 338,
        "d": -0.0054,
        "ci_low": -0.0584,
        "ci_high": 0.0046,
        "null_mean": 0.0042,
        "perm_p": 0.8286
      },
      "addition": {
        "n": 1000,
        "d": 0.0051,
        "ci_low": -0.0175,
        "ci_high": 0.0138,
        "null_mean": 0.001,
        "perm_p": 0.1689
      },
      "omission": {
        "n": 924,
        "d": -0.0019,
        "ci_low": -0.0166,
        "ci_high": 0.0041,
        "null_mean": 0.0003,
        "perm_p": 0.6807
      }
    },
    "A": {
      "substitution_morphological": {
        "n": 918,
        "d": -0.0023,
        "ci_low": -0.0257,
        "ci_high": 0.0037,
        "null_mean": 0.0004,
        "perm_p": 0.7716
      },
      "substitution_lexical": {
        "n": 928,
        "d": 0.0009,
        "ci_low": -0.0232,
        "ci_high": 0.009,
        "null_mean": 0.0019,
        "perm_p": 0.6002
      },
      "substitution_word_order": {
        "n": 311,
        "d": -0.0411,
        "ci_low": -0.0933,
        "ci_high": -0.0449,
        "null_mean": 0.0015,
        "perm_p": 1.0
      },
      "addition": {
        "n": 794,
        "d": -0.0054,
        "ci_low": -0.0302,
        "ci_high": -0.0019,
        "null_mean": 0.0002,
        "perm_p": 0.8881
      },
      "omission": {
        "n": 1000,
        "d": -0.0028,
        "ci_low": -0.0221,
        "ci_high": 0.0029,
        "null_mean": 0.0012,
        "perm_p": 0.8736
      }
    },
    "aleph": {
      "substitution_morphological": {
        "n": 1000,
        "d": 0.0011,
        "ci_low": -0.0184,
        "ci_high": 0.0052,
        "null_mean": 0.0007,
        "perm_p": 0.4388
      },
      "substitution_lexical": {
        "n": 1000,
        "d": 0.0002,
        "ci_low": -0.0212,
        "ci_high": 0.009,
        "null_mean": 0.0009,
        "perm_p": 0.5637
      },
      "substitution_word_order": {
        "n": 364,
        "d": -0.014,
        "ci_low": -0.0749,
        "ci_high": -0.0111,
        "null_mean": 0.0035,
        "perm_p": 0.985
      },
      "addition": {
        "n": 1000,
        "d": -0.0065,
        "ci_low": -0.0256,
        "ci_high": -0.0019,
        "null_mean": 0.0011,
        "perm_p": 0.9905
      },
      "omission": {
        "n": 1000,
        "d": -0.0023,
        "ci_low": -0.0243,
        "ci_high": 0.0068,
        "null_mean": 0.0012,
        "perm_p": 0.8526
      }
    }
  },
  "typology_split_half": {
    "B": {
      "full": {
        "halves": {
          "odd": {
            "n": 2261,
            "v_broad": 0.07,
            "v_broad_ci": [
              0.057,
              0.109
            ],
            "v_broad_p": 0.005,
            "v_sub": 0.058,
            "v_sub_ci": [
              0.036,
              0.11
            ],
            "v_sub_p": 0.2239
          },
          "even": {
            "n": 2104,
            "v_broad": 0.088,
            "v_broad_ci": [
              0.074,
              0.114
            ],
            "v_broad_p": 0.005,
            "v_sub": 0.09,
            "v_sub_ci": [
              0.073,
              0.128
            ],
            "v_sub_p": 0.01
          }
        },
        "cross_half_tv": {
          "A_even": {
            "A_odd": 0.0449,
            "D_odd": 0.1103,
            "P66_odd": 0.1431,
            "aleph_odd": 0.1445
          },
          "D_even": {
            "A_odd": 0.0802,
            "D_odd": 0.0592,
            "P66_odd": 0.1307,
            "aleph_odd": 0.1511
          },
          "P66_even": {
            "A_odd": 0.0929,
            "D_odd": 0.0536,
            "P66_odd": 0.0465,
            "aleph_odd": 0.0718
          },
          "aleph_even": {
            "A_odd": 0.1129,
            "D_odd": 0.0699,
            "P66_odd": 0.0945,
            "aleph_odd": 0.0814
          }
        },
        "same_mean": 0.058,
        "cross_mean": 0.1046,
        "gap": 0.0466,
        "gap_null_mean": 0.0005,
        "gap_null_sd": 0.0054,
        "gap_p": 0.002,
        "nearest_self": 2,
        "n_witnesses": 4,
        "nearest_p": 0.1996,
        "profiles_percent": {
          "A": {
            "odd": {
              "substitution_morphological": 25.3,
              "substitution_lexical": 19.2,
              "substitution_word_order": 9.3,
              "addition": 28.7,
              "omission": 17.6
            },
            "even": {
              "substitution_morphological": 24.9,
              "substitution_lexical": 18.4,
              "substitution_word_order": 8.3,
              "addition": 33.2,
              "omission": 15.3
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 22.8,
              "substitution_lexical": 23.8,
              "substitution_word_order": 7.4,
              "addition": 25.1,
              "omission": 20.9
            },
            "even": {
              "substitution_morphological": 19.5,
              "substitution_lexical": 26.5,
              "substitution_word_order": 7.2,
              "addition": 28.4,
              "omission": 18.3
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 28.1,
              "substitution_lexical": 22.1,
              "substitution_word_order": 7.4,
              "addition": 19.7,
              "omission": 22.7
            },
            "even": {
              "substitution_morphological": 27.5,
              "substitution_lexical": 24.4,
              "substitution_word_order": 6.6,
              "addition": 22.0,
              "omission": 19.4
            }
          },
          "aleph": {
            "odd": {
              "substitution_morphological": 27.0,
              "substitution_lexical": 20.0,
              "substitution_word_order": 7.2,
              "addition": 19.8,
              "omission": 26.0
            },
            "even": {
              "substitution_morphological": 18.9,
              "substitution_lexical": 21.9,
              "substitution_word_order": 9.0,
              "addition": 24.0,
              "omission": 26.2
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "P66",
            "even": "P66"
          },
          "substitution_lexical": {
            "odd": "D",
            "even": "D"
          },
          "substitution_word_order": {
            "odd": "A",
            "even": "aleph"
          },
          "addition": {
            "odd": "A",
            "even": "A"
          },
          "omission": {
            "odd": "aleph",
            "even": "aleph"
          }
        }
      },
      "attested_loci": {
        "halves": {
          "odd": {
            "n": 1506,
            "v_broad": 0.065,
            "v_broad_ci": [
              0.052,
              0.127
            ],
            "v_broad_p": 0.0547,
            "v_sub": 0.087,
            "v_sub_ci": [
              0.065,
              0.139
            ],
            "v_sub_p": 0.0547
          },
          "even": {
            "n": 1403,
            "v_broad": 0.094,
            "v_broad_ci": [
              0.082,
              0.129
            ],
            "v_broad_p": 0.005,
            "v_sub": 0.07,
            "v_sub_ci": [
              0.059,
              0.124
            ],
            "v_sub_p": 0.2886
          }
        },
        "cross_half_tv": {
          "A_even": {
            "A_odd": 0.0847,
            "D_odd": 0.1137,
            "P66_odd": 0.1886,
            "aleph_odd": 0.182
          },
          "D_even": {
            "A_odd": 0.0887,
            "D_odd": 0.052,
            "P66_odd": 0.1348,
            "aleph_odd": 0.182
          },
          "P66_even": {
            "A_odd": 0.0735,
            "D_odd": 0.053,
            "P66_odd": 0.0668,
            "aleph_odd": 0.114
          },
          "aleph_even": {
            "A_odd": 0.1278,
            "D_odd": 0.0558,
            "P66_odd": 0.0951,
            "aleph_odd": 0.129
          }
        },
        "same_mean": 0.0831,
        "cross_mean": 0.1174,
        "gap": 0.0343,
        "gap_null_mean": 0.0003,
        "gap_null_sd": 0.0068,
        "gap_p": 0.002,
        "nearest_self": 2,
        "n_witnesses": 4,
        "nearest_p": 0.1836,
        "profiles_percent": {
          "A": {
            "odd": {
              "substitution_morphological": 28.2,
              "substitution_lexical": 18.9,
              "substitution_word_order": 7.3,
              "addition": 27.6,
              "omission": 17.9
            },
            "even": {
              "substitution_morphological": 23.4,
              "substitution_lexical": 17.5,
              "substitution_word_order": 7.7,
              "addition": 35.7,
              "omission": 15.7
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 22.9,
              "substitution_lexical": 24.3,
              "substitution_word_order": 6.9,
              "addition": 25.6,
              "omission": 20.3
            },
            "even": {
              "substitution_morphological": 19.8,
              "substitution_lexical": 25.3,
              "substitution_word_order": 6.9,
              "addition": 29.7,
              "omission": 18.3
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 29.6,
              "substitution_lexical": 23.9,
              "substitution_word_order": 6.0,
              "addition": 18.5,
              "omission": 21.9
            },
            "even": {
              "substitution_morphological": 26.4,
              "substitution_lexical": 25.7,
              "substitution_word_order": 7.3,
              "addition": 22.1,
              "omission": 18.5
            }
          },
          "aleph": {
            "odd": {
              "substitution_morphological": 33.0,
              "substitution_lexical": 18.6,
              "substitution_word_order": 5.7,
              "addition": 19.5,
              "omission": 23.3
            },
            "even": {
              "substitution_morphological": 20.1,
              "substitution_lexical": 24.1,
              "substitution_word_order": 7.7,
              "addition": 22.9,
              "omission": 25.1
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "aleph",
            "even": "P66"
          },
          "substitution_lexical": {
            "odd": "D",
            "even": "P66"
          },
          "substitution_word_order": {
            "odd": "A",
            "even": "aleph"
          },
          "addition": {
            "odd": "A",
            "even": "A"
          },
          "omission": {
            "odd": "aleph",
            "even": "aleph"
          }
        }
      }
    },
    "A": {
      "full": {
        "halves": {
          "odd": {
            "n": 2175,
            "v_broad": 0.063,
            "v_broad_ci": [
              0.042,
              0.1
            ],
            "v_broad_p": 0.0199,
            "v_sub": 0.062,
            "v_sub_ci": [
              0.044,
              0.111
            ],
            "v_sub_p": 0.199
          },
          "even": {
            "n": 1911,
            "v_broad": 0.071,
            "v_broad_ci": [
              0.06,
              0.098
            ],
            "v_broad_p": 0.005,
            "v_sub": 0.079,
            "v_sub_ci": [
              0.063,
              0.126
            ],
            "v_sub_p": 0.0299
          }
        },
        "cross_half_tv": {
          "B_even": {
            "B_odd": 0.0443,
            "D_odd": 0.1606,
            "P66_odd": 0.0835,
            "aleph_odd": 0.0709
          },
          "D_even": {
            "B_odd": 0.1287,
            "D_odd": 0.023,
            "P66_odd": 0.075,
            "aleph_odd": 0.0875
          },
          "P66_even": {
            "B_odd": 0.0399,
            "D_odd": 0.1089,
            "P66_odd": 0.0389,
            "aleph_odd": 0.0325
          },
          "aleph_even": {
            "B_odd": 0.0797,
            "D_odd": 0.1071,
            "P66_odd": 0.0663,
            "aleph_odd": 0.0423
          }
        },
        "same_mean": 0.0371,
        "cross_mean": 0.0867,
        "gap": 0.0496,
        "gap_null_mean": -0.0003,
        "gap_null_sd": 0.0079,
        "gap_p": 0.002,
        "nearest_self": 2,
        "n_witnesses": 4,
        "nearest_p": 0.2375,
        "profiles_percent": {
          "B": {
            "odd": {
              "substitution_morphological": 25.3,
              "substitution_lexical": 19.0,
              "substitution_word_order": 9.3,
              "addition": 17.6,
              "omission": 28.7
            },
            "even": {
              "substitution_morphological": 24.9,
              "substitution_lexical": 17.6,
              "substitution_word_order": 8.3,
              "addition": 16.1,
              "omission": 33.2
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 21.5,
              "substitution_lexical": 25.0,
              "substitution_word_order": 6.5,
              "addition": 24.8,
              "omission": 22.2
            },
            "even": {
              "substitution_morphological": 20.3,
              "substitution_lexical": 25.8,
              "substitution_word_order": 6.8,
              "addition": 23.7,
              "omission": 23.3
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 23.4,
              "substitution_lexical": 25.0,
              "substitution_word_order": 7.6,
              "addition": 17.0,
              "omission": 27.0
            },
            "even": {
              "substitution_morphological": 24.4,
              "substitution_lexical": 21.8,
              "substitution_word_order": 6.9,
              "addition": 17.0,
              "omission": 29.9
            }
          },
          "aleph": {
            "odd": {
              "substitution_morphological": 22.7,
              "substitution_lexical": 22.3,
              "substitution_word_order": 8.2,
              "addition": 18.5,
              "omission": 28.4
            },
            "even": {
              "substitution_morphological": 19.0,
              "substitution_lexical": 22.7,
              "substitution_word_order": 7.6,
              "addition": 18.8,
              "omission": 31.8
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "B",
            "even": "B"
          },
          "substitution_lexical": {
            "odd": "P66",
            "even": "D"
          },
          "substitution_word_order": {
            "odd": "B",
            "even": "B"
          },
          "addition": {
            "odd": "D",
            "even": "D"
          },
          "omission": {
            "odd": "B",
            "even": "B"
          }
        }
      },
      "attested_loci": {
        "halves": {
          "odd": {
            "n": 1617,
            "v_broad": 0.065,
            "v_broad_ci": [
              0.042,
              0.121
            ],
            "v_broad_p": 0.0299,
            "v_sub": 0.076,
            "v_sub_ci": [
              0.052,
              0.132
            ],
            "v_sub_p": 0.0995
          },
          "even": {
            "n": 1484,
            "v_broad": 0.08,
            "v_broad_ci": [
              0.066,
              0.117
            ],
            "v_broad_p": 0.005,
            "v_sub": 0.074,
            "v_sub_ci": [
              0.059,
              0.121
            ],
            "v_sub_p": 0.209
          }
        },
        "cross_half_tv": {
          "B_even": {
            "B_odd": 0.0834,
            "D_odd": 0.1587,
            "P66_odd": 0.1101,
            "aleph_odd": 0.0941
          },
          "D_even": {
            "B_odd": 0.1258,
            "D_odd": 0.0316,
            "P66_odd": 0.0751,
            "aleph_odd": 0.1073
          },
          "P66_even": {
            "B_odd": 0.0613,
            "D_odd": 0.0944,
            "P66_odd": 0.0425,
            "aleph_odd": 0.0469
          },
          "aleph_even": {
            "B_odd": 0.0933,
            "D_odd": 0.1135,
            "P66_odd": 0.0848,
            "aleph_odd": 0.0814
          }
        },
        "same_mean": 0.0597,
        "cross_mean": 0.0971,
        "gap": 0.0374,
        "gap_null_mean": -0.0001,
        "gap_null_sd": 0.0077,
        "gap_p": 0.002,
        "nearest_self": 2,
        "n_witnesses": 4,
        "nearest_p": 0.1996,
        "profiles_percent": {
          "B": {
            "odd": {
              "substitution_morphological": 28.3,
              "substitution_lexical": 19.0,
              "substitution_word_order": 7.3,
              "addition": 18.0,
              "omission": 27.3
            },
            "even": {
              "substitution_morphological": 23.4,
              "substitution_lexical": 17.1,
              "substitution_word_order": 7.7,
              "addition": 16.4,
              "omission": 35.3
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 22.0,
              "substitution_lexical": 24.4,
              "substitution_word_order": 6.2,
              "addition": 25.0,
              "omission": 22.4
            },
            "even": {
              "substitution_morphological": 20.1,
              "substitution_lexical": 25.8,
              "substitution_word_order": 6.8,
              "addition": 23.7,
              "omission": 23.5
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 23.8,
              "substitution_lexical": 27.3,
              "substitution_word_order": 6.0,
              "addition": 17.0,
              "omission": 26.0
            },
            "even": {
              "substitution_morphological": 24.3,
              "substitution_lexical": 23.2,
              "substitution_word_order": 6.4,
              "addition": 16.8,
              "omission": 29.3
            }
          },
          "aleph": {
            "odd": {
              "substitution_morphological": 27.6,
              "substitution_lexical": 21.3,
              "substitution_word_order": 7.1,
              "addition": 17.6,
              "omission": 26.5
            },
            "even": {
              "substitution_morphological": 19.4,
              "substitution_lexical": 23.1,
              "substitution_word_order": 7.6,
              "addition": 17.6,
              "omission": 32.3
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "B",
            "even": "P66"
          },
          "substitution_lexical": {
            "odd": "P66",
            "even": "D"
          },
          "substitution_word_order": {
            "odd": "B",
            "even": "B"
          },
          "addition": {
            "odd": "D",
            "even": "D"
          },
          "omission": {
            "odd": "B",
            "even": "B"
          }
        }
      }
    },
    "aleph": {
      "full": {
        "halves": {
          "odd": {
            "n": 2635,
            "v_broad": 0.04,
            "v_broad_ci": [
              0.031,
              0.076
            ],
            "v_broad_p": 0.1592,
            "v_sub": 0.059,
            "v_sub_ci": [
              0.045,
              0.102
            ],
            "v_sub_p": 0.204
          },
          "even": {
            "n": 2541,
            "v_broad": 0.054,
            "v_broad_ci": [
              0.04,
              0.083
            ],
            "v_broad_p": 0.0597,
            "v_sub": 0.062,
            "v_sub_ci": [
              0.039,
              0.121
            ],
            "v_sub_p": 0.1741
          }
        },
        "cross_half_tv": {
          "A_even": {
            "A_odd": 0.0449,
            "B_odd": 0.0823,
            "D_odd": 0.0478,
            "P66_odd": 0.1002
          },
          "B_even": {
            "A_odd": 0.0758,
            "B_odd": 0.08,
            "D_odd": 0.0782,
            "P66_odd": 0.0809
          },
          "D_even": {
            "A_odd": 0.0563,
            "B_odd": 0.0974,
            "D_odd": 0.0358,
            "P66_odd": 0.077
          },
          "P66_even": {
            "A_odd": 0.0646,
            "B_odd": 0.0636,
            "D_odd": 0.0503,
            "P66_odd": 0.0426
          }
        },
        "same_mean": 0.0508,
        "cross_mean": 0.0729,
        "gap": 0.022,
        "gap_null_mean": 0.0002,
        "gap_null_sd": 0.0057,
        "gap_p": 0.002,
        "nearest_self": 3,
        "n_witnesses": 4,
        "nearest_p": 0.02,
        "profiles_percent": {
          "A": {
            "odd": {
              "substitution_morphological": 22.6,
              "substitution_lexical": 22.6,
              "substitution_word_order": 8.2,
              "addition": 28.4,
              "omission": 18.2
            },
            "even": {
              "substitution_morphological": 19.1,
              "substitution_lexical": 21.9,
              "substitution_word_order": 7.8,
              "addition": 31.3,
              "omission": 19.8
            }
          },
          "B": {
            "odd": {
              "substitution_morphological": 27.0,
              "substitution_lexical": 19.8,
              "substitution_word_order": 7.3,
              "addition": 25.7,
              "omission": 20.2
            },
            "even": {
              "substitution_morphological": 19.0,
              "substitution_lexical": 21.2,
              "substitution_word_order": 9.0,
              "addition": 25.8,
              "omission": 25.0
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 22.2,
              "substitution_lexical": 23.7,
              "substitution_word_order": 6.4,
              "addition": 28.0,
              "omission": 19.8
            },
            "even": {
              "substitution_morphological": 19.2,
              "substitution_lexical": 24.5,
              "substitution_word_order": 5.9,
              "addition": 30.8,
              "omission": 19.6
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 23.5,
              "substitution_lexical": 24.8,
              "substitution_word_order": 6.0,
              "addition": 23.1,
              "omission": 22.7
            },
            "even": {
              "substitution_morphological": 22.3,
              "substitution_lexical": 21.7,
              "substitution_word_order": 6.3,
              "addition": 25.0,
              "omission": 24.7
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "B",
            "even": "P66"
          },
          "substitution_lexical": {
            "odd": "P66",
            "even": "D"
          },
          "substitution_word_order": {
            "odd": "A",
            "even": "B"
          },
          "addition": {
            "odd": "A",
            "even": "A"
          },
          "omission": {
            "odd": "P66",
            "even": "B"
          }
        }
      },
      "attested_loci": {
        "halves": {
          "odd": {
            "n": 1715,
            "v_broad": 0.057,
            "v_broad_ci": [
              0.041,
              0.104
            ],
            "v_broad_p": 0.0846,
            "v_sub": 0.09,
            "v_sub_ci": [
              0.06,
              0.136
            ],
            "v_sub_p": 0.0199
          },
          "even": {
            "n": 1607,
            "v_broad": 0.052,
            "v_broad_ci": [
              0.04,
              0.097
            ],
            "v_broad_p": 0.1741,
            "v_sub": 0.042,
            "v_sub_ci": [
              0.033,
              0.12
            ],
            "v_sub_p": 0.8408
          }
        },
        "cross_half_tv": {
          "A_even": {
            "A_odd": 0.0794,
            "B_odd": 0.152,
            "D_odd": 0.055,
            "P66_odd": 0.1402
          },
          "B_even": {
            "A_odd": 0.0875,
            "B_odd": 0.1283,
            "D_odd": 0.0628,
            "P66_odd": 0.0757
          },
          "D_even": {
            "A_odd": 0.0808,
            "B_odd": 0.1275,
            "D_odd": 0.0306,
            "P66_odd": 0.1049
          },
          "P66_even": {
            "A_odd": 0.0822,
            "B_odd": 0.1093,
            "D_odd": 0.0405,
            "P66_odd": 0.0491
          }
        },
        "same_mean": 0.0719,
        "cross_mean": 0.0932,
        "gap": 0.0213,
        "gap_null_mean": 0.0007,
        "gap_null_sd": 0.007,
        "gap_p": 0.002,
        "nearest_self": 3,
        "n_witnesses": 4,
        "nearest_p": 0.02,
        "profiles_percent": {
          "A": {
            "odd": {
              "substitution_morphological": 27.4,
              "substitution_lexical": 21.7,
              "substitution_word_order": 7.0,
              "addition": 26.4,
              "omission": 17.5
            },
            "even": {
              "substitution_morphological": 19.5,
              "substitution_lexical": 22.9,
              "substitution_word_order": 7.6,
              "addition": 31.8,
              "omission": 18.2
            }
          },
          "B": {
            "odd": {
              "substitution_morphological": 33.0,
              "substitution_lexical": 18.2,
              "substitution_word_order": 5.7,
              "addition": 23.3,
              "omission": 19.8
            },
            "even": {
              "substitution_morphological": 20.2,
              "substitution_lexical": 23.6,
              "substitution_word_order": 7.8,
              "addition": 24.8,
              "omission": 23.6
            }
          },
          "D": {
            "odd": {
              "substitution_morphological": 22.3,
              "substitution_lexical": 24.7,
              "substitution_word_order": 6.1,
              "addition": 27.9,
              "omission": 19.0
            },
            "even": {
              "substitution_morphological": 20.3,
              "substitution_lexical": 23.7,
              "substitution_word_order": 6.1,
              "addition": 29.8,
              "omission": 20.1
            }
          },
          "P66": {
            "odd": {
              "substitution_morphological": 25.5,
              "substitution_lexical": 25.9,
              "substitution_word_order": 5.2,
              "addition": 20.2,
              "omission": 23.2
            },
            "even": {
              "substitution_morphological": 22.3,
              "substitution_lexical": 24.3,
              "substitution_word_order": 5.5,
              "addition": 24.9,
              "omission": 23.0
            }
          }
        },
        "largest_share": {
          "substitution_morphological": {
            "odd": "B",
            "even": "P66"
          },
          "substitution_lexical": {
            "odd": "P66",
            "even": "P66"
          },
          "substitution_word_order": {
            "odd": "A",
            "even": "B"
          },
          "addition": {
            "odd": "D",
            "even": "A"
          },
          "omission": {
            "odd": "P66",
            "even": "B"
          }
        }
      }
    }
  },
  "content_vs_random": {
    "content_masked_d": 0.0058,
    "random_masked_mean_d": 0.0016,
    "difference": 0.0042,
    "boot_ci_low": -0.0055,
    "boot_ci_high": 0.0152,
    "boot_share_le_0": 0.23,
    "n_boot": 2000,
    "sample_per_replicate": 1000
  },
  "split_half": {
    "B": {
      "pairs": [
        {
          "pair": "A-D",
          "odd": 0.840827,
          "even": 0.827007
        },
        {
          "pair": "A-P66",
          "odd": 0.998735,
          "even": 0.673241
        },
        {
          "pair": "A-aleph",
          "odd": 0.898051,
          "even": 0.667543
        },
        {
          "pair": "D-P66",
          "odd": 0.611181,
          "even": 0.580743
        },
        {
          "pair": "D-aleph",
          "odd": 0.678887,
          "even": 0.7077
        },
        {
          "pair": "P66-aleph",
          "odd": 0.535162,
          "even": 0.629306
        }
      ],
      "matrix": {
        "labels": [
          "A_odd",
          "D_odd",
          "P66_odd",
          "aleph_odd",
          "A_even",
          "D_even",
          "P66_even",
          "aleph_even"
        ],
        "rows": [
          [
            0.0,
            0.840827,
            0.998735,
            0.898051,
            0.735222,
            0.896402,
            1.08017,
            0.794132
          ],
          [
            0.840827,
            0.0,
            0.611181,
            0.678887,
            1.066315,
            0.618344,
            0.742903,
            0.926855
          ],
          [
            0.998735,
            0.611181,
            0.0,
            0.535162,
            0.98718,
            0.719251,
            0.456956,
            0.704765
          ],
          [
            0.898051,
            0.678887,
            0.535162,
            0.0,
            1.013337,
            0.809603,
            0.663536,
            0.744351
          ],
          [
            0.735222,
            1.066315,
            0.98718,
            1.013337,
            0.0,
            0.827007,
            0.673241,
            0.667543
          ],
          [
            0.896402,
            0.618344,
            0.719251,
            0.809603,
            0.827007,
            0.0,
            0.580743,
            0.7077
          ],
          [
            1.08017,
            0.742903,
            0.456956,
            0.663536,
            0.673241,
            0.580743,
            0.0,
            0.629307
          ],
          [
            0.794132,
            0.926855,
            0.704765,
            0.744351,
            0.667543,
            0.7077,
            0.629307,
            0.0
          ]
        ]
      }
    },
    "A": {
      "pairs": [
        {
          "pair": "B-D",
          "odd": 0.641519,
          "even": 0.454302
        },
        {
          "pair": "B-P66",
          "odd": 0.521079,
          "even": 0.611037
        },
        {
          "pair": "B-aleph",
          "odd": 0.486616,
          "even": 0.503702
        },
        {
          "pair": "D-P66",
          "odd": 0.590511,
          "even": 0.417892
        },
        {
          "pair": "D-aleph",
          "odd": 0.620032,
          "even": 0.568701
        },
        {
          "pair": "P66-aleph",
          "odd": 0.34943,
          "even": 0.518469
        }
      ],
      "matrix": {
        "labels": [
          "B_odd",
          "D_odd",
          "P66_odd",
          "aleph_odd",
          "B_even",
          "D_even",
          "P66_even",
          "aleph_even"
        ],
        "rows": [
          [
            0.0,
            0.641519,
            0.521079,
            0.486616,
            0.712826,
            0.827493,
            0.747772,
            0.875598
          ],
          [
            0.641519,
            0.0,
            0.590511,
            0.620032,
            0.773623,
            0.647919,
            0.640092,
            0.874021
          ],
          [
            0.521079,
            0.590511,
            0.0,
            0.34943,
            0.800999,
            0.681599,
            0.405492,
            0.655011
          ],
          [
            0.486616,
            0.620032,
            0.34943,
            0.0,
            0.797027,
            0.672481,
            0.478208,
            0.663146
          ],
          [
            0.712826,
            0.773623,
            0.800999,
            0.797027,
            0.0,
            0.454302,
            0.611037,
            0.503702
          ],
          [
            0.827493,
            0.647919,
            0.681599,
            0.672481,
            0.454302,
            0.0,
            0.417892,
            0.568701
          ],
          [
            0.747772,
            0.640092,
            0.405492,
            0.478208,
            0.611037,
            0.417892,
            0.0,
            0.518469
          ],
          [
            0.875598,
            0.874021,
            0.655011,
            0.663146,
            0.503702,
            0.568701,
            0.518469,
            0.0
          ]
        ]
      }
    },
    "ℵ": {
      "pairs": [
        {
          "pair": "A-B",
          "odd": 0.39532,
          "even": 0.468605
        },
        {
          "pair": "A-D",
          "odd": 0.512791,
          "even": 0.727139
        },
        {
          "pair": "A-P66",
          "odd": 0.917966,
          "even": 0.709954
        },
        {
          "pair": "B-D",
          "odd": 0.550276,
          "even": 0.604866
        },
        {
          "pair": "B-P66",
          "odd": 0.776213,
          "even": 0.685199
        },
        {
          "pair": "D-P66",
          "odd": 0.704842,
          "even": 0.625404
        }
      ],
      "matrix": {
        "labels": [
          "A_odd",
          "B_odd",
          "D_odd",
          "P66_odd",
          "A_even",
          "B_even",
          "D_even",
          "P66_even"
        ],
        "rows": [
          [
            0.0,
            0.39532,
            0.512791,
            0.917966,
            0.683026,
            0.856218,
            1.019621,
            1.279141
          ],
          [
            0.39532,
            0.0,
            0.550276,
            0.776213,
            0.763482,
            0.757076,
            0.95928,
            1.149403
          ],
          [
            0.512791,
            0.550276,
            0.0,
            0.704842,
            0.864513,
            0.872507,
            0.798144,
            1.058094
          ],
          [
            0.917966,
            0.776213,
            0.704842,
            0.0,
            1.0703,
            1.097033,
            1.061464,
            0.831272
          ],
          [
            0.683026,
            0.763482,
            0.864513,
            1.0703,
            0.0,
            0.468605,
            0.727139,
            0.709954
          ],
          [
            0.856218,
            0.757076,
            0.872507,
            1.097033,
            0.468605,
            0.0,
            0.604866,
            0.685199
          ],
          [
            1.019621,
            0.95928,
            0.798144,
            1.061464,
            0.727139,
            0.604866,
            0.0,
            0.625404
          ],
          [
            1.279141,
            1.149403,
            1.058094,
            0.831272,
            0.709954,
            0.685199,
            0.625404,
            0.0
          ]
        ]
      }
    }
  }
};
