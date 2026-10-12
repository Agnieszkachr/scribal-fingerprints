"""Build the verse-matched subset: variants (against baseline B) restricted to
verses in which all five manuscripts have attested text."""
import re

import pandas as pd

from download_itsee_data import TARGET_MSS, load_all_transcriptions, write_type_counts


def verse_sort_key(v):
    ch, vs = re.match(r'J (\d+):(\d+)', v).groups()
    return int(ch), int(vs)


def main(base_ms='B'):
    ms_texts, _ = load_all_transcriptions(download=False)
    for ms in TARGET_MSS:
        print(f"Found {len(ms_texts[ms])} verses with attested text for {ms}")
    common_verses = set.intersection(*(set(ms_texts[ms]) for ms in TARGET_MSS))
    print(f"Verses attested in all {len(TARGET_MSS)} manuscripts: {len(common_verses)}")

    with open("data/common_extant_verses.txt", "w", encoding='utf-8') as f:
        for v in sorted(common_verses, key=verse_sort_key):
            f.write(f"{v}\n")

    df = pd.read_csv(f"data/variants_full_john_{base_ms}.csv")
    df_matched = df[df['verse'].isin(common_verses)]
    out_path = "data/variants_ablation_matched.csv"
    df_matched.to_csv(out_path, index=False)
    write_type_counts(df_matched, 'ablation_matched')
    print(f"Filtered {len(df)} variants down to {len(df_matched)} for the verse-matched analysis -> {out_path}")


if __name__ == "__main__":
    main()
