"""Hold-out sample for the boundary between morphological and lexical substitution.

Draws 100 substitutions from the John table of baseline B that were not seen
when the annotation rule was specified: a substitution is left out of the pool
if it belongs to one of the two earlier samples (``threshold_sample_200.csv``,
``reliability_sample_john_300.csv``) or if its pair of normalised readings
occurs in either of them. The draw is a simple random sample of the remaining
substitutions with the seed of ``src/stats_core.py``; the rule's labels are not
written to the sheet, which is annotated blind as M (same lexeme, different
form) or L (different lexeme).

    python annotation/draw_holdout_sample.py   ->  annotation/holdout_sample_100.csv

The script refuses to overwrite a sheet that already holds annotations.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import stats_core as sc  # noqa: E402

HERE = Path(__file__).resolve().parent
SHEET = HERE / "holdout_sample_100.csv"
N = 100
SUBSTITUTIONS = ["substitution_morphological", "substitution_lexical"]
KEY = ["verse", "manuscript", "base_reading", "ms_reading"]


def earlier_samples():
    frames = [pd.read_csv(HERE / name) for name in ("threshold_sample_200.csv", "reliability_sample_john_300.csv")]
    s = pd.concat(frames, ignore_index=True)
    return s.rename(columns={"baseline_reading": "base_reading", "manuscript_reading": "ms_reading"})[KEY]


def main():
    if SHEET.exists() and pd.read_csv(SHEET)["annotation"].notna().any():
        sys.exit(f"{SHEET.name} already holds annotations; it is not overwritten.")
    table = pd.read_csv(ROOT / "data" / "variants_full_john_B.csv")
    subs = table[table["type"].isin(SUBSTITUTIONS)].copy()
    seen = earlier_samples().drop_duplicates()
    in_sample = subs.merge(seen.assign(_seen=True), on=KEY, how="left")["_seen"].fillna(False).to_numpy(bool)
    seen_pairs = set(map(tuple, subs.loc[in_sample, ["base_norm", "ms_norm"]].to_numpy()))
    same_pair = subs[["base_norm", "ms_norm"]].apply(tuple, axis=1).isin(seen_pairs).to_numpy()
    pool = subs[~in_sample & ~same_pair]
    print(f"substitutions {len(subs)}; in the earlier samples {int(in_sample.sum())}; "
          f"same pair of readings as a sampled variant {int((same_pair & ~in_sample).sum())}; pool {len(pool)}")
    draw = pool.sample(n=N, random_state=sc.SEED).reset_index(drop=True)
    sheet = pd.DataFrame({
        "ID": [f"HS-{i:03d}" for i in range(1, N + 1)],
        "verse": draw["verse"],
        "manuscript": draw["manuscript"],
        "baseline_reading": draw["base_reading"],
        "manuscript_reading": draw["ms_reading"],
        "baseline_context": draw["base_context_10w"],
        "manuscript_context": draw["ms_context_10w"],
        "annotation": "",
        "unsure": "",
        "note": "",
    })
    sheet.to_csv(SHEET, index=False, encoding="utf-8")
    print(f"{SHEET.name}: {len(sheet)} substitutions, by witness {draw['manuscript'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
