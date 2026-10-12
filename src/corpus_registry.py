"""Corpus metadata: ITSEE sources, witnesses and versification (John-only)."""

from typing import Any, Dict, List

ITSEE_BASE_URLS: Dict[str, List[str]] = {
    "john": ["https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/"],
}

ITSEE_FILE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "john": {
        "P66": "NT_GRC_P66_John.xml",
        "aleph": "NT_GRC_01_John.xml",
        "A": "NT_GRC_02_John.xml",
        "B": "NT_GRC_03_John.xml",
        "D": "NT_GRC_05_John.xml",
    },
}

BOOK_CODES: Dict[str, Dict[str, Any]] = {
    "john": {
        "itsee_code": "B04",
        "prefix_patterns": ["John.", "B04K"],
        "total_chapters": 21,
    },
}

CORPUS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "john": {
        "status": "complete",
        "witnesses": {
            "B":     {"siglum": "03", "century": 4, "text_type": "Alexandrian"},
            "aleph": {"siglum": "01", "century": 4, "text_type": "Alexandrian"},
            "A":     {"siglum": "02", "century": 5, "text_type": "Byzantine"},
            "D":     {"siglum": "05", "century": 5, "text_type": "Western"},
            "P66":   {"siglum": "P66", "century": 2, "text_type": "early_papyrus"},
        },
        "known_lacunae": {
            "A": ["6:50-8:52 (missing leaves)"],
            "D": ["1:16-3:26, 18:14-20:13 (later hand)"],
            "P66": ["fragmentary from 14; 21:10-25 missing"],
        },
        "expected_verses_per_chapter": {
            1: 51, 2: 25, 3: 36, 4: 54, 5: 47, 6: 71, 7: 53, 8: 59,
            9: 41, 10: 42, 11: 57, 12: 50, 13: 38, 14: 31, 15: 27,
            16: 33, 17: 26, 18: 40, 19: 42, 20: 31, 21: 25,
        },
        "corpus_specific_flags": {},
    },
}


def get_corpus_witnesses(corpus: str) -> list:
    return list(CORPUS_REGISTRY.get(corpus, {}).get("witnesses", {}).keys())
