"""
动作模型训练占位：
提供曲线统计与简单序列样本抽取的骨架，便于后续替换为RNN/Transformer训练。
"""

from pathlib import Path
import json
from typing import Dict, List


def collect_motion_stats(index_file: Path) -> Dict:
    data = json.loads(index_file.read_text(encoding="utf-8"))
    counts = 0
    params = set()
    for m in data.get("models", []):
        motions = m.get("motions", {})
        base = Path(m["model_path"])
        for group in motions.values():
            if not isinstance(group, list):
                continue
            for item in group:
                f = item.get("File")
                if not f:
                    continue
                p = base / f
                try:
                    motion = json.loads(p.read_text(encoding="utf-8"))
                    for c in motion.get("Curves", []):
                        if c.get("Target") == "Parameter" and c.get("Id"):
                            params.add(c["Id"])
                    counts += 1
                except Exception:
                    pass
    return {"motion_files": counts, "unique_params": sorted(list(params))}


def sample_param_sequences(index_file: Path, target_params: List[str], seq_len: int = 60) -> List[Dict]:
    data = json.loads(index_file.read_text(encoding="utf-8"))
    samples: List[Dict] = []
    for m in data.get("models", []):
        base = Path(m["model_path"])
        motions = m.get("motions", {})
        for group in motions.values():
            if not isinstance(group, list):
                continue
            for item in group:
                f = item.get("File")
                if not f:
                    continue
                p = base / f
                try:
                    motion = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                curves = motion.get("Curves", [])
                # 建立 param -> timeline
                param_to_points = {tp: [] for tp in target_params}
                for c in curves:
                    if c.get("Target") == "Parameter" and c.get("Id") in param_to_points:
                        seg = c.get("Segments", [])
                        # 解析线性段 (简化)
                        if len(seg) >= 2:
                            t0, v0 = float(seg[0]), float(seg[1])
                            param_to_points[c["Id"]].append((t0, v0))
                        i = 2
                        while i + 2 < len(seg):
                            # [1, t, v]
                            if int(seg[i]) == 1:
                                t, v = float(seg[i+1]), float(seg[i+2])
                                param_to_points[c["Id"]].append((t, v))
                                i += 3
                            else:
                                break
                # 采样固定长度（插值省略）
                for tp in target_params:
                    pts = param_to_points.get(tp, [])
                    if len(pts) >= 2:
                        samples.append({"param": tp, "points": pts[:seq_len]})
    return samples


if __name__ == "__main__":
    import sys
    index = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/processed/index.json")
    stats = collect_motion_stats(index)
    seqs = sample_param_sequences(index, ["ParamAngleX", "ParamEyeLOpen"], seq_len=60)
    print(json.dumps({"stats": stats, "sample_sequences": seqs[:5]}, ensure_ascii=False, indent=2))


