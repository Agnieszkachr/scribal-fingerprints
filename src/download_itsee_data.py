"""
Download ITSEE Data
===================

Fetches TEI XML manuscript transcriptions from the ITSEE servers for a
specified corpus, and stores them in data/raw/{corpus}/.

Adapted from the scribal-fingerprints pilot study (John-only version)
to accept any corpus defined in the corpus registry.

Usage:
    python -m src.download_itsee_data --corpus john
    python -m src.download_itsee_data --corpus mark
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

from src.config import RAW_DIR, CORPORA, ensure_dirs
from src.corpus_registry import (
    CORPUS_REGISTRY, ITSEE_BASE_URLS, ITSEE_FILE_TEMPLATES, BOOK_CODES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Verse ID Parsing ────────────────────────────────────────────────

# ITSEE book codes -> the book each belongs to. Used by parse_book_code to
# recover which BOOK an <ab n="..."> belongs to, which parse_verse_id discards.
_ITSEE_BOOK_CODES = {
    "B01": "matthew", "B02": "mark", "B03": "luke", "B04": "john", "B05": "acts",
}
_NAME_TO_CODE = {
    "matt": "B01", "matthew": "B01", "mark": "B02", "luke": "B03",
    "john": "B04", "acts": "B05",
}


def parse_book_code(n):
    """Return the ITSEE book code ('B01'..'B05') an @n attribute belongs to.

    parse_verse_id() returns only (chapter, verse, volume), and its compact
    branch matches with re.search(r"K(\d+)V(\d+)", n) -- which ignores the
    leading B-number entirely. That is safe only if every <ab> in a file
    belongs to the book the filename claims. It does not: NT_GRC_01_Mark.xml
    holds 686 B02 (Mark) verses AND 19 B03 (Luke) ones, so 'B03K1V4' and
    'B02K1V4' both resolve to chapter 1 verse 4 and the later silently
    overwrites the earlier in process_xml's verses dict. That is the source of
    the cross-Gospel collisions in the variant CSVs -- a row labelled Mk 1:4
    carrying Luke 1:4 on one side.

    Handles both @n formats in use: compact ('B02K1V4') and dotted
    ('John.1.1'). Returns None if the book cannot be determined.
    """
    m = re.match(r"(B\d{2})", n or "")
    if m:
        # A compact code we do not recognise is still a *determinate* book:
        # it simply is not one of the five this project reads. Returning None
        # here would make process_xml's filter treat it as undetermined and
        # keep it, which is how fifteen verses of James (B20) entered the
        # Luke-Acts corpus from NT_GRC_02_Acts.xml. Return the code itself so
        # the caller can reject it.
        return m.group(1)
    head = (n or "").split(".")[0].strip().lower()
    return _NAME_TO_CODE.get(head)


def expected_book_codes(corpus):
    """Which ITSEE book codes legitimately belong to *corpus*."""
    codes = BOOK_CODES.get(corpus, {})
    out = set()
    for key in ("itsee_code", "itsee_code_luke", "itsee_code_acts"):
        if codes.get(key):
            out.add(codes[key])
    return out


def parse_verse_id(n: str, corpus: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Parse a TEI @n attribute into (chapter, verse, volume).

    Returns (None, None, None) if the format is unrecognised.
    The *volume* value is 'luke' or 'acts' for luke_acts only,
    or the corpus name otherwise.
    """
    codes = BOOK_CODES.get(corpus, {})
    volume = corpus

    # Luke-Acts may have two different prefixes
    if corpus == "luke_acts":
        if n.startswith("Luke.") or n.startswith("B03K"):
            volume = "luke"
        elif n.startswith("Acts.") or n.startswith("B05K"):
            volume = "acts"

    # Format: Book.chapter.verse  (e.g. John.1.1, Mark.3.5)
    for prefix in codes.get("prefix_patterns", []):
        if "." in prefix and n.startswith(prefix):
            parts = n.split(".")
            if len(parts) >= 3:
                try:
                    return int(parts[1]), int(parts[2]), volume
                except ValueError:
                    continue

    # Format: B04K1V1 (ITSEE compact encoding)
    match = re.search(r"K(\d+)V(\d+)", n)
    if match:
        return int(match.group(1)), int(match.group(2)), volume

    # Format: Book.chapter.verse for any book name
    parts = n.split(".")
    if len(parts) >= 3:
        try:
            return int(parts[-2]), int(parts[-1]), volume
        except ValueError:
            pass

    return None, None, None


# ── Download Logic ──────────────────────────────────────────────────

def download_xml(corpus: str) -> Dict[str, Path]:
    """Download ITSEE XML files for *corpus*, returning {siglum: filepath}.

    Tries each base URL in sequence for the corpus.  Files already on disk
    are not re-downloaded.  Returns only successfully downloaded files.
    """
    out_dir = RAW_DIR / corpus
    out_dir.mkdir(parents=True, exist_ok=True)

    templates = ITSEE_FILE_TEMPLATES.get(corpus, {})
    base_urls = ITSEE_BASE_URLS.get(corpus, [])
    downloaded: Dict[str, Path] = {}

    for siglum, filename in templates.items():
        filepath = out_dir / filename
        if filepath.exists():
            logger.info("Already on disk: %s", filepath.name)
            downloaded[siglum] = filepath
            continue

        success = False
        for base_url in base_urls:
            url = base_url + filename
            logger.info("Trying %s ...", url)
            try:
                r = requests.get(url, timeout=60)
                if r.status_code == 200 and len(r.content) > 500:
                    filepath.write_bytes(r.content)
                    logger.info("  ✓ Downloaded %s (%d bytes)", filename, len(r.content))
                    downloaded[siglum] = filepath
                    success = True
                    break
                else:
                    logger.warning("  ✗ HTTP %d for %s", r.status_code, url)
            except requests.RequestException as exc:
                logger.warning("  ✗ Request failed: %s", exc)

        if not success:
            logger.error(
                "Could not download %s for %s from any URL — skipping.",
                filename, corpus,
            )

    return downloaded


# ── Main ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ITSEE TEI XML transcriptions for a corpus.",
    )
    parser.add_argument(
        "--corpus", type=str, required=True, choices=CORPORA,
        help="Corpus to download: mark, matthew, luke_acts, john",
    )
    args = parser.parse_args()
    ensure_dirs()

    corpus = args.corpus
    logger.info("═══ Downloading ITSEE data for: %s ═══", corpus)

    if CORPUS_REGISTRY.get(corpus, {}).get("status") == "complete":
        out_dir = RAW_DIR / corpus
        xml_files = list(out_dir.glob("*.xml")) if out_dir.exists() else []
        if xml_files:
            logger.info(
                "Corpus '%s' is marked complete and has %d XML files — skipping download.",
                corpus, len(xml_files),
            )
            return
        else:
            logger.info(
                "Corpus '%s' is marked complete but no XML files found in %s — attempting download.",
                corpus, out_dir,
            )

    downloaded = download_xml(corpus)
    logger.info(
        "Downloaded %d / %d files for '%s'.",
        len(downloaded),
        len(ITSEE_FILE_TEMPLATES.get(corpus, {})),
        corpus,
    )

    if not downloaded:
        logger.warning(
            "No XML files obtained for '%s'. The pipeline will skip this corpus. "
            "Check ITSEE availability or place XML files manually in %s.",
            corpus, RAW_DIR / corpus,
        )


if __name__ == "__main__":
    main()
