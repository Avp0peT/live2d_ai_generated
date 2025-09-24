"""
数据集占位模块：
提供 Live2D 纹理切片与掩膜读取的骨架，供后续AI训练使用。
当前实现返回原始贴图路径列表，训练阶段由调用方读取。
"""

from pathlib import Path
from typing import List, Dict
import json


def load_texture_manifest(index_file: Path) -> List[Dict]:
    data = json.loads(index_file.read_text(encoding="utf-8"))
    textures: List[Dict] = []
    for m in data.get("models", []):
        base = Path(m["model_path"])  # 绝对或相对均可
        for tex in m.get("textures", []):
            textures.append({
                "model_id": m["model_id"],
                "path": str(base / tex)
            })
    return textures


