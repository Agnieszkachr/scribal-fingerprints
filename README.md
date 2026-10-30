# Manuscript Textual Profile Analysis Engine

[Interactive Website](https://agnieszkachr.github.io/scribal-fingerprints/) · [GitHub Repository](https://github.com/Agnieszkachr/scribal-fingerprints)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23359315.svg)](https://doi.org/10.5281/zenodo.23359315)

This repository contains the codebase, extraction pipelines and analytical scripts for a
computational analysis of textual variation in five major Greek witnesses to the Gospel
of John (P66, Codex Sinaiticus, Codex Alexandrinus, Codex Vaticanus, Codex Bezae).
The project asks whether the witnesses possess statistically detectable, reproducible
**manuscript-level change profiles**, combining a classical typology of variants
(addition, omission, word order, morphological and lexical substitution) with contextual
embeddings of the variant loci (`Ancient-Greek-BERT`).

This is the code and data of the article *The Typological Structure of Textual Variation:
A Computational Analysis of Major Witnesses to the Gospel of John*, which reports the first
stage of a longer project. Its result in brief: the counted typology of changes is the robust
instrument, and contextual embeddings of short context windows add little to it.

> **On the repository name.** The repository keeps its original working name,
> `scribal-fingerprints`. A profile combines the text-type, the exemplar and the scribe, and
> the design cannot separate them (see the note below), so the article speaks of
> manuscript-level profiles rather than scribal fingerprints.

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
  permutation), and the verse-level effect size is tested against its own null, in which
  whole witness-verse units are permuted within chapters (`verse_level_check.py`).

## Key Results (variant typology, current extraction)

<p align="center">
  <img src="outputs/fig4_types_full_B.png" alt="Variant-type distribution per witness (baseline B)" width="600">
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
In the odd and the even chapters separately, the same witness has the largest share of four of
the five classes (`outputs/supplementary_checks.json`).

### Embedding-based results

Against B, inter-manuscript distances between change vectors exceed intra-manuscript
distances by Cohen's d = 0.014 [0.004 – 0.026] (block permutation p < 0.001). Averaged to the
verse (2,234 witness-verse units), d = 0.016, and permuting whole units within chapters gives
p < 0.001 (anchor A: d = 0.005, p = 0.003; anchor ℵ: d = 0.010, p < 0.001;
`outputs/verse_level_permutation.json`). With the witness labels shuffled within chapter x variant
type, so that each witness keeps its mixture of types, the null is 0.001 ± 0.001 and p < 0.001 under
all three anchors (`outputs/type_stratified_permutation.json`): the separation is not a by-product
of the type mixture. The ARI of a four-cluster partition is 0.002. Within single variant classes d lies between −0.005 and
0.012, and no within-class value is distinguishable from its permutation null under all
three anchors. Feature isolation: function words only 0.008, content masked 0.006, random
masked 0.002 (mean of five draws); the difference between content and random masking, 0.004,
has a paired-bootstrap 95 % interval of −0.006 to 0.015. See `outputs/pilot_report_full_*.txt` and the website.

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
│   ├── extract_variants.py             # TEI parsing, alignment, annotation (shared with the SCRIPTA pipeline)
│   ├── download_itsee_data.py          # ITSEE download and verse-id parsing
│   ├── config.py, corpus_registry.py   # Paths, witnesses, versification
│   ├── stats_core.py                   # Inference shared with the SCRIPTA pipeline
│   └── utils/
│       ├── token_normalizer.py         # Surface forms and orthographic normalisation
│       ├── lemma_lexicon.py            # Same lexeme or different lexeme (MorphGNT form-to-lemma list)
│       └── nomina_sacra.py             # Expansion table for the attested nomina sacra
├── create_verse_matched_dataset.py     # Verse-matched subset: verses attested in all five witnesses
├── run_ablation_study.py               # Function-words-only, content-masked and random-masked (control) datasets
├── profile_scribes.py                  # Ancient-Greek-BERT embeddings, change vectors, manuscript and chapter profiles
├── run_statistical_tests.py            # Block bootstrap / permutation inference (Cramér's V, Cohen's d, ARI, split-half)
├── create_visualizations.py            # Exploratory per-configuration figures (PCA, dendrogram, type shares, cumulative ARI, heat map)
├── create_article_figures.py           # Figures 3 and 4 of the article (feature isolation, split halves)
├── sbl_anchor.py                       # Typology with the SBL edition as anchor
├── john_text_checks.py                 # Bezae's replacement blocks; Sinaiticus in John 1:1-8:38
├── supplementary_checks.py             # Within-class d with CIs, paired masking comparison, typology split halves
├── verse_level_check.py                # Cohen's d on verse aggregates with a permutation of whole witness-verse units
├── type_stratified_check.py            # Cohen's d against a null that keeps each witness's mixture of variant types
├── annotation/                         # Hand-annotated calibration (200) and reliability (300) samples, evaluation script
├── data/
│   ├── raw/john/                       # Raw ITSEE transcriptions (one file per witness)
│   ├── variants_full_john_{B,A,aleph}.csv   # Variants against each baseline
│   ├── variants_ablation_{matched,func_words,masked,random_masked[_s1..s4]}.csv
│   └── common_extant_verses.txt        # 532 verses with attested text in all five witnesses
├── outputs/                            # Type counts, coverage report, statistical reports, figures
└── docs/                               # Static companion website (GitHub Pages, main branch)
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

