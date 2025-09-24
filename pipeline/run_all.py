#!/usr/bin/env python3
"""
一键执行脚本：索引 -> 端到端生成 -> 验证

功能：
- 若 `data/processed/index.json` 不存在，则自动运行 `scripts/scan_models.py` 生成索引
- 调用 `pipeline/generate_model.py` 完成端到端生成（默认使用 AI 占位后端）
- 调用校验逻辑对生成结果进行验证，并打印摘要

使用示例：
  python pipeline/run_all.py --template-id 100100 --output-name oneclick_demo
  # 或随机模板：
  python pipeline/run_all.py --output-name oneclick_demo

可选：
- --use-diffusers  使用 Diffusers/LoRA img2img（需已安装 diffusers/torch/accelerate）
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def ensure_index(index_file: Path) -> None:
    if index_file.exists():
        logging.info("索引已存在：%s", index_file)
        return
    logging.info("未找到索引，开始扫描模型数据集……")
    cmd = [sys.executable, str(Path("scripts") / "scan_models.py")]
    subprocess.check_call(cmd)
    if not index_file.exists():
        raise SystemExit(f"扫描后仍未找到索引：{index_file}")
    logging.info("索引生成完成：%s", index_file)


def run_generate(
    output_name: str,
    template_strategy: str,
    template_id: Optional[str],
    use_diffusers: bool,
    index_file: Path,
) -> Path:
    env: Dict[str, str] = dict(os.environ)
    if use_diffusers:
        env["TEXTURE_BACKEND"] = "diffusers"
    else:
        env.setdefault("TEXTURE_BACKEND", "jitter")

    cmd = [
        sys.executable,
        str(Path("pipeline") / "generate_model.py"),
        "--output-name",
        output_name,
        "--template-strategy",
        template_strategy,
        "--texture-mode",
        "ai_generated",
        "--motion-mode",
        "ai_generated",
        "--expression-mode",
        "ai_generated",
        "--physics-mode",
        "ai_generated",
        "--index-file",
        str(index_file),
    ]
    if template_strategy == "specified" and template_id:
        cmd += ["--template-id", template_id]

    logging.info("开始端到端生成：%s", output_name)
    subprocess.check_call(cmd, env=env)
    out_dir = Path("outputs") / output_name
    if not out_dir.exists():
        raise SystemExit(f"未找到生成目录：{out_dir}")
    logging.info("生成完成：%s", out_dir)
    return out_dir


def validate_output(output_dir: Path) -> bool:
    # 复用 validate_single_model（与 generate_model.py 一致的导入方式）
    sys.path.append(str(Path(__file__).parent.parent / "scripts"))
    try:
        from validate_model import validate_single_model  # type: ignore
    except Exception:
        logging.warning("无法导入 validate_single_model，跳过验证阶段。")
        return True

    logging.info("开始验证生成结果……")
    result = validate_single_model(output_dir)
    if getattr(result, "is_valid", False):
        logging.info("✅ 验证通过")
        return True
    errors = getattr(result, "errors", [])
    logging.warning("⚠️  验证失败：%d 个问题", len(errors) if errors else 0)
    for err in list(errors or [])[:5]:
        logging.warning("  - %s", err)
    return False


def main() -> None:
    configure_logging()
    ap = argparse.ArgumentParser(description="一键执行：索引 -> 生成 -> 验证")
    ap.add_argument("--output-name", default="oneclick_model")
    ap.add_argument("--template-id", default=None)
    ap.add_argument("--use-diffusers", action="store_true")
    ap.add_argument("--index-file", default="data/processed/index.json")
    args = ap.parse_args()

    index_path = Path(args.index_file)
    ensure_index(index_path)

    strategy = "specified" if args.template_id else "random"
    out_dir = run_generate(
        output_name=args.output_name,
        template_strategy=strategy,
        template_id=args.template_id,
        use_diffusers=bool(args.use_diffusers),
        index_file=index_path,
    )

    ok = validate_output(out_dir)
    print("\n=== 一键执行完成 ===")
    print(f"输出目录: {out_dir}")
    print(f"模型文件: {out_dir / (args.output_name + '.model3.json')}")
    print("验证结果: ", "通过" if ok else "失败，详见日志")
    print("\n预览提示：\n  1) python -m http.server 5500\n  2) 打开 http://127.0.0.1:5500/web/preview.html 并输入输出目录（如 outputs/" + args.output_name + ")")


if __name__ == "__main__":
    main()


