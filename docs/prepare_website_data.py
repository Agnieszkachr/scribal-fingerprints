#!/usr/bin/env python3
"""
Prepare website data files from pipeline outputs.
Reads from ../outputs/ and ../data/, writes JS data files to data/ and copies the
figures the website shows to img/ (and removes any other PNG from img/).
Outputs JavaScript files (window.DATA_* = {...}) instead of JSON so they work
both via file:// protocol and HTTP server (no fetch/CORS issues).

    python docs/prepare_website_data.py
"""

import csv
import json
import os
import random
import re
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


DATA_FILES = {
    'B': 'variants_full_john_B.csv',
    'A': 'variants_full_john_A.csv',
    'aleph': 'variants_full_john_aleph.csv',
    'ablation_matched': 'variants_ablation_matched.csv',
    'ablation_func_words': 'variants_ablation_func_words.csv',
    'ablation_masked': 'variants_ablation_masked.csv',
    'ablation_random_masked': 'variants_ablation_random_masked.csv',
}

# The random-masking control is reported as the mean over five draws.
RANDOM_TAGS = ['ablation_random_masked'] + [f'ablation_random_masked_s{i}' for i in range(1, 5)]
for _tag in RANDOM_TAGS[1:]:
    DATA_FILES.setdefault(_tag, f'variants_{_tag}.csv')

# Figures shown on the website (copied from ../outputs/ to img/).
SITE_IMAGES = ['fig1_pca_full_B.png', 'fig8_aleph_D_by_chapter.png']


def count_variants(tag):
    """Number of variants currently in the data CSV for this configuration."""
    fname = DATA_FILES.get(tag)
    if not fname:
        return None
    path = os.path.join(DATA_SRC_DIR, fname)
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        return sum(1 for _ in f) - 1


def read_report_n(tag):
    """N of variants the embedding report was computed on (first line of the report)."""
    path = os.path.join(OUTPUTS_DIR, f'pilot_report_full_{tag}.txt')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8', errors='replace') as f:
        m = re.search(r'N=(\d+)', f.readline())
    return int(m.group(1)) if m else None


def read_metric_rows(path):
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
        # Permutation null mean and block-permutation p-value, where reported
        for col, suffix in (('Null_Mean', '_Null_Mean'), ('Perm_P', '_P')):
            v = r.get(col, '')
            if v:
                try:
                    result[metric + suffix] = float(v)
                except (ValueError, TypeError):
                    pass
    return result


def read_pilot_results(tag):
    """Merge the embedding results (pilot_results_full_{tag}.csv) with the
    variant-type results (typology_results_{tag}.csv).  The type-based
    metrics are taken from the typology file when it exists, because it is
    recomputed directly from the current variant CSV.  ``stale`` flags an
    embedding report computed on a different number of variants than the
    current data file contains."""
    result = {}
    pilot = os.path.join(OUTPUTS_DIR, f'pilot_results_full_{tag}.csv')
    typology = os.path.join(OUTPUTS_DIR, f'typology_results_{tag}.csv')
    if os.path.exists(pilot):
        result.update(read_metric_rows(pilot))
    if os.path.exists(typology):
        result.update(read_metric_rows(typology))
    if not result:
        print(f"  [!!] no results for {tag}")
        return None
    rho = None
    for key in ('Odd_Even_Split_Rho_AttestLoci', 'Odd_Even_Split_Rho_Full', 'Odd_Even_Split_Rho'):
        if isinstance(result.get(key), float):
            rho = result[key]
            break
    if rho is not None:
        result['Odd_Even_Split_Rho'] = rho
    n_report, n_current = read_report_n(tag), count_variants(tag)
    result['N'] = n_report
    result['N_current'] = n_current
    result['stale'] = bool(n_report and n_current and n_report != n_current)
    return result


def read_random_masked():
    """The random-masking control: the mean over the five draws for Cohen's d,
    its interval, null mean and ARI, with every draw listed.  A mean of the
    draws' p-values is not meaningful, so the number of draws with p <= 0.05 is
    given instead."""
    draws = [(tag, read_pilot_results(tag)) for tag in RANDOM_TAGS]
    draws = [(tag, d) for tag, d in draws if d]
    if not draws:
        return None
    result = dict(draws[0][1])
    for key in ("Cohen's d", "Cohen's d_CI_Low", "Cohen's d_CI_High", "Cohen's d_Null_Mean",
                "Cohen's d Verse", 'ARI'):
        vals = [d[key] for _, d in draws if isinstance(d.get(key), float)]
        if len(vals) == len(draws):
            result[key] = sum(vals) / len(vals)
    for key in ("Cohen's d_P", 'ARI_P', 'ARI_Null_Mean'):
        result.pop(key, None)
    result['draws'] = [{'tag': tag, 'd': d.get("Cohen's d"), 'p': d.get("Cohen's d_P"),
                        'ari': d.get('ARI')} for tag, d in draws]
    result['n_draws'] = len(draws)
    result['n_draws_significant'] = sum(
        1 for _, d in draws if isinstance(d.get("Cohen's d_P"), float) and d["Cohen's d_P"] <= 0.05)
    return result


