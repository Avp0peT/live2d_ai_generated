#!/usr/bin/env python3
"""
程序化生成 Live2D .motion3.json 的简易工具
支持：
- idle/呼吸（循环缓慢起伏）
- 点头/摇头（短促缓动）
- 眨眼（稀疏脉冲）

输出符合 Cubism Motion3 结构的 JSON。
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import math
import argparse


def bezier_segments_from_keypoints(points: List[tuple]) -> List[float]:
    """用线性片段编码Segments（1, t, v），起点为(t0,v0)。这里简化为线性段。"""
    if not points:
        return []
    seg: List[float] = [float(points[0][0]), float(points[0][1])]
    for t, v in points[1:]:
        seg.extend([1.0, float(t), float(v)])
    return seg


def generate_idle(duration: float, fps: float = 30.0) -> List[Dict[str, Any]]:
    """生成呼吸/idle曲线（Angle/Body微幅摆动、眼睑轻动）。"""
    curves = []
    # AngleX/Y/Z 小幅度正弦
    for pid, amp in [("ParamAngleX", 5.0), ("ParamAngleY", 3.0), ("ParamAngleZ", 2.0)]:
        keypoints = []
        num = int(duration * fps)
        for i in range(num + 1):
            t = i / fps
            v = amp * math.sin(2 * math.pi * t / duration)
            keypoints.append((t, v))
        curves.append({"Target": "Parameter", "Id": pid, "Segments": bezier_segments_from_keypoints(keypoints)})

    # EyeLOpen/EyeROpen 轻微变化
    for pid in ("ParamEyeLOpen", "ParamEyeROpen"):
        points = [(0.0, 1.0), (duration * 0.5, 0.9), (duration, 1.0)]
        curves.append({"Target": "Parameter", "Id": pid, "Segments": bezier_segments_from_keypoints(points)})
    return curves


def generate_nod(duration: float) -> List[Dict[str, Any]]:
    """点头：AngleX/AngleY/AngleZ 的短期摆动。"""
    curves = []
    points = [(0.0, 0.0), (duration * 0.25, -10.0), (duration * 0.5, 0.0), (duration * 0.75, 6.0), (duration, 0.0)]
    for pid in ("ParamAngleX", "ParamAngleY", "ParamAngleZ"):
        curves.append({"Target": "Parameter", "Id": pid, "Segments": bezier_segments_from_keypoints(points)})
    return curves


def generate_blink(duration: float, repeats: int = 2) -> List[Dict[str, Any]]:
    """眨眼：在duration内做repeats次闭合。"""
    curves = []
    for pid in ("ParamEyeLOpen", "ParamEyeROpen"):
        seg_points: List[tuple] = [(0.0, 1.0)]
        for i in range(repeats):
            t0 = (i + 0.25) * duration / repeats
            seg_points.extend([(t0, 0.2), (t0 + duration * 0.05, 1.0)])
        seg_points.append((duration, 1.0))
        curves.append({"Target": "Parameter", "Id": pid, "Segments": bezier_segments_from_keypoints(seg_points)})
    return curves


def build_motion(curves: List[Dict[str, Any]], duration: float, fps: float, loop: bool) -> Dict[str, Any]:
    return {
        "Version": 3,
        "Meta": {
            "Duration": float(duration),
            "Fps": float(fps),
            "Loop": bool(loop),
            "AreBeziersRestricted": False,
            "CurveCount": len(curves),
        },
        "Curves": curves,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", help="输出文件路径，如 outputs/demo/mtn/auto_idle.motion3.json")
    ap.add_argument("type", choices=["idle", "nod", "blink"], help="动作类型")
    ap.add_argument("--duration", type=float, default=2.0)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()

    if args.type == "idle":
        curves = generate_idle(args.duration, args.fps)
    elif args.type == "nod":
        curves = generate_nod(args.duration)
    else:
        curves = generate_blink(args.duration)

    motion = build_motion(curves, args.duration, args.fps, args.loop)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(motion, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"生成动作: {out}")


if __name__ == "__main__":
    main()


