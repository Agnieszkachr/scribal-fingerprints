import os
import xml.etree.ElementTree as ET
import pandas as pd

from download_itsee_data import ITSEE_URLS, parse_verse_id

def process_xml_verses(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    verses = set()
    for ab in root.findall('.//tei:ab', ns):
        n = ab.get('n', '')
        ch, v = parse_verse_id(n)
        if ch is not None:
            # Check if there is actual content
            content = "".join(ab.itertext()).strip()
            if len(content) > 3: # Has some words
                verses.add(f"J {ch}:{v}")
    return verses

def main():
    target_mss = ['P66', 'aleph', 'A', 'B', 'D']
    ms_verse_sets = {}
    
    for ms in target_mss:
        filepath = f"data/xml/{ms}.xml"
        if not os.path.exists(filepath):
            print(f"Missing XML for {ms}!")
            return
        
        verses = process_xml_verses(filepath)
        ms_verse_sets[ms] = verses
        print(f"Found {len(verses)} verses with text for {ms}")
        
    common_verses = set.intersection(*ms_verse_sets.values())
    print(f"Extant Common Verses across all 5: {len(common_verses)}")
    
    with open("data/common_extant_verses.txt", "w") as f:
        for v in sorted(list(common_verses)):
            f.write(f"{v}\n")
            
    df = pd.read_csv("data/variants_full_john_B.csv")
    initial_len = len(df)
    
    df_ablation = df[df['verse'].isin(common_verses)]
    final_len = len(df_ablation)
    
    out_path = "data/variants_ablation_matched.csv"
    df_ablation.to_csv(out_path, index=False)
    print(f"Filtered {initial_len} variants down to {final_len} variants for verse-matched analysis.")
    print(f"Saved to {out_path}!")

if __name__ == "__main__":
    main()
