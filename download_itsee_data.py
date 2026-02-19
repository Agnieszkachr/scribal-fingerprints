import os
import requests
import xml.etree.ElementTree as ET
import difflib
import pandas as pd
import re
import unicodedata

ITSEE_URLS = {
    'P66': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_P66_John.xml',
    'aleph': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_01_John.xml',
    'A': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_02_John.xml',
    'B': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_03_John.xml',
    'D': 'https://itseeweb.cal.bham.ac.uk/iohannes/transcriptions/greek/NT_GRC_05_John.xml'
}

def clean_text(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def normalize_orthography(word):
    w = strip_accents(word.lower())
    w = re.sub(r'ν$', '', w)  # Movable nu
    w = w.replace('ει', 'ι')   # Itacism
    w = w.replace('η', 'ι')    # Itacism
    w = w.replace('υ', 'ι')    # Itacism
    w = w.replace('αι', 'ε')   # Itacism
    w = w.replace('ω', 'ο')    # Alpha-O/Omega
    w = w.replace('ς', 'σ')    # Sigma
    return w

def is_orthographic_noise(w1, w2):
    if w1 == "[ADD]" or w2 == "[OMIT]": return False
    w1_norm = normalize_orthography(" ".join(w1.split()))
    w2_norm = normalize_orthography(" ".join(w2.split()))
    return w1_norm == w2_norm

def parse_verse_id(n):
    # Formats: John.1.1 or B04K1V1
    if n.startswith('John.'):
        parts = n.split('.')
        if len(parts) >= 3:
            return int(parts[1]), int(parts[2])
    elif n.startswith('B04K'):
        match = re.search(r'K(\d+)V(\d+)', n)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None, None

def process_xml(file_path, ms_name):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    verses = {}
    coverage = {} # chapter -> verse count
    
    for ab in root.findall('.//tei:ab', ns):
        n = ab.get('n', '')
        ch, v = parse_verse_id(n)
        if ch is not None:
            verse_label = f"J {ch}:{v}"
            words = []
            for w in ab.findall('.//tei:w', ns):
                text_content = "".join(w.itertext())
                if text_content: 
                    words.append(clean_text(text_content))
            
            verses[verse_label] = " ".join(words)
            coverage[ch] = coverage.get(ch, 0) + 1
            
    return verses, coverage

import argparse

def download_and_extract(base_ms='B'):
    os.makedirs('data/xml', exist_ok=True)
    ms_texts = {}
    coverage_data = []
    
    # Expected total verses per chapter for John (rough estimate for coverage report)
    expected_verses = {
        1:51, 2:25, 3:36, 4:54, 5:47, 6:71, 7:53, 8:59, 9:41, 10:42,
        11:57, 12:50, 13:38, 14:31, 15:27, 16:33, 17:26, 18:40, 19:42, 20:31, 21:25
    }

    print("Retrieving ITSEE XML files...")
    for ms, url in ITSEE_URLS.items():
        filepath = f"data/xml/{ms}.xml"
        if not os.path.exists(filepath):
            print(f"Downloading {ms}...")
            r = requests.get(url)
            with open(filepath, 'wb') as f:
                 f.write(r.content)
        
        texts, coverage = process_xml(filepath, ms)
        ms_texts[ms] = texts
        
        for ch in range(1, 22):
            v_count = coverage.get(ch, 0)
            total = expected_verses.get(ch, 1)
            coverage_data.append({
                'manuscript': ms,
                'chapter': ch,
                'verses_available': v_count,
                'verses_total': total,
                'coverage_pct': round((v_count / total) * 100, 2)
            })

    # Only write coverage report if strictly needed, or skip overwriting
    pd.DataFrame(coverage_data).to_csv('outputs/coverage_report.csv', index=False)
    print("Coverage report saved to outputs/coverage_report.csv")

    target_mss = ['P66', 'aleph', 'A', 'B', 'D']
    variants = []
    
    print(f"Extracting variants for Chapters 1-21 against {base_ms}...")
    for verse_id, base_text in ms_texts[base_ms].items():
        base_words = base_text.split()
        if not base_words: continue
        
        # Extract chapter from "J ch:v"
        ch_match = re.search(r'J (\d+):', verse_id)
        chapter = int(ch_match.group(1)) if ch_match else 0
        
        for ms in target_mss:
            if ms == base_ms: continue # Do not compare baseline to itself
            if verse_id not in ms_texts[ms]: continue
            
            ms_text = ms_texts[ms][verse_id]
            ms_words = ms_text.split()
            if not ms_words: continue
            
            s = difflib.SequenceMatcher(None, base_words, ms_words)
            
            for tag, i1, i2, j1, j2 in s.get_opcodes():
                if tag != 'equal':
                    base_reading = " ".join(base_words[i1:i2]) if i1 != i2 else "[ADD]"
                    ms_reading = " ".join(ms_words[j1:j2]) if j1 != j2 else "[OMIT]"
                    
                    if not base_reading.strip() and not ms_reading.strip(): continue
                    if is_orthographic_noise(base_reading, ms_reading): continue
                    
                    # 10-word context
                    start_i = max(0, i1 - 5)
                    end_i = min(len(base_words), i2 + 5)
                    base_context = " ".join(base_words[start_i:end_i])
                    
                    start_j = max(0, j1 - 5)
                    end_j = min(len(ms_words), j2 + 5)
                    ms_context = " ".join(ms_words[start_j:end_j])
                    
                    refined_tag = tag
                    if base_reading == "[ADD]": refined_tag = 'addition'
                    elif ms_reading == "[OMIT]": refined_tag = 'omission'
                    elif tag == 'replace':
                        bw, mw = base_reading.split(), ms_reading.split()
                        if len(bw) == len(mw) and sorted(bw) == sorted(mw):
                            refined_tag = 'substitution_word_order'
                        else:
                            sm = difflib.SequenceMatcher(None, normalize_orthography(base_reading), normalize_orthography(ms_reading))
                            refined_tag = 'substitution_morphological' if sm.ratio() > 0.5 else 'substitution_lexical'
                    
                    if bool(re.search(r'[A-Za-zα-ωΑ-Ω]', base_reading)) or bool(re.search(r'[A-Za-zα-ωΑ-Ω]', ms_reading)):
                        variants.append({
                            'chapter': chapter,
                            'verse': verse_id,
                            'manuscript': ms,
                            'base_reading': base_reading,
                            'ms_reading': ms_reading,
                            'type': refined_tag,
                            'base_context_10w': base_context,
                            'ms_context_10w': ms_context
                        })
                    
    df = pd.DataFrame(variants)
    output_target = f'data/variants_full_john_{base_ms}.csv'
    df.to_csv(output_target, index=False)
    print(f"Extracted {len(df)} substantive variants against {base_ms} to {output_target}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract scribal variants against a baseline MS.')
    parser.add_argument('--baseline', type=str, default='B', help='Baseline manuscript (B, aleph, A, D)')
    args = parser.parse_args()
    download_and_extract(base_ms=args.baseline)
