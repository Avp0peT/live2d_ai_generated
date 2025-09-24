#!/usr/bin/env python3
"""
质量评估（占位）：
计算两张图像的PSNR/SSIM，并可对目录对比输出平均值。
依赖：opencv-python, scikit-image
"""

from pathlib import Path
import argparse
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim


def compute_psnr(img1, img2):
    mse = np.mean((img1.astype(np.float32) - img2.astype(np.float32)) ** 2)
    if mse == 0:
        return 99.0
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))


def compute_ssim(img1, img2):
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return float(score)


def compare_dirs(ref_dir: Path, gen_dir: Path):
    ref_pngs = list(ref_dir.rglob('*.png'))
    if not ref_pngs:
        return {"count": 0, "psnr": 0.0, "ssim": 0.0}
    ps, ss = [], []
    for rp in ref_pngs:
        gp = gen_dir / rp.relative_to(ref_dir)
        if not gp.exists():
            continue
        rimg = cv2.imread(str(rp), cv2.IMREAD_COLOR)
        gimg = cv2.imread(str(gp), cv2.IMREAD_COLOR)
        if rimg is None or gimg is None or rimg.shape != gimg.shape:
            continue
        ps.append(compute_psnr(rimg, gimg))
        ss.append(compute_ssim(rimg, gimg))
    if not ps:
        return {"count": 0, "psnr": 0.0, "ssim": 0.0}
    return {"count": len(ps), "psnr": float(np.mean(ps)), "ssim": float(np.mean(ss))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True, help='参考目录')
    ap.add_argument('--gen', required=True, help='生成目录')
    args = ap.parse_args()
    stat = compare_dirs(Path(args.ref), Path(args.gen))
    print(stat)


if __name__ == '__main__':
    main()