def build_stats_summary():
    """Build stats_summary.js from all pilot_results CSVs."""
    configs = {
        'Baseline B': 'B',
        'Baseline A': 'A',
        'Baseline ℵ': 'aleph',
        'Attested in all five (532 verses)': 'ablation_matched',
        'Function words only': 'ablation_func_words',
        'Content masked': 'ablation_masked',
        'Random masked (control)': None,
    }
    summary = {}
    for label, tag in configs.items():
        data = read_pilot_results(tag) if tag else read_random_masked()
        if data:
            summary[label] = data
            d_val = data.get("Cohen's d", 'N/A')
            ari_val = data.get('ARI', 'N/A')
            print(f"  [OK] {label}: d={d_val}, ARI={ari_val}")
        else:
            summary[label] = {"error": "data not found"}
            print(f"  [!!] {label}: data not found")

    # Feature isolation (article § 5.4, Table 5): d with its block-bootstrap
    # interval, permutation null mean and p-value for each condition.
    feature_panel = []
    for label, src in [('Full context', 'Baseline B'),
                       ('Function words only', 'Function words only'),
                       ('Content masked', 'Content masked'),
                       ('Random masked (control)', 'Random masked (control)')]:
        data = summary.get(src, {})
        feature_panel.append({
            'label': label,
            'n': data.get('N_current') or data.get('N'),
            'd': data.get("Cohen's d"),
            'ci_low': data.get("Cohen's d_CI_Low"),
            'ci_high': data.get("Cohen's d_CI_High"),
            'null_mean': data.get("Cohen's d_Null_Mean"),
            'p': data.get("Cohen's d_P"),
            'ari': data.get('ARI'),
            'draws': [x['d'] for x in data.get('draws', [])] or None,
            'n_draws_significant': data.get('n_draws_significant'),
        })

    out = {'configs': summary, 'feature_panel': feature_panel}
    write_js(os.path.join(DATA_DEST, 'stats_summary.js'), 'DATA_STATS', out)
    return out


