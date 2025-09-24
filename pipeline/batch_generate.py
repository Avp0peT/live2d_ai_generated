#!/usr/bin/env python3
"""
批量并行生成脚本：
- 从 data/processed/index.json 挑选前N个模板（可按过滤条件）
- 并行调用 generate_model.py 生成模型
"""

from pathlib import Path
import json
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_job(args_list):
    return subprocess.run(args_list, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="data/processed/index.json")
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--out-prefix", default="batch_ai_")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--texture-mode", default="ai_generated")
    ap.add_argument("--motion-mode", default="ai_generated")
    ap.add_argument("--expression-mode", default="ai_generated")
    ap.add_argument("--physics-mode", default="ai_generated")
    args = ap.parse_args()

    data = json.loads(Path(args.index).read_text(encoding="utf-8"))
    models = data.get("models", [])[: args.count]

    jobs = []
    for m in models:
        mid = m["model_id"]
        out_name = f"{args.out_prefix}{mid}"
        cmd = [
            "python",
            str(Path(__file__).parent / "generate_model.py"),
            "--output-name",
            out_name,
            "--template-strategy",
            "specified",
            "--template-id",
            mid,
            "--texture-mode",
            args.texture_mode,
            "--motion-mode",
            args.motion_mode,
            "--expression-mode",
            args.expression_mode,
            "--physics-mode",
            args.physics_mode,
        ]
        jobs.append(cmd)

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(run_job, j) for j in jobs]
        for fu in as_completed(futs):
            results.append(fu.result())

    ok = sum(1 for r in results if r.returncode == 0)
    fail = len(results) - ok
    print(f"完成批量生成：成功 {ok}，失败 {fail}")
    for r in results:
        if r.returncode != 0:
            print("--- 失败任务输出 ---")
            print(r.stderr)


if __name__ == "__main__":
    main()


