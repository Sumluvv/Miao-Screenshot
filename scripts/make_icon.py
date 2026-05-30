# -*- coding: utf-8 -*-
"""生成 assets/icon.png 与 icon.ico（打包用）"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 8
    d.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=size // 6,
        fill=(37, 99, 235, 255),
    )
    # 左右分屏示意
    mid = size // 2
    gap = max(2, size // 24)
    d.rectangle([pad * 2, pad * 2, mid - gap, size - pad * 2], fill=(255, 255, 255, 230))
    d.rectangle([mid + gap, pad * 2, size - pad * 2, size - pad * 2], fill=(255, 255, 255, 180))
  # 相机小圆
    cx, cy = size // 2, size - pad * 3
    r = size // 10
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 165, 233, 255))
    return img


def main():
    png = ASSETS / "icon.png"
    ico = ASSETS / "icon.ico"
    sizes = [256, 128, 64, 48, 32, 16]
    master = draw_icon(256)
    master.save(png)
    master.save(ico, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"已生成: {png}")
    print(f"已生成: {ico}")


if __name__ == "__main__":
    main()
