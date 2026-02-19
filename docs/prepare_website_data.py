#!/usr/bin/env python3
"""
Prepare website data files from pipeline outputs.
Reads from ../outputs/ and ../data/, writes JS data files to data/ and copies PNGs to img/.
Outputs JavaScript files (window.DATA_* = {...}) instead of JSON so they work
both via file:// protocol and HTTP server (no fetch/CORS issues).
"""

import csv
import json
import os
import random
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(SCRIPT_DIR, '..', 'outputs')
DATA_SRC_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
DATA_DEST = os.path.join(SCRIPT_DIR, 'data')
IMG_DEST = os.path.join(SCRIPT_DIR, 'img')


def ensure_dirs():
    os.makedirs(DATA_DEST, exist_ok=True)
    os.makedirs(IMG_DEST, exist_ok=True)


def read_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_js(dest, var_name, data):
    """Write data as a JS file: window.VAR_NAME = {...};"""
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(f'window.{var_name} = ')
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(';\n')
    print(f"  -> {dest}")


def read_pilot_results(tag):
    """Read pilot_results_full_{tag}.csv (vertical format: Metric,Value,CI_Low,CI_High,...)."""
    path = os.path.join(OUTPUTS_DIR, f'pilot_results_full_{tag}.csv')
    if not os.path.exists(path):
        print(f"  [!!] {path} not found")
        return None
    rows = read_csv(path)
    result = {}
    for r in rows:
        metric = r.get('Metric', '')
        val = r.get('Value', '')
        ci_low = r.get('CI_Low', '')
        ci_high = r.get('CI_High', '')
        try:
            result[metric] = float(val)
        except (ValueError, TypeError):
            result[metric] = val
        if ci_low:
            try:
                result[metric + '_CI_Low'] = float(ci_low)
            except (ValueError, TypeError):
                pass
        if ci_high:
            try:
                result[metric + '_CI_High'] = float(ci_high)
            except (ValueError, TypeError):
                pass
    return result


def build_stats_summary():
    """Build stats_summary.js from all pilot_results CSVs."""
    configs = {
        'Baseline B': 'B',
        'Baseline A': 'A',
        'Verse-matched': 'ablation_matched',
        'Function words only': 'ablation_func_words',
        'Content masked': 'ablation_masked',
    }
    summary = {}
    for label, tag in configs.items():
        data = read_pilot_results(tag)
        if data:
            summary[label] = data
            d_val = data.get("Cohen's d", 'N/A')
            ari_val = data.get('ARI', 'N/A')
            print(f"  [OK] {label}: d={d_val}, ARI={ari_val}")
        else:
            summary[label] = {"error": "data not found"}
            print(f"  [!!] {label}: data not found")

    # Build ablation comparison with percentage drops
    baseline = summary.get('Baseline B', {})
    baseline_d = baseline.get("Cohen's d", 0)
    baseline_ari = baseline.get('ARI', 0)

    ablation_panel = []
    for label in ['Baseline B', 'Verse-matched', 'Function words only', 'Content masked']:
        data = summary.get(label, {})
        d = data.get("Cohen's d", 0)
        ari = data.get('ARI', 0)
        if isinstance(d, str):
            d = 0
        if isinstance(ari, str):
            ari = 0
        d_drop = ((baseline_d - d) / baseline_d * 100) if baseline_d else 0
        ari_drop = ((baseline_ari - ari) / baseline_ari * 100) if baseline_ari else 0
        ablation_panel.append({
            'label': label,
            'cohens_d': round(float(d), 4),
            'ari': round(float(ari), 4),
            'd_pct_drop': round(float(d_drop), 1),
            'ari_pct_drop': round(float(ari_drop), 1),
        })

    out = {'configs': summary, 'ablation_panel': ablation_panel}
    write_js(os.path.join(DATA_DEST, 'stats_summary.js'), 'DATA_STATS', out)
    return out


def build_type_counts():
    """Build type_counts.js from type_counts_full_B.csv."""
    path = os.path.join(OUTPUTS_DIR, 'type_counts_full_B.csv')
    rows = read_csv(path)
    data = []
    for r in rows:
        entry = {'manuscript': r['manuscript']}
        for k, v in r.items():
            if k != 'manuscript':
                try:
                    entry[k] = int(v)
                except ValueError:
                    entry[k] = v
        data.append(entry)
    write_js(os.path.join(DATA_DEST, 'type_counts.js'), 'DATA_TYPES', data)
    return data


