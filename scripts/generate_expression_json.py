#!/usr/bin/env python3
"""
程序化生成 exp3.json 表情（占位）：
按照给定模板参数ID集合，生成若干静态表情（微笑、眨眼、惊讶等）。
"""

import json
from pathlib import Path
import argparse


def make_expression(params: dict) -> dict:
    return {
        "Type": "Live2D Expression",
        "FadeInTime": 0.3,
        "FadeOutTime": 0.3,
        "Parameters": [
            {"Id": pid, "Value": val, "Blend": blend}
            for pid, (val, blend) in params.items()
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output_dir", help="输出目录（exp/）")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 基础表情集合（可按需扩展/条件化）
    presets = {
        "auto_smile": {
            "ParamMouthForm": (1.0, "Add"),
            "ParamMouthOpenY": (0.2, "Add"),
            "ParamEyeLOpen": (1.0, "Multiply"),
            "ParamEyeROpen": (1.0, "Multiply"),
        },
        "auto_blink_soft": {
            "ParamEyeLOpen": (0.6, "Multiply"),
            "ParamEyeROpen": (0.6, "Multiply"),
        },
        "auto_surprised": {
            "ParamMouthOpenY": (1.0, "Add"),
            "ParamBrowLY": (-0.5, "Add"),
            "ParamBrowRY": (-0.5, "Add"),
        },
    }

    outputs = []
    for name, mapping in presets.items():
        data = make_expression(mapping)
        p = out_dir / f"{name}.exp3.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(p.name)

    print("\n".join(outputs))


if __name__ == "__main__":
    main()


