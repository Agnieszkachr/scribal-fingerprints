"""Paths and constants for the extraction pipeline (John-only configuration)."""

from pathlib import Path
from typing import List

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
VARIANTS_DIR: Path = DATA_DIR / "variants"
EMBEDDINGS_DIR: Path = DATA_DIR / "embeddings"
COMMON_VERSES_DIR: Path = DATA_DIR / "common_verses"

OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
DOCS_DATA_DIR: Path = DOCS_DIR / "data"
DOCS_IMG_DIR: Path = DOCS_DIR / "img"

CORPORA: List[str] = ["john"]

BASELINE_MANUSCRIPT: str = "B"   # Codex Vaticanus

BERT_MODEL: str = "pranaydeeps/Ancient-Greek-BERT"
BERT_MODEL_REVISION: str = "main"

RANDOM_SEED: int = 42


def ensure_dirs() -> None:
    """Create the project directories if they do not exist."""
    for d in [RAW_DIR, VARIANTS_DIR, EMBEDDINGS_DIR, COMMON_VERSES_DIR,
              OUTPUTS_DIR, DOCS_DATA_DIR, DOCS_IMG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    for corpus in CORPORA:
        (RAW_DIR / corpus).mkdir(parents=True, exist_ok=True)
        (OUTPUTS_DIR / corpus).mkdir(parents=True, exist_ok=True)
