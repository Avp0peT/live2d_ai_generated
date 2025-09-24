"""
动作推理占位：
调用程序化生成器生成基础 idle/nod/blink 动作，返回可并入的Motions结构。
"""

from pathlib import Path
import subprocess
import json
from typing import Dict, List
import os


def generate_basic_motions(out_dir: Path) -> Dict[str, List[Dict[str, str]]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    motions_dir = out_dir / "mtn"
    motions_dir.mkdir(parents=True, exist_ok=True)

    motion_map = {
        "Auto": [
            ("auto_idle", "idle", 3.0, True),
            ("auto_nod", "nod", 1.2, False),
            ("auto_blink", "blink", 2.0, True),
        ]
    }

    results: Dict[str, List[Dict[str, str]]] = {}
    for group, items in motion_map.items():
        group_list: List[Dict[str, str]] = []
        for name, mtype, duration, loop in items:
            target = motions_dir / f"{name}.motion3.json"
            cmd = [
                "python",
                str(Path(__file__).parent.parent / "scripts" / "generate_motion_json.py"),
                str(target),
                mtype,
                "--duration",
                str(duration),
            ]
            if loop:
                cmd.append("--loop")
            # 抑制子进程输出，避免污染上层stdout
            with open(os.devnull, 'wb') as devnull:
                subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
            group_list.append({"File": f"mtn/{name}.motion3.json", "Name": name})
        results[group] = group_list
    return results


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs/tmp")
    motions = generate_basic_motions(out)
    # 固定UTF-8字节输出，避免Windows控制台编码影响
    sys.stdout.buffer.write(json.dumps(motions, ensure_ascii=False, indent=2).encode('utf-8'))
    sys.stdout.buffer.flush()


