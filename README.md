# Manuscript Textual Profile Analysis Engine

[Interactive Website](https://agnieszkachr.github.io/scribal-fingerprints/) · [GitHub Repository](https://github.com/Agnieszkachr/scribal-fingerprints)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23359316.svg)](https://doi.org/10.5281/zenodo.23359316)

This repository contains the codebase, extraction pipelines and analytical scripts for a
computational analysis of textual variation in five major Greek witnesses to the Gospel
of John (P66, Codex Sinaiticus, Codex Alexandrinus, Codex Vaticanus, Codex Bezae).
The project asks whether the witnesses possess statistically detectable, reproducible
**manuscript-level change profiles**, combining a classical typology of variants
(addition, omission, word order, morphological and lexical substitution) with contextual
embeddings of the variant loci (`Ancient-Greek-BERT`).

## Important Methodological Note

The profiles reflect the aggregate textual tradition of a witness and may be influenced by:

1. Text-type affiliation (Alexandrian, Western, Byzantine)
2. Exemplar tradition inherited by the copyist
3. Individual scribal habits and preferences

**The current methodology cannot disentangle these factors.** Profiles should be read as
manuscript-level characteristics, not as fingerprints of an individual scribe.

## Known Limitations

- **Text-type confound.** The five witnesses belong to different text-types, so part of
  any profile separation reflects text-type rather than scribal behaviour.
- **Lemmatisation.** Morphological and lexical substitutions are separated by a form-to-lemma
  lexicon derived from the printed text (MorphGNT SBLGNT). Witness spellings it does not
  contain fall back to character similarity, so corrupted forms, variant spellings of
  proper names and numerals written as letters can be mis-filed.
- **Embedding model.** `Ancient-Greek-BERT` was trained mostly on Classical Greek; its
  behaviour on unaccented Koine transcriptions has not been validated independently.
- **Dependence between observations.** Several variants can occur in one verse and their
  context windows overlap. Inference therefore uses chapter-level blocks (bootstrap and
  permutation), and the embedding report additionally gives a verse-level effect size.

## Key Results (variant typology, current extraction)

<p align="center">
  <img src="outputs/fig4_types_full_B.png" alt="Variant type distribution (Baseline B)" width="600">
</p>

Against Codex Vaticanus (B) as the baseline, 4,365 variants are extracted
(P66 992, ℵ 1,199, A 829, D 1,345). Additions and omissions together make up 42–48 % of
the variants of each witness, morphological substitutions 21–28 %, lexical substitutions
19–25 % and word-order shifts 7–9 %. The variant-type distributions differ significantly
between witnesses (`outputs/typology_report_B.txt`):

| Test (baseline B, N = 4,365) | Cramér's V [95 % block-bootstrap CI] | Permutation null (mean ± SD) | p |
|---|---|---|---|
| Substitution / addition / omission | 0.077 [0.066 – 0.099] | 0.025 ± 0.008 | 0.005 |
| Morphological / lexical / word order | 0.065 [0.049 – 0.096] | 0.035 ± 0.011 | 0.010 |

Alexandrinus has the largest share of additions and Sinaiticus the largest share of
omissions against B; Bezae has the largest share of lexical substitutions under all three
baselines, and P66 the largest share of morphological substitutions among the witnesses
other than Vaticanus (`outputs/type_counts_full_*.csv`, `outputs/typology_report_*.txt`).

### Embedding-based results

Against B, inter-manuscript distances between change vectors exceed intra-manuscript
distances by Cohen's d = 0.014 [0.004 – 0.026] (block permutation p < 0.001); the ARI of a
four-cluster partition is 0.002. Within single variant classes d lies between −0.005 and
0.012. Feature isolation: function words only 0.008, content masked 0.006, random masked
0.002 (mean of five draws). See `outputs/pilot_report_full_*.txt` and the website.

The embedding stage (`profile_scribes.py`) requires the BERT model; the vector files
(`outputs/*.pkl`) are not part of the repository.

## Repository Structure

```text
├── LICENSE                             # MIT License
├── README.md                           # This file
├── CITATION.cff                        # Citation metadata
├── requirements.txt                    # Python package dependencies
├── download_itsee_data.py              # Fetches the ITSEE TEI XML and runs the extraction for one baseline
├── src/
│   ├── extract_variants.py             # TEI parsing, alignment, classification (shared with the SCRIPTA pipeline)
│   ├── download_itsee_data.py          # ITSEE download and verse-id parsing
│   ├── config.py, corpus_registry.py   # Paths, witnesses, versification
│   └── utils/
│       ├── token_normalizer.py         # Surface forms and orthographic normalisation
│       └── nomina_sacra.py             # Expansion table for the attested nomina sacra
├── create_verse_matched_dataset.py     # Verse-matched subset: verses attested in all five witnesses
├── run_ablation_study.py               # Function-words-only, content-masked and random-masked (control) datasets
├── profile_scribes.py                  # Ancient-Greek-BERT embeddings, change vectors, manuscript and chapter profiles
├── run_statistical_tests.py            # Block bootstrap / permutation inference (Cramér's V, Cohen's d, ARI, split-half)
├── create_visualizations.py            # Figures (PCA, dendrogram, type distribution, cumulative ARI, stability heatmap)
├── data/
│   ├── raw/john/                       # Raw ITSEE transcriptions (one file per witness)
│   ├── variants_full_john_{B,A,aleph}.csv   # Variants against each baseline
│   ├── variants_ablation_{matched,func_words,masked,random_masked[_s1..s4]}.csv
│   └── common_extant_verses.txt        # 532 verses with attested text in all five witnesses
├── outputs/                            # Type counts, coverage report, statistical reports, figures
└── docs/                               # Static companion website (GitHub Pages)
```

## Methodological Details

### Transcription processing (`src/extract_variants.py`)

- Only the **first-hand text** is read: inside `<app>` the reading with `type="orig"` is
  used and corrector readings are ignored.
- Only the outermost `<w>` of a nested pair is read. Words split across line, column or
  page breaks (`<lb break="no"/>` inside `<w>`; `<w part="I">` + `<w part="F">` across
  `<ab>`) are joined; marginal sigla (`<seg type="margin">`), punctuation, running titles
  (`<fw>`) and notes are dropped.
- **Nomina sacra** (`<abbr type="nomSac">`) are expanded from a table of the attested
  abbreviations (θς → θεος, πρς → πατρος, ανος → ανθρωπος, ιης → ιησους, …); the
  supralinear stroke for final nu (`¯`) is resolved to ν.
- Tokens are lower-cased and stripped of diacritics (accents, breathings, diaeresis,
  iota subscript) and of every non-letter character. Tokens that contain editorially
  `<supplied>` text or a `<gap>` are flagged `reconstructed`, tokens containing
  `<unclear>` text are flagged `uncertain`; both count as attested by default.
  `--exclude-supplied` / `--exclude-unclear` drop the variant blocks that rest on such
  tokens (a robustness configuration; the counts dropped are printed).
- Verses with no attested text (lacunae; John 5:4; 7:53–8:11 where absent) are skipped;
  the coverage report counts only verses with text.

### Orthographic normalisation

Alignment is computed on normalised tokens so that the following alternations neither
break the alignment nor count as variants:

- itacism: ει/ι, η/ι, οι/υ/ι, αι/ε, and ω/ο (the digraph ου is protected);
- movable nu in the endings -σι(ν) and -ε(ν) (never in εν, μεν, ην, ουδεν, μηδεν, …) and
  movable sigma (ουτως/ουτω, αχρις/αχρι, μεχρις/μεχρι);
- elision (αλλ’/αλλα, δι’/δια, μετ’/μετα, …);
- consonant gemination (ιωανης/ιωαννης);
- final sigma and letter case.

The surface forms in the CSVs keep the transcribed spelling.

### Alignment and classification

Each manuscript verse is aligned with the baseline verse by `difflib.SequenceMatcher`
(longest common subsequence, `autojunk=False`). Every non-equal block becomes one variant:

- `insert` → **addition**; `delete` → **omission**;
- `replace` with the same multiset of words → **word-order shift**;
- `replace` otherwise → **substitution**, morphological if both sides have the same number
  of words and every positionally paired word is a form of the same lexeme, lexical
  otherwise (see *Morphological vs lexical substitution* below);
- after alignment, an omission and an addition (or two substitutions) of the same words
  within eight baseline tokens of each other are merged into one **word-order shift**,
  since the LCS alignment never emits a transposition as a single block.

### Morphological vs lexical substitution (`src/utils/lemma_lexicon.py`)

Two word forms are the same lexeme if they share a lemma in
`src/utils/data/morphgnt_form_lemmas.tsv`, a form-to-lemma list of every word form of the
MorphGNT SBLGNT (accents removed; 17,347 forms). Suppletive forms (ειπον/λεγω, ηλθον/ερχομαι)
therefore count as one lexeme and compounds (επερωταω/ερωταω) as two. Crasis is resolved
before comparison (καγω → και εγω, καν → και εαν, ουδεν → ουδε εν). A form the lexicon does
not contain is compared with its partner by character similarity of the alignment keys
(same lexeme above 0.5), unless the two words differ in their verbal prefix. A block is
morphological only if every paired word is the same lexeme; a word without a partner makes
it lexical.

The rule was checked against hand annotation of two samples from John: 200 substitution
pairs drawn evenly across the range of character similarity, and the 134 substitutions of
the 300-variant reliability sample (`annotation/`).

The lexicon is derived from MorphGNT (https://github.com/morphgnt/sblgnt), whose parsing
and lemmatisation are licensed CC BY-SA 3.0; the derived list is distributed under the
same licence. Rebuild it with `python -m src.utils.build_lemma_lexicon path/to/sblgnt`.

Unequal replace blocks (e.g. two words replaced by one) are kept as single substitution
units; `n_base_words` and `n_ms_words` record the block shape. Each variant carries a
context window of five words on either side in the baseline and in the manuscript.

### Embeddings (`profile_scribes.py`)

Each context window is embedded with `pranaydeeps/Ancient-Greek-BERT`; the 768-d vector is
the attention-masked mean of the last-layer token vectors. The **change vector** of a
variant is `embedding(manuscript context) − embedding(baseline context)`. A manuscript
profile is the mean change vector of its variants; chapter profiles likewise.

### Feature isolation (`run_ablation_study.py`)

Three derived datasets probe what the embedding separation rests on:

- **function words only** – the variants whose two readings consist entirely of function
  words (articles, pronouns, particles, conjunctions, prepositions, negations); the
  context windows are untouched;
- **content masked** – every variant, with each content word in the readings and in the
  context windows replaced by `CONTENT`, so that only the function words and the word
  positions remain visible to the model;
- **random masked (control)** – every variant, with the same *number* of words per field
  replaced by `CONTENT` as under content masking, but at positions drawn at random
  (seeded by verse, witness and block) irrespective of word class. Because the control is
  a random draw, five draws are written (`random_masked` with seed 42 and
  `random_masked_s1`–`s4`) and its effect is reported as the mean over draws. The difference
  between the masked conditions isolates the effect of *which* words are hidden from the
  effect of how many.

### Statistical framework (`run_statistical_tests.py`, `src/stats_core.py`)

The statistics are in `src/stats_core.py`, which is shared with the multi-corpus SCRIPTA
pipeline, so that John gives identical numbers in both. Every resampling procedure draws
from its own random generator seeded with 42.

- Distances between change vectors and between profiles are **cosine** distances.
- **Cohen's d** compares inter-manuscript with intra-manuscript pairwise distances on all
  change vectors (point estimate); a 95 % CI comes from a chapter-level block bootstrap
  (B = 2,000, 1,000 vectors per replicate) and the null from chapter-restricted label
  permutations (2,000) on the same vectors as the point estimate. The report also
  gives d within each variant class, d for every pair of witnesses, and d after averaging
  the change vectors per verse and manuscript.
- **ARI** compares k-means clusters (k = number of witnesses, `n_init=10`, seed 42, at most
  3,000 variants) with the manuscript labels; null by chapter-restricted permutation (200).
- **Cramér's V** on the variant-type contingency tables (point estimate), with a
  chapter-level block bootstrap (B = 2,000) and chapter-restricted permutations (200).
- Permutation p-values are reported as (k + 1)/(B + 1).
- **Split-half replicability**: Spearman ρ between the six inter-manuscript centroid
  distances computed on odd and on even chapters, with and without restriction to the
  532 verses attested in all witnesses; in addition the full odd/even centroid distance
  matrix and the paired distances are written to `outputs/split_half_*.csv`.

## Pipeline Execution

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Extract variants (downloads the ITSEE XML on first run); writes data/variants_full_john_<MS>.csv,
#    outputs/type_counts_full_<MS>.csv and outputs/coverage_report.csv
python download_itsee_data.py --baseline B
python download_itsee_data.py --baseline A
python download_itsee_data.py --baseline aleph
python download_itsee_data.py --baseline B --exclude-supplied   # robustness configuration

# 3. Derived datasets
python create_verse_matched_dataset.py
python run_ablation_study.py

# 4. Embeddings (needs torch + transformers and the Ancient-Greek-BERT model)
python profile_scribes.py --baseline B
python profile_scribes.py --baseline A
python profile_scribes.py --ablation matched
python profile_scribes.py --ablation func_words
python profile_scribes.py --ablation masked
python profile_scribes.py --ablation random_masked
python profile_scribes.py --ablation random_masked_s1    # … s2, s3, s4
python profile_scribes.py --baseline aleph

# 5. Statistics (add --typology-only to run the variant-type tests without embeddings)
python run_statistical_tests.py --baseline B
python run_statistical_tests.py --ablation matched      # etc.

# 6. Figures
python create_visualizations.py --baseline B
python create_visualizations.py --ablation matched      # etc.

# 7. Website data
cd docs && python prepare_website_data.py

# 8. Robustness: the SBL edition (MorphGNT, data/morphgnt/) as anchor, typology only
python sbl_anchor.py      # -> data/variants_full_john_SBL.csv, outputs/sbl_anchor_john.json

# 9. Checks reported in § 5.1: Bezae's unequal replacement blocks; Sinaiticus in John 1:1-8:38
python john_text_checks.py   # -> outputs/john_text_checks.json
```

The MorphGNT text in `data/morphgnt/` (Tauber 2017, doi:10.5281/zenodo.376200) is distributed
under its own licence, CC BY-SA 3.0.

## Output Interpretation

Manuscript profiles capture manuscript-level patterns of textual variation. High
similarity between profiles may indicate shared text-type affiliation, a common exemplar
tradition, similar scribal training, or geographic/temporal proximity. The profiles do
not prove individual scribe identification, do not distinguish intentional from
unintentional changes, and say nothing about the direction of change (which requires a
genealogical method such as the CBGM).

## Relationship to Existing Methods

The Coherence-Based Genealogical Method used in the Editio Critica Maior addresses
genealogical relationships and textual flow; this tool characterises aggregate change
profiles. Traditional scribal-habits studies (Royse, Head, Hernández) identify tendencies
of specific manuscripts by manual analysis; this tool offers automated, corpus-scale
counts and effect sizes with uncertainty, but cannot attribute patterns to individual
scribes rather than to the tradition.

## Interactive Website

[https://agnieszkachr.github.io/scribal-fingerprints/](https://agnieszkachr.github.io/scribal-fingerprints/)

A static HTML/CSS/JS companion site in `docs/` (GitHub Pages) with interactive Plotly
charts, a manuscript coverage table and a searchable explorer of ~2,000 sampled variants.
Serve locally with `cd docs && python -m http.server 8080`; regenerate its data files with
`python prepare_website_data.py` from the `docs/` directory.

## License

This project is licensed under the [MIT License](LICENSE).

## Citation

If you use this code or data, please cite:

> Ziemińska, A. B. (2026). *scribal-fingerprints: The Typological Structure of Textual Variation in the Gospel of John (code and data)* (version 2.0.0). Zenodo. https://doi.org/10.5281/zenodo.23359316

```bibtex
@software{zieminska2026scribal_software,
  author    = {Ziemińska, Agnieszka B.},
  title     = {scribal-fingerprints: The Typological Structure of Textual Variation in the Gospel of John (code and data)},
  year      = {2026},
  publisher = {Zenodo},
  version   = {2.0.0},
  doi       = {10.5281/zenodo.23359316},
  url       = {https://doi.org/10.5281/zenodo.23359316}
}
```
