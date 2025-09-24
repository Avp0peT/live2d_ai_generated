#!/usr/bin/env python3
"""
参数ID映射工具：
在不同模型之间建立参数ID映射（如不同命名规范），并输出统一后的映射表，便于动作/表情迁移。
"""

import json
from pathlib import Path
import argparse


def load_index(index_path: Path):
    return json.loads(index_path.read_text(encoding="utf-8"))


def retarget_map(src_params, dst_params):
    # 简单策略：大小写不敏感匹配 + 常用别名
    aliases = {
        "PARAMEYELOPEN": ["PARAMEYELOPEN", "PARAMEYE_L_OPEN", "PARAMEYELEFTOPEN", "PARAMEYELOPEN"],
        "PARAMEYEROPEN": ["PARAMEYEROPEN", "PARAMEYE_R_OPEN", "PARAMEYERIGHTOPEN", "PARAMEYEROPEN"],
        "PARAMMOUTHOPENY": ["PARAMMOUTHOPENY", "PARAM_MOUTH_OPEN_Y"],
        "PARAMANGLEX": ["PARAMANGLEX", "PARAM_ANGLE_X"],
        "PARAMANGLEY": ["PARAMANGLEY", "PARAM_ANGLE_Y"],
        "PARAMANGLEZ": ["PARAMANGLEZ", "PARAM_ANGLE_Z"],
    }
    dst_norm = {p.upper(): p for p in dst_params}

    mapping = {}
    for sp in src_params:
        key = sp.upper()
        # 直接匹配
        if key in dst_norm:
            mapping[sp] = dst_norm[key]
            continue
        # 别名匹配
        found = None
        for canon, variations in aliases.items():
            if key == canon or key in variations:
                for v in [canon] + variations:
                    if v in dst_norm:
                        found = dst_norm[v]
                        break
            if found:
                break
        if found:
            mapping[sp] = found
    return mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_model_dir")
    ap.add_argument("dst_model_dir")
    ap.add_argument("--out", default="data/processed/retarget_map.json")
    args = ap.parse_args()

    src = Path(args.src_model_dir)
    dst = Path(args.dst_model_dir)
    # 读取两个模型的参数ID（从 model3.json 的 Groups 或从任一 motion 曲线提取）
    def extract_params(model_dir: Path):
        model3 = list(model_dir.glob("*.model3.json"))[0]
        m = json.loads(model3.read_text(encoding="utf-8"))
        params = set()
        for g in m.get("Groups", []):
            if g.get("Target") == "Parameter":
                params.update(g.get("Ids", []))
        return sorted(list(params))

    src_params = extract_params(src)
    dst_params = extract_params(dst)
    mapping = retarget_map(src_params, dst_params)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"src": str(src), "dst": str(dst), "mapping": mapping}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成参数映射: {out}")


if __name__ == "__main__":
    main()


