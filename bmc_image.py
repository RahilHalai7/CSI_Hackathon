#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def load_data(data_file: str | None) -> dict:
    default = {
        "Key Partners": [],
        "Key Activities": [],
        "Key Resources": [],
        "Value Propositions": [],
        "Customer Relationships": [],
        "Channels": [],
        "Customer Segments": [],
        "Cost Structure": [],
        "Revenue Streams": [],
    }
    if not data_file:
        return default
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for k in default.keys():
            v = loaded.get(k, [])
            if isinstance(v, str):
                default[k] = [v]
            elif isinstance(v, list):
                default[k] = v
    except Exception:
        pass
    return default


def wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_block(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, items: list[str], fill: tuple, font_title: ImageFont.ImageFont, font_text: ImageFont.ImageFont):
    # rectangle
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=(0, 0, 0), width=2)
    # title
    pad = 8
    title_lines = wrap_text(title, draw, font_title, w - 2 * pad)
    ty = y + pad
    for line in title_lines:
        draw.text((x + pad, ty), line, fill=(0, 0, 0), font=font_title)
        ty += font_title.size + 2
    # items as bullets
    if items:
        ty += 4
        for item in items:
            bullet = f"• {item}"
            for l in wrap_text(bullet, draw, font_text, w - 2 * pad):
                draw.text((x + pad, ty), l, fill=(0, 0, 0), font=font_text)
                ty += font_text.size + 2


def generate_bmc_png(output_path: str, title: str, data: dict):
    # Canvas size similar to draw.io layout
    width, height = 1200, 560
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

    # Title banner
    tbw, tbh = 300, 20
    draw.text(((width - tbw) // 2, 5), title, fill=(0, 0, 0), font=font_title)

    # Positions (same as bmc_drawio.py with slight height adjustment)
    positions = {
        "Key Partners": (0, 30, 200, 330),
        "Key Activities": (200, 30, 200, 160),
        "Key Resources": (200, 190, 200, 170),
        "Value Propositions": (400, 30, 300, 330),
        "Customer Relationships": (700, 30, 250, 160),
        "Channels": (700, 190, 250, 170),
        "Customer Segments": (950, 30, 250, 330),
        "Cost Structure": (0, 360, 700, 190),
        "Revenue Streams": (700, 360, 500, 190),
    }

    fills = {
        "Key Partners": (218, 232, 252),
        "Key Activities": (255, 242, 204),
        "Key Resources": (248, 206, 204),
        "Value Propositions": (213, 232, 212),
        "Customer Relationships": (225, 213, 231),
        "Channels": (245, 245, 245),
        "Customer Segments": (255, 230, 204),
        "Cost Structure": (226, 242, 255),
        "Revenue Streams": (255, 218, 218),
    }

    for key, (x, y, w, h) in positions.items():
        items = data.get(key, [])
        if isinstance(items, str):
            items = [items]
        draw_block(draw, x, y, w, h, key, items, fills[key], font_title, font_text)

    # Save
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")

    print(f"✅ BMC image generated: {out}")


def main():
    parser = argparse.ArgumentParser(description="Generate a Business Model Canvas image (PNG)")
    parser.add_argument("--output", default=str(Path("images") / "bmc_generated.png"), help="Output PNG path")
    parser.add_argument("--title", default="Business Model Canvas", help="Title text")
    parser.add_argument("--data-file", default=None, help="JSON file with BMC block content")
    args = parser.parse_args()

    data = load_data(args.data_file)
    generate_bmc_png(args.output, args.title, data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())