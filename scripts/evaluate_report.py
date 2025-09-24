#!/usr/bin/env python3
"""
批量评估汇总：
针对多个模型输出目录，调用 evaluate_quality 比较参考与生成目录，汇总为 JSON/CSV。
"""

from pathlib import Path
import argparse
import json
import csv
from evaluate_quality import compare_dirs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pairs', nargs='+', required=True, help='一组 ref=... gen=... 形式的对，如 ref=outputs/a/model.1024 gen=outputs/b/textures_ai')
    ap.add_argument('--out-json', default='reports/quality_report.json')
    ap.add_argument('--out-csv', default='reports/quality_report.csv')
    args = ap.parse_args()

    results = []
    for pair in args.pairs:
        kv = dict(s.split('=') for s in pair.split()) if ' ' in pair else dict(s.split('=') for s in pair.split(',')) if ',' in pair else dict(s.split('=') for s in pair.split(';')) if ';' in pair else dict(s.split('=') for s in pair.split(','))
        ref = Path(kv.get('ref',''))
        gen = Path(kv.get('gen',''))
        stat = compare_dirs(ref, gen)
        results.append({'ref': str(ref), 'gen': str(gen), **stat})

    outj = Path(args.out_json)
    outj.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps({'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')

    outc = Path(args.out_csv)
    with outc.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['ref','gen','count','psnr','ssim'])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f'JSON: {outj}\nCSV: {outc}')


if __name__ == '__main__':
    main()