def build_cumulative_ari():
    """Build cumulative_ari.js from cumulative_analysis CSVs."""
    baselines = {
        'Baseline B': 'cumulative_analysis_B.csv',
        'Baseline A': 'cumulative_analysis_A.csv',
        'Verse-matched': 'cumulative_analysis_ablation_matched.csv',
    }
    result = {}
    for label, fname in baselines.items():
        path = os.path.join(OUTPUTS_DIR, fname)
        if os.path.exists(path):
            rows = read_csv(path)
            result[label] = [
                {'chapters': int(r['chapters']), 'ari': round(float(r['ari']), 6)}
                for r in rows
            ]
            print(f"  [OK] {label}: {len(rows)} data points")
        else:
            print(f"  [!!] {label}: {fname} not found")
    write_js(os.path.join(DATA_DEST, 'cumulative_ari.js'), 'DATA_CUMULATIVE', result)
    return result


def build_chapter_stability():
    """Build chapter_stability.js from chapter_stability_B.csv."""
    path = os.path.join(OUTPUTS_DIR, 'chapter_stability_B.csv')
    rows = read_csv(path)
    by_ms = {}
    for r in rows:
        ms = r['manuscript']
        if ms not in by_ms:
            by_ms[ms] = []
        by_ms[ms].append({
            'chapter': int(r['chapter']),
            'distance': round(float(r['distance_to_global']), 6),
        })
    write_js(os.path.join(DATA_DEST, 'chapter_stability.js'), 'DATA_STABILITY', by_ms)
    return by_ms


def build_coverage():
    """Build coverage.js from coverage_report.csv."""
    path = os.path.join(OUTPUTS_DIR, 'coverage_report.csv')
    rows = read_csv(path)
    data = []
    for r in rows:
        data.append({
            'manuscript': r['manuscript'],
            'chapter': int(r['chapter']),
            'verses_available': int(r['verses_available']),
            'verses_total': int(r['verses_total']),
            'coverage_pct': float(r['coverage_pct']),
        })
    write_js(os.path.join(DATA_DEST, 'coverage.js'), 'DATA_COVERAGE', data)
    return data


def build_variants_sample():
    """Build variants_sample.js: ~2000 rows stratified by manuscript & type."""
    variants_files = {
        'B': os.path.join(DATA_SRC_DIR, 'variants_full_john_B.csv'),
        'A': os.path.join(DATA_SRC_DIR, 'variants_full_john_A.csv'),
    }
    all_variants = []
    for baseline, path in variants_files.items():
        if os.path.exists(path):
            rows = read_csv(path)
            for r in rows:
                all_variants.append(r)
            print(f"  [OK] {baseline}: {len(rows)} rows loaded")

    if not all_variants:
        print("  [!!] No variant data found!")
        return []

    random.seed(42)
    target_n = 2000
    strata = {}
    for v in all_variants:
        key = (v.get('manuscript', ''), v.get('type', ''))
        if key not in strata:
            strata[key] = []
        strata[key].append(v)

    total = len(all_variants)
    sample = []
    for key, group in strata.items():
        proportion = len(group) / total
        n_sample = max(1, round(proportion * target_n))
        if len(group) <= n_sample:
            sample.extend(group)
        else:
            sample.extend(random.sample(group, n_sample))

    if len(sample) > target_n:
        sample = random.sample(sample, target_n)

    clean = []
    for v in sample:
        clean.append({
            'chapter': v.get('chapter', ''),
            'verse': v.get('verse', ''),
            'manuscript': v.get('manuscript', ''),
            'base_reading': v.get('base_reading', ''),
            'ms_reading': v.get('ms_reading', ''),
            'type': v.get('type', ''),
        })

    clean.sort(key=lambda x: (x['chapter'], x['verse'], x['manuscript']))

    write_js(os.path.join(DATA_DEST, 'variants_sample.js'), 'DATA_VARIANTS', clean)
    print(f"  ({len(clean)} rows)")
    return clean


def copy_images():
    """Copy all PNG figures from outputs/ to img/."""
    count = 0
    for fname in os.listdir(OUTPUTS_DIR):
        if fname.endswith('.png'):
            src = os.path.join(OUTPUTS_DIR, fname)
            dst = os.path.join(IMG_DEST, fname)
            shutil.copy2(src, dst)
            count += 1
    print(f"  -> Copied {count} PNG files to img/")


def main():
    print("=== Preparing website data ===\n")
    ensure_dirs()

    print("[1/7] Building stats_summary.js...")
    build_stats_summary()

    print("\n[2/7] Building type_counts.js...")
    build_type_counts()

    print("\n[3/7] Building cumulative_ari.js...")
    build_cumulative_ari()

    print("\n[4/7] Building chapter_stability.js...")
    build_chapter_stability()

    print("\n[5/7] Building coverage.js...")
    build_coverage()

    print("\n[6/7] Building variants_sample.js (~2000 rows)...")
    build_variants_sample()

    print("\n[7/7] Copying PNG figures...")
    copy_images()

    print("\n=== Done! ===")


if __name__ == '__main__':
    main()
