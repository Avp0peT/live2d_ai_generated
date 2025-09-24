"""
LoRA 训练脚手架（占位）：
提供最小参数与数据组织说明，实际训练需接入具体图像-图像LoRA训练流程。
当前实现：
- 读取 index.json，收集纹理路径，拆分train/val列表
- 输出一个manifest，供后续 LoRA 训练器使用
"""

from pathlib import Path
import json
import random
import argparse


def build_manifest(index_file: Path, out_file: Path, val_ratio: float = 0.05):
    data = json.loads(index_file.read_text(encoding="utf-8"))
    textures = []
    for m in data.get("models", []):
        base = Path(m["model_path"]) 
        for t in m.get("textures", []):
            p = base / t
            textures.append(str(p))
    random.shuffle(textures)
    n_val = max(1, int(len(textures) * val_ratio))
    val = textures[:n_val]
    train = textures[n_val:]
    manifest = {"train": train, "val": val}
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="data/processed/index.json")
    ap.add_argument("--out", default="experiments/lora_texture_manifest.json")
    ap.add_argument("--val-ratio", type=float, default=0.05)
    args = ap.parse_args()

    manifest = build_manifest(Path(args.index), Path(args.out), args.val_ratio)
    print(json.dumps({"summary": {k: len(v) for k, v in manifest.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


