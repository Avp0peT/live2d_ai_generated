"""
纹理训练脚手架（占位）：
提供数据加载/增强/日志的骨架，便于后续替换为扩散/LoRA训练。
当前实现仅遍历 index.json 统计纹理分布并保存到 experiments/ 下。
"""

from pathlib import Path
import json
import argparse


def summarize_textures(index_file: Path) -> dict:
    data = json.loads(index_file.read_text(encoding="utf-8"))
    res_stats = {}
    count = 0
    for m in data.get("models", []):
        base = Path(m["model_path"])
        for t in m.get("textures", []):
            p = base / t
            try:
                from PIL import Image
                with Image.open(p) as img:
                    res = f"{img.width}x{img.height}"
                res_stats[res] = res_stats.get(res, 0) + 1
                count += 1
            except Exception:
                pass
    return {"total_textures": count, "resolutions": res_stats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="data/processed/index.json")
    ap.add_argument("--exp", default="experiments/texture_stats.json")
    args = ap.parse_args()

    stats = summarize_textures(Path(args.index))
    out = Path(args.exp)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


