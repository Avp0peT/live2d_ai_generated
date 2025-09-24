#!/usr/bin/env python3
"""
几何变形占位：
为后续在 Editor 中应用的几何变形生成 delta 文件（示意）。
当前：收集目标模型的关键参数ID，并生成一个空的 geometry_delta.json 框架。
"""

from pathlib import Path
import json
import argparse


def extract_param_ids(model_dir: Path):
    model3 = list(model_dir.glob('*.model3.json'))
    if not model3:
        return []
    m = json.loads(model3[0].read_text(encoding='utf-8'))
    params = []
    for g in m.get('Groups', []):
        if g.get('Target') == 'Parameter':
            params.extend(g.get('Ids', []))
    return sorted(set(params))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model_dir')
    ap.add_argument('--out', default='outputs/geometry_delta.json')
    args = ap.parse_args()
    ids = extract_param_ids(Path(args.model_dir))
    delta = {
        "version": 1,
        "target_model": args.model_dir,
        "parameters": ids,
        "artmesh_deltas": [],  # 未来填入顶点偏移或控制点变更
        "deformer_deltas": []  # 未来填入弯曲/旋转变形器变更
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"已写入 {out}")


if __name__ == '__main__':
    main()


