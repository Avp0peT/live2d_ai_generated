"""
AI纹理生成推理：
支持两种模式：
1) jitter（默认，占位）：亮度/饱和度微扰
2) diffusers：调用 Stable Diffusion/Diffusers img2img，并可加载 LoRA（若可用）
"""

from pathlib import Path
from typing import List
from PIL import Image, ImageEnhance
import random
import argparse
import os


def jitter_texture(src: Path, dst: Path, hue_delta: float = 0.0, sat: float = 1.1, bright: float = 1.05):
    img = Image.open(src).convert("RGBA")
    # 亮度
    img = ImageEnhance.Brightness(img).enhance(bright)
    # 饱和度
    img = ImageEnhance.Color(img).enhance(sat)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG")


def process_textures_jitter(src_textures: List[Path], out_dir: Path) -> List[str]:
    rels: List[str] = []
    for i, tex in enumerate(src_textures):
        rel = f"textures_ai/texture_{i:02d}.png"
        dst = out_dir / rel
        jitter_texture(tex, dst, sat=1.05 + random.uniform(-0.05, 0.1), bright=1.0 + random.uniform(-0.05, 0.1))
        rels.append(rel)
    return rels


def maybe_import_diffusers():
    try:
        from diffusers import StableDiffusionImg2ImgPipeline
        import torch
        return StableDiffusionImg2ImgPipeline, torch
    except Exception:
        return None, None


def process_textures_diffusers(src_textures: List[Path], out_dir: Path) -> List[str]:
    StableDiffusionImg2ImgPipeline, torch = maybe_import_diffusers()
    if StableDiffusionImg2ImgPipeline is None:
        raise RuntimeError("未安装 diffusers/torch，或不可用")

    model_id = os.environ.get("DIFFUSERS_MODEL_ID", "stabilityai/sd-turbo")
    prompt = os.environ.get("DIFFUSERS_PROMPT", "high quality texture, cel shading, clean edges")
    negative = os.environ.get("DIFFUSERS_NEGATIVE", "blurry, lowres, jpeg artifacts")
    strength = float(os.environ.get("DIFFUSERS_STRENGTH", "0.35"))
    guidance = float(os.environ.get("DIFFUSERS_GUIDANCE", "1.5"))
    steps = int(os.environ.get("DIFFUSERS_STEPS", "10"))
    device = "cuda" if torch.cuda.is_available() else "cpu"

    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if device=="cuda" else torch.float32)
    pipe = pipe.to(device)

    # 可选加载 LoRA（需 diffusers>=0.16）
    lora_path = os.environ.get("DIFFUSERS_LORA_PATH")
    if lora_path and Path(lora_path).exists():
        try:
            pipe.load_lora_weights(lora_path)
        except Exception:
            pass

    rels: List[str] = []
    for i, tex in enumerate(src_textures):
        init_image = Image.open(tex).convert("RGBA")
        # 将 alpha 作为蒙版，送入管线时转为RGB
        rgb = init_image.convert("RGB")
        result = pipe(
            prompt=prompt,
            image=rgb,
            negative_prompt=negative,
            strength=strength,
            guidance_scale=guidance,
            num_inference_steps=steps
        ).images[0]
        # 恢复 alpha：将生成图与原 alpha 合成
        result = result.convert("RGBA")
        result.putalpha(init_image.split()[-1])
        rel = f"textures_ai/texture_{i:02d}.png"
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        result.save(dst, "PNG")
        rels.append(rel)
    return rels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template-model-dir", required=True, help="模板模型目录，包含原纹理")
    ap.add_argument("--textures", nargs="*", required=True, help="相对路径的纹理列表，如 model.1024/texture_00.png ...")
    ap.add_argument("--out-dir", required=True, help="输出根目录（模型输出目录）")
    ap.add_argument("--backend", choices=["jitter", "diffusers"], default=os.environ.get("TEXTURE_BACKEND", "jitter"))
    args = ap.parse_args()

    base = Path(args.template_model_dir)
    srcs = [base / t for t in args.textures]
    out = Path(args.out_dir)
    if args.backend == "diffusers":
        rels = process_textures_diffusers(srcs, out)
    else:
        rels = process_textures_jitter(srcs, out)
    print("\n".join(rels))


if __name__ == "__main__":
    main()


