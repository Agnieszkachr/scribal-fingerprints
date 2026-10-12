"""Fetch the ITSEE TEI XML transcriptions of John and extract classified variants.

The parsing, alignment and classification live in ``src/extract_variants.py``
(see its docstring for the TEI handling, the normalisation rules and the
typology). This script downloads the transcriptions into ``data/raw/john/``,
runs the extraction against the chosen baseline, and writes the variant table
in the column layout the analysis scripts read::

    data/variants_full_john_{baseline}.csv
    outputs/coverage_report.csv
    outputs/type_counts_full_{baseline}.csv

Usage::

    python download_itsee_data.py [--baseline B] [--exclude-supplied] [--exclude-unclear]
"""

import argparse
import shutil

import pandas as pd

from src import extract_variants as ev
from src.config import OUTPUTS_DIR, RAW_DIR, VARIANTS_DIR, ensure_dirs
from src.download_itsee_data import download_xml

CORPUS = "john"
TARGET_MSS = ["P66", "aleph", "A", "B", "D"]
VARIANT_TYPES = ev.VARIANT_TYPES

# Column names used by the analysis scripts in this repository.
COLUMNS = {
    "variant_type": "type",
    "baseline_reading": "base_reading",
    "manuscript_reading": "ms_reading",
}
COLUMN_ORDER = [
    "chapter", "verse", "manuscript", "base_reading", "ms_reading", "type",
    "base_context_10w", "ms_context_10w", "base_norm", "ms_norm",
    "n_base_words", "n_ms_words", "block_index", "reconstructed", "uncertain",
]


def load_all_transcriptions(download: bool = True):
    """Parsed transcriptions, {siglum: {verse: [Token, ...]}}, plus the coverage table."""
    ensure_dirs()
    if download:
        download_xml(CORPUS)
    ms_texts = ev.load_corpus(CORPUS)
    return ms_texts, ev.coverage_report(CORPUS, ms_texts)


def write_type_counts(df: pd.DataFrame, suffix: str, out_dir=OUTPUTS_DIR) -> str:
    """Per-manuscript counts of each variant type for a derived dataset."""
    work = df.rename(columns={"type": "variant_type"})
    path = OUTPUTS_DIR / f"type_counts_full_{suffix}.csv"
    ev.type_counts(work).to_csv(path, index=False)
    return str(path)


def download_and_extract(base_ms: str = "B", exclude_supplied: bool = False,
                         exclude_unclear: bool = False) -> pd.DataFrame:
    ensure_dirs()
    print("Loading ITSEE XML transcriptions...")
    download_xml(CORPUS)

    ev.EXCLUDE_SUPPLIED = exclude_supplied
    ev.EXCLUDE_UNCLEAR = exclude_unclear
    df = ev.extract_for_corpus(CORPUS, base_ms=base_ms)
    if df is None:
        raise SystemExit("Extraction produced no table; check data/raw/john/.")

    policy = ("_drop_supplied" if exclude_supplied else "") + ("_drop_unclear" if exclude_unclear else "")
    df = df.rename(columns=COLUMNS)[COLUMN_ORDER]
    target = VARIANTS_DIR.parent / f"variants_full_john_{base_ms}{policy}.csv"
    df.to_csv(target, index=False)
    print(f"Extracted {len(df)} variants against {base_ms} to {target}")
    print(df["type"].value_counts().to_string())

    out_dir = OUTPUTS_DIR / CORPUS
    suffix = "" if base_ms == "B" else f"_{base_ms}"
    if exclude_supplied:
        suffix += "_drop_supplied"
    if exclude_unclear:
        suffix += "_drop_unclear"
    shutil.copy(out_dir / f"coverage_report{suffix}.csv", OUTPUTS_DIR / "coverage_report.csv")
    shutil.copy(out_dir / f"type_counts_john{suffix}.csv",
                OUTPUTS_DIR / f"type_counts_full_{base_ms}{policy}.csv")
    print("Coverage report saved to outputs/coverage_report.csv")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract variants of John against a baseline witness.")
    parser.add_argument("--baseline", default="B", help="Baseline witness (P66, aleph, A, B, D)")
    parser.add_argument("--exclude-supplied", action="store_true",
                        help="Drop variant blocks resting on <supplied> text or a <gap>.")
    parser.add_argument("--exclude-unclear", action="store_true",
                        help="Drop variant blocks resting on <unclear> text.")
    args = parser.parse_args()
    download_and_extract(args.baseline, args.exclude_supplied, args.exclude_unclear)
