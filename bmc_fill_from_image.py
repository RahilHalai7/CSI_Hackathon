#!/usr/bin/env python3
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

import google.generativeai as genai
from google.cloud import vision
from PIL import Image as PILImage

from bmc_image import generate_bmc_png


BMC_KEYS = [
    "Customer Segments",
    "Value Propositions",
    "Channels",
    "Customer Relationships",
    "Revenue Streams",
    "Key Activities",
    "Key Resources",
    "Key Partners",
    "Cost Structure",
]


def choose_model() -> str:
    preferred = (
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
    )
    try:
        models = list(genai.list_models())
        supported = [
            m.name for m in models
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        flash = [n for n in supported if "flash" in n and "exp" not in n]
        if flash:
            return flash[0]
        pro = [n for n in supported if "pro" in n and "exp" not in n]
        if pro:
            return pro[0]
        for pref in preferred:
            for name in supported:
                if pref in name:
                    return name
        if supported:
            return supported[0]
    except Exception:
        pass
    return preferred[0]


def ocr_extract(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")
    return response.full_text_annotation.text if response.full_text_annotation else ""


def preprocess_text(raw: str) -> str:
    if not raw.strip():
        return ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    text = re.sub(r"\s+", " ", " ".join(lines))
    return text.strip()


def prompt_json_bmc(source_text: str) -> str:
    instructions = {
        "instructions": "Return strict JSON for the 9 Business Model Canvas blocks.",
        "format": {
            "Customer Segments": ["..."],
            "Value Propositions": ["..."],
            "Channels": ["..."],
            "Customer Relationships": ["..."],
            "Revenue Streams": ["..."],
            "Key Activities": ["..."],
            "Key Resources": ["..."],
            "Key Partners": ["..."],
            "Cost Structure": ["..."]
        },
        "rules": [
            "Use concise bullets (max 7 per block).",
            "Infer missing details reasonably based on context.",
            "Return ONLY JSON, no prose.",
        ],
        "source": source_text,
    }
    return json.dumps(instructions, ensure_ascii=False)


def generate_bmc_dict(source_text: str) -> Dict[str, List[str]]:
    if load_dotenv:
        load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    data: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}

    if not api_key:
        return data

    genai.configure(api_key=api_key)
    model_name = choose_model()
    model = genai.GenerativeModel(model_name)
    prompt = prompt_json_bmc(source_text)
    try:
        resp = model.generate_content(prompt)
        txt = resp.text or "{}"
        # Extract JSON object using a simple brace capture if needed
        m = re.search(r"\{[\s\S]*\}", txt)
        payload = m.group(0) if m else txt
        parsed = json.loads(payload)
        # Normalize
        out: Dict[str, List[str]] = {}
        for key in BMC_KEYS:
            v = parsed.get(key, [])
            if isinstance(v, str):
                out[key] = [v]
            elif isinstance(v, list):
                out[key] = [str(i).strip() for i in v if str(i).strip()]
            else:
                out[key] = []
        return out
    except Exception:
        return data


def heuristic_parse_bmc(raw_text: str) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    current: Optional[str] = None
    # Build patterns allowing optional colon and case-insensitive
    patterns = {k: re.compile(rf"\b{re.escape(k)}\b:?", re.IGNORECASE) for k in BMC_KEYS}
    for line in raw_text.splitlines():
        s = line.strip()
        if not s:
            continue
        found = None
        for k, p in patterns.items():
            if p.search(s):
                found = k
                break
        if found:
            current = found
            continue
        if current:
            # remove common bullet markers
            s = re.sub(r"^[\-•\*\d\.\)]+\s*", "", s)
            buckets[current].append(s)
    return buckets


def generate_bmc_dict_from_image(image_path: str) -> Dict[str, List[str]]:
    if load_dotenv:
        load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    data: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    if not api_key:
        return data
    genai.configure(api_key=api_key)
    model_name = choose_model()
    model = genai.GenerativeModel(model_name)
    try:
        img = PILImage.open(image_path)
        prompt = (
            "Analyze this image of a Business Model Canvas. Read all legible text "
            "inside each block and return STRICT JSON with these keys: "
            + ", ".join(BMC_KEYS) + 
            ". Each key maps to a list of concise bullet strings. Return ONLY JSON."
        )
        resp = model.generate_content([prompt, img])
        txt = resp.text or "{}"
        m = re.search(r"\{[\s\S]*\}", txt)
        payload = m.group(0) if m else txt
        parsed = json.loads(payload)
        out: Dict[str, List[str]] = {}
        for key in BMC_KEYS:
            v = parsed.get(key, [])
            if isinstance(v, str):
                out[key] = [v]
            elif isinstance(v, list):
                out[key] = [str(i).strip() for i in v if str(i).strip()]
            else:
                out[key] = []
        return out
    except Exception:
        return data


def fill_bmc_from_image(image_path: str, output_png: str, title: str) -> Dict[str, List[str]]:
    print(f"📸 Using image: {image_path}")
    try:
        raw = ocr_extract(image_path)
        clean = preprocess_text(raw)
        print("🔍 OCR extracted characters:", len(clean))
        # Try AI JSON generation from text
        bmc = generate_bmc_dict(clean)
    except Exception as e:
        print(f"⚠️ OCR unavailable ({e}). Falling back to AI image analysis.")
        bmc = generate_bmc_dict_from_image(image_path)
    # Fallback to heuristic parsing if empty
    if not any(bmc[k] for k in BMC_KEYS):
        try:
            raw2 = ocr_extract(image_path)
        except Exception:
            raw2 = ""
        bmc = heuristic_parse_bmc(raw2)
    # Render PNG
    generate_bmc_png(output_png, title, bmc)
    return bmc


def main():
    parser = argparse.ArgumentParser(description="Auto-fill BMC from image via OCR + Gemini, then render PNG")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--output", default=str(Path("images") / "bmc_filled.png"), help="Output PNG path")
    parser.add_argument("--title", default="Business Model Canvas", help="Title for the canvas")
    args = parser.parse_args()

    data = fill_bmc_from_image(args.image, args.output, args.title)
    print("\nSections filled:")
    for k in BMC_KEYS:
        items = data.get(k, [])
        print(f"- {k}: {len(items)} items")
        for it in items[:5]:
            print(f"  • {it}")
    # Save JSON snapshot alongside PNG
    try:
        meta_path = Path(args.output).with_suffix("")
        json_path = Path(str(meta_path) + "_data.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n📝 Saved structured data: {json_path}")
    except Exception:
        pass
    print(f"\n✅ Output image: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())