def build_article_checks():
    """Build article_checks.js: the analyses reported in the article that are
    not part of the per-configuration results -- the SBL edition as anchor
    (§ 5.5), Bezae's replacement blocks and Sinaiticus in John 1:1-8:38
    (§ 5.1), d within each variant class (§ 5.3, Table 4), the paired
    comparison of the masked conditions (§ 5.4), and the split halves of the
    embeddings and of the typology (§ 5.5, Table 6)."""
    out = {}
    path = os.path.join(OUTPUTS_DIR, 'sbl_anchor_john.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            s = json.load(f)
        out['sbl'] = {
            'n': s['n'],
            'per_witness': s['per_witness'],
            'association': s['association'],
            'shares': {w: v['shares'] for w, v in s['witnesses'].items()},
        }
        print("  [OK] SBL anchor")
    path = os.path.join(OUTPUTS_DIR, 'john_text_checks.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            out['text_checks'] = json.load(f)
        print("  [OK] Bezae's replacement blocks; Sinaiticus in 1:1-8:38")
    path = os.path.join(OUTPUTS_DIR, 'supplementary_checks.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            sup = json.load(f)
        # Table 4 (d within each class with interval and p) and the split
        # halves of the typology (§ 5.5), both from supplementary_checks.py
        out['within_class'] = sup.get('within_class_d', {})
        out['typology_split_half'] = sup.get('typology_split_half', {})
        out['content_vs_random'] = sup.get('content_vs_random_masking', {})
        print("  [OK] supplementary checks")
    out['split_half'] = {}
    for tag, label in (('B', 'B'), ('A', 'A'), ('aleph', 'ℵ')):
        pairs = os.path.join(OUTPUTS_DIR, f'split_half_pairs_{tag}.csv')
        cents = os.path.join(OUTPUTS_DIR, f'split_half_centroids_{tag}.csv')
        if not (os.path.exists(pairs) and os.path.exists(cents)):
            continue
        rows = read_csv(cents)
        labels = [k for k in rows[0].keys() if k]
        out['split_half'][label] = {
            'pairs': [{'pair': r['pair'], 'odd': float(r['odd_distance']),
                       'even': float(r['even_distance'])} for r in read_csv(pairs)],
            'matrix': {'labels': labels,
                       'rows': [[float(r[c]) for c in labels] for r in rows]},
        }
        print(f"  [OK] split-half geometry, baseline {label}")
    write_js(os.path.join(DATA_DEST, 'article_checks.js'), 'DATA_ARTICLE', out)
    return out


def build_type_counts():
    """Build type_counts.js from type_counts_full_B.csv (the array used by the
    chart) and type_counts_all.js with every configuration."""
    data = None
    all_configs = {}
    for tag in DATA_FILES:
        path = os.path.join(OUTPUTS_DIR, f'type_counts_full_{tag}.csv')
        if not os.path.exists(path):
            continue
        rows = []
        for r in read_csv(path):
            entry = {'manuscript': r['manuscript']}
            for k, v in r.items():
                if k != 'manuscript':
                    try:
                        entry[k] = int(v)
                    except ValueError:
                        entry[k] = v
            rows.append(entry)
        all_configs[tag] = rows
        if tag == 'B':
            data = rows
    write_js(os.path.join(DATA_DEST, 'type_counts.js'), 'DATA_TYPES', data or [])
    write_js(os.path.join(DATA_DEST, 'type_counts_all.js'), 'DATA_TYPES_ALL', all_configs)
    return data


def build_cumulative_ari():
    """Build cumulative_ari.js from cumulative_analysis CSVs."""
    baselines = {
        'Baseline B': 'cumulative_analysis_B.csv',
        'Baseline A': 'cumulative_analysis_A.csv',
        'Baseline ℵ': 'cumulative_analysis_aleph.csv',
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
    """Build variants_sample.js: ~2000 rows stratified by baseline, manuscript & type."""
    variants_files = {
        'B': os.path.join(DATA_SRC_DIR, 'variants_full_john_B.csv'),
        'A': os.path.join(DATA_SRC_DIR, 'variants_full_john_A.csv'),
        'ℵ': os.path.join(DATA_SRC_DIR, 'variants_full_john_aleph.csv'),
    }
    all_variants = []
    for baseline, path in variants_files.items():
        if os.path.exists(path):
            rows = read_csv(path)
            for r in rows:
                r['baseline'] = baseline
                all_variants.append(r)
            print(f"  [OK] {baseline}: {len(rows)} rows loaded")

    if not all_variants:
        print("  [!!] No variant data found!")
        return []

    random.seed(42)
    target_n = 2000
    strata = {}
    for v in all_variants:
        key = (v['baseline'], v.get('manuscript', ''), v.get('type', ''))
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

    def verse_number(ref):
        m = re.search(r'(\d+):(\d+)', ref or '')
        return int(m.group(2)) if m else 0

    clean = []
    for v in sample:
        clean.append({
            'baseline': v['baseline'],
            'chapter': int(v.get('chapter') or 0),
            'verse': v.get('verse', ''),
            'verse_no': verse_number(v.get('verse', '')),
            'manuscript': 'ℵ' if v.get('manuscript') == 'aleph' else v.get('manuscript', ''),
            'base_reading': v.get('base_reading', ''),
            'ms_reading': v.get('ms_reading', ''),
            'type': v.get('type', ''),
        })

    clean.sort(key=lambda x: (x['chapter'], x['verse_no'], x['baseline'], x['manuscript']))

    write_js(os.path.join(DATA_DEST, 'variants_sample.js'), 'DATA_VARIANTS', clean)
    print(f"  ({len(clean)} rows)")
    return clean


def copy_images():
    """Copy the figures the website shows from outputs/ to img/ and remove any
    other PNG from img/ (all figures remain in outputs/)."""
    count = 0
    for fname in SITE_IMAGES:
        src = os.path.join(OUTPUTS_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(IMG_DEST, fname))
            count += 1
        else:
            print(f"  [!!] {fname} not found in outputs/")
    removed = 0
    for fname in os.listdir(IMG_DEST):
        if fname.endswith('.png') and fname not in SITE_IMAGES:
            os.remove(os.path.join(IMG_DEST, fname))
            removed += 1
    print(f"  -> Copied {count} PNG files to img/, removed {removed} not shown on the site")


def main():
    print("=== Preparing website data ===\n")
    ensure_dirs()

    print("[1/8] Building stats_summary.js...")
    build_stats_summary()

    print("\n[2/8] Building article_checks.js...")
    build_article_checks()

    print("\n[3/8] Building type_counts.js...")
    build_type_counts()

    print("\n[4/8] Building cumulative_ari.js...")
    build_cumulative_ari()

    print("\n[5/8] Building chapter_stability.js...")
    build_chapter_stability()

    print("\n[6/8] Building coverage.js...")
    build_coverage()

    print("\n[7/8] Building variants_sample.js (~2000 rows)...")
    build_variants_sample()

    print("\n[8/8] Copying PNG figures...")
    copy_images()

    print("\n=== Done! ===")


if __name__ == '__main__':
    main()
