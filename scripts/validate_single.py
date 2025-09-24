#!/usr/bin/env python3
from pathlib import Path
import sys

# Ensure we can import from scripts directory
sys.path.append(str(Path(__file__).parent))

from validate_model import validate_single_model  # type: ignore


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/validate_single.py <model_dir>")
        sys.exit(1)
    model_dir = Path(sys.argv[1])
    result = validate_single_model(model_dir)
    print("\n=== 单模型验证结果 ===")
    print(f"模型: {result.model_id}")
    print(f"路径: {result.model_path}")
    print(f"是否有效: {result.is_valid}")
    print(f"错误数: {len(result.errors)}")
    print(f"警告数: {len(result.warnings)}")
    if not result.is_valid:
        print("\n前若干错误:")
        for err in result.errors[:10]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()