### Alignment and annotation

Each manuscript verse is aligned with the baseline verse by `difflib.SequenceMatcher`
(`autojunk=False`), an implementation of Ratcliff–Obershelp matching: it finds the longest
contiguous block of shared tokens and repeats the search on either side of it. This is a
heuristic, not an exact longest-common-subsequence alignment. Every non-equal block becomes one variant:

- `insert` → **addition**; `delete` → **omission**;
- `replace` with the same multiset of words → **word-order shift**;
- `replace` otherwise → **substitution**, morphological if both sides have the same number
  of words and every positionally paired word is a form of the same lexeme, lexical
  otherwise (see *Morphological vs lexical substitution* below);
- after alignment, an omission and an addition (or two substitutions) of the same words
  within eight baseline tokens of each other are merged into one **word-order shift**,
  since the alignment never emits a transposition as a single block.

### Morphological vs lexical substitution (`src/utils/lemma_lexicon.py`)

Two word forms are the same lexeme if they share a lemma in
`src/utils/data/morphgnt_form_lemmas.tsv`, a form-to-lemma list of every word form of the
MorphGNT SBLGNT (accents removed; 17,347 forms). Suppletive forms (ειπον/λεγω, ηλθον/ερχομαι)
therefore count as one lexeme and compounds (επερωταω/ερωταω) as two. Crasis is resolved
before comparison (καγω → και εγω, καν → και εαν, ουδεν → ουδε εν). A form the lexicon does
not contain is compared with its partner by character similarity of the alignment keys
A witness spelling that the lexicon does not contain is first looked up on its orthographic
alignment key (so that ερχωμαι is read as ερχομαι). A form still not found is the same lexeme
as its partner if its character similarity to some attested form of the partner's lemma is at
least 0.8 (ηνυξεν against the forms of ανοιγω). Only if neither word can be placed are the two
compared with each other (same lexeme above 0.5). Alternative spellings of one proper name
that the lexicon lemmatises separately (Μαρια/Μαριαμ) count as one lexeme. A block is
morphological only if every paired word is the same lexeme; a word without a partner makes
it lexical.

The rule was checked against blind hand annotation of two samples from John
(`annotation/`, evaluated by `python annotation/evaluate_annotation.py`):

- 200 substitution pairs, 25 from each of eight bands of character similarity: the lexicon
  rule agrees in 94.0 % (κ = 0.87), character similarity alone in 78.0 % at 0.5 and at most
  81.0 % at any threshold. The handling of crasis and witness spellings was added after the
  errors of the plain lexicon lookup (87.5 %) on this sample and on the reliability sample had
  been read, so these figures are in-sample.
- 300 variants stratified by type: κ = 0.97 over the five types; complete agreement for
  additions, omissions and word-order shifts; κ = 0.88 on the 134 substitutions
  (morphological vs lexical), where all eight disagreements lie.

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

