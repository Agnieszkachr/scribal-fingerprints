"""Agreement between the variant-annotation rule and the hand annotation of
two samples from John (baseline B).

* ``threshold_sample_200.csv`` -- 200 substitution pairs drawn with a fixed
  seed, 25 from each of eight equal bands of character similarity, annotated
  blind as M (same lexeme, different form) or L (different lexeme).
* ``reliability_sample_john_300.csv`` -- 300 variants stratified by the type
  assigned at sampling (``sampling_stratum``), annotated blind into the five
  variant types.

The rule's labels are taken from ``data/variants_full_john_B.csv``. For the
threshold sample, the character-similarity rule (same lexeme above a
threshold) is reported alongside for comparison.

    python annotation/evaluate_annotation.py
"""
import difflib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.utils.lemma_lexicon import key  # noqa: E402
from src.utils.token_normalizer import normalize_orthography  # noqa: E402

TYPE_NAMES = {
    "substitution_morphological": "Morphological substitution",
    "substitution_lexical": "Lexical substitution",
    "substitution_word_order": "Word-order shift",
    "addition": "Addition", "omission": "Omission",
}


def kappa(a, b):
    a, b = pd.Series(a).reset_index(drop=True), pd.Series(b).reset_index(drop=True)
    po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in set(a) | set(b))
    return po, (po - pe) / (1 - pe)


def char_rule(base, ms, threshold):
    b = [normalize_orthography(key(w)) for w in str(base).split()]
    m = [normalize_orthography(key(w)) for w in str(ms).split()]
    sim = lambda x, y: difflib.SequenceMatcher(None, x, y, autojunk=False).ratio()
    s = (sum(sim(x, y) for x, y in zip(b, m)) / len(b)) if len(b) == len(m) else sim(" ".join(b), " ".join(m))
    return "M" if s > threshold else "L"


def rule_labels(sample):
    table = pd.read_csv(ROOT / "data" / "variants_full_john_B.csv")
    lookup = {(r.verse, r.manuscript, r.base_reading, r.ms_reading): r.type for r in table.itertuples()}
    return sample.apply(lambda r: lookup.get((r.verse, r.manuscript, r.baseline_reading, r.manuscript_reading)), axis=1)


def threshold_sample():
    s = pd.read_csv(Path(__file__).parent / "threshold_sample_200.csv")
    s = s[s.annotation.isin(["M", "L"])].copy()
    s["rule"] = rule_labels(s).map({"substitution_morphological": "M", "substitution_lexical": "L"})
    print(f"Threshold sample: {len(s)} annotated pairs ({(s.annotation == 'M').sum()} M, {(s.annotation == 'L').sum()} L)")
    rows = [("lexicon rule (current)", s.rule)]
    for t in (0.5, 0.57):
        rows.append((f"character similarity > {t}", s.apply(lambda r: char_rule(r.baseline_reading, r.manuscript_reading, t), axis=1)))
    for name, pred in rows:
        po, k = kappa(s.annotation, pred)
        prec = {c: ((pred == c) & (s.annotation == c)).sum() / max((pred == c).sum(), 1) for c in "ML"}
        rec = {c: ((pred == c) & (s.annotation == c)).sum() / max((s.annotation == c).sum(), 1) for c in "ML"}
        print(f"  {name:30} agreement {po:.3f}  kappa {k:.3f}  "
              f"M precision {prec['M']:.3f} recall {rec['M']:.3f}  L precision {prec['L']:.3f} recall {rec['L']:.3f}")
    grid = np.round(np.arange(0.20, 0.81, 0.01), 2)
    acc = [(s.apply(lambda r: char_rule(r.baseline_reading, r.manuscript_reading, t), axis=1) == s.annotation).mean() for t in grid]
    print(f"  best character-similarity threshold: {grid[int(np.argmax(acc))]:.2f} (agreement {max(acc):.3f})")
    return s


def reliability_sample():
    s = pd.read_csv(Path(__file__).parent / "reliability_sample_john_300.csv")
    s["rule"] = rule_labels(s).map(TYPE_NAMES)
    s = s[s.annotation.notna()]
    print(f"\nReliability sample: {len(s)} annotated variants, {int(s.unsure.sum())} flagged unsure")
    interp = s.rule.isin(["Morphological substitution", "Lexical substitution", "Word-order shift"])
    for name, sub in (("all variants", s), ("substitutions and word order", s[interp]),
                      ("additions and omissions", s[~interp]),
                      ("substitutions only (M/L)", s[s.rule.isin(["Morphological substitution", "Lexical substitution"])])):
        po, k = kappa(sub.annotation, sub.rule)
        print(f"  {name:30} n={len(sub):3}  agreement {po:.3f}  kappa {k:.3f}")
    print("  agreement by the rule's category:")
    for cat, sub in s.groupby("rule"):
        print(f"    {cat:28} {int((sub.annotation == cat).sum()):3}/{len(sub):3}")
    print(pd.crosstab(s.rule, s.annotation, rownames=["rule"], colnames=["annotation"]).to_string())
    return s


if __name__ == "__main__":
    threshold_sample()
    reliability_sample()
