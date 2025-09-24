#!/usr/bin/env python3
"""
程序化生成 physics3.json（占位）：
从模板 physics3.json 读取结构，微调部分参数（如输出、回弹等），用于占位AI物理生成。
"""

import json
from pathlib import Path
import argparse


def tweak_physics(template: Path, out: Path, scale: float = 1.0):
    data = json.loads(template.read_text(encoding="utf-8"))
    # 简单策略：对 EffectiveMass/Delay/Output/Particles 等字段做轻微缩放
    def _scale(v):
        try:
            return float(v) * scale
        except Exception:
            return v

    for setting in data.get("PhysicsSettings", []):
        for output in setting.get("Outputs", []):
            for k in ("Scale", "Weight", "Reflect" ):
                if k in output and isinstance(output[k], (float, int)):
                    output[k] = _scale(output[k])
        for particle in setting.get("Particles", []):
            for k in ("Mobility", "Delay", "Acceleration", "Radius"):
                if k in particle and isinstance(particle[k], (float, int)):
                    particle[k] = _scale(particle[k])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template", help="模板 physics3.json")
    ap.add_argument("output", help="输出 physics3.json")
    ap.add_argument("--scale", type=float, default=1.05)
    args = ap.parse_args()

    tweak_physics(Path(args.template), Path(args.output), args.scale)
    print(f"生成物理: {args.output}")


if __name__ == "__main__":
    main()