# 6. Figures (see "Figures of the Article" below)
python create_article_figures.py         # -> outputs/fig3_feature_isolation.png, outputs/fig5_split_half.png
python create_visualizations.py --baseline B
python create_visualizations.py --ablation matched      # etc.

# 7. Agreement of the annotation rule with the hand annotation (§§ 4.1, 6.5)
python annotation/evaluate_annotation.py

# 8. Robustness: the SBL edition (MorphGNT, data/morphgnt/) as anchor, typology only
python sbl_anchor.py      # -> data/variants_full_john_SBL.csv, outputs/sbl_anchor_john.json

# 9. Checks reported in § 5.1: Bezae's unequal replacement blocks; Sinaiticus in John 1:1-8:38
python john_text_checks.py   # -> outputs/john_text_checks.json

# 10. Supplementary checks: within-class d with permutation p and bootstrap CI (anchors B, A, ℵ);
#     content masking against random masking, paired bootstrap; split halves of the typology;
#     Bezae's variants shared with Sinaiticus chapter by chapter (needs the vector files of step 4)
python supplementary_checks.py   # -> outputs/supplementary_checks.json, outputs/fig8_aleph_D_by_chapter.png

# 11. Cohen's d on verse aggregates, permuting whole witness-verse units within chapters
#     (anchors B, A, ℵ; needs the vector files of step 4)
python verse_level_check.py      # -> outputs/verse_level_permutation.json

# 12. Cohen's d against a null that shuffles witness labels within chapter x variant type
#     (anchors B, A, ℵ and the content-masked dataset; needs the vector files of step 4)
python type_stratified_check.py  # -> outputs/type_stratified_permutation.json

# 13. Website data (reads everything above; run last)
python docs/prepare_website_data.py
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

## Figures of the Article

| Article | File | Script |
|---|---|---|
| Figure 1. Variant-type distribution per witness, baseline B | `outputs/fig4_types_full_B.png` | `create_visualizations.py` |
| Figure 2. Bezae's variants shared with Sinaiticus, by chapter | `outputs/fig8_aleph_D_by_chapter.png` | `supplementary_checks.py` |
| Figure 3. Cohen's d for the full corpus and the feature-isolation datasets | `outputs/fig3_feature_isolation.png` | `create_article_figures.py` |
| Figure 4. Split-half profile distances, odd against even chapters | `outputs/fig5_split_half.png` | `create_article_figures.py` |

The numbers in the file names and in the titles printed inside the per-configuration figures
are the pipeline's own, not the article's. The two-dimensional projection
(`outputs/fig1_pca_full_B.png`) is not reproduced in the article (§ 5.2): it shows the four
witness centroids inside one cloud.

## Interactive Website

[https://agnieszkachr.github.io/scribal-fingerprints/](https://agnieszkachr.github.io/scribal-fingerprints/)

A static HTML/CSS/JS companion site in `docs/`, served by GitHub Pages from the `main`
branch. It follows the order of the article (typology first, embeddings second) with
interactive Plotly charts and the tables of the five findings, a methodology page, a
manuscript coverage table and a searchable explorer of about 2,000 sampled variants against
baselines B, A and ℵ. Serve it locally with `python -m http.server 8080 --directory docs`;
regenerate its data files and figures with `python docs/prepare_website_data.py`.

## License

This project is licensed under the [MIT License](LICENSE).

## Citation

If you use this code or data, please cite the archived release on Zenodo. The DOI below covers all
versions and resolves to the latest one; the results of the article are those of version 2.1.2,
and each version has its own DOI on the Zenodo page.

> Ziemińska, A. B. (2026). *scribal-fingerprints: The Typological Structure of Textual Variation in the Gospel of John (code and data)* (version 2.1.2). Zenodo. https://doi.org/10.5281/zenodo.23359315

```bibtex
@software{zieminska2026scribal_software,
  author    = {Ziemińska, Agnieszka B.},
  title     = {scribal-fingerprints: The Typological Structure of Textual Variation in the Gospel of John (code and data)},
  year      = {2026},
  publisher = {Zenodo},
  version   = {2.1.2},
  doi       = {10.5281/zenodo.23359315},
  url       = {https://doi.org/10.5281/zenodo.23359315}
}
```
