"""
Translate TXT files from Hindi, Marathi, or Odia to English using LibreTranslate.

Default output directory: translated/

Usage examples:
- Single file (auto-detect language):
  python translate_txt.py --input "pdf_text/Audio_Hindi_sample2_google_stt_20250928_020956.txt"

- Explicit source language:
  python translate_txt.py --input "pdf_text/Audio_Marathi_sample1_google_stt_20250928_011815.txt" --source mr

- Custom endpoint and output:
  python translate_txt.py --input "pdf_text/Audio_Odia_sample2_google_stt_20250928_021349.txt" --source or --api-url https://libretranslate.com --output "translated/odia_to_english.txt"

Environment variables:
- LIBRETRANSLATE_URL (default: https://libretranslate.com)
- LIBRETRANSLATE_API_KEY (optional; if your instance requires a key)
"""

import argparse
import os
import sys
import json
import time
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Optional fallback translator (free, public API)
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator  # type: ignore
    _FALLBACK_AVAILABLE = True
except Exception:
    _FALLBACK_AVAILABLE = False


def _normalize_lang_code(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return None
    lang = lang.strip().lower()
    mapping = {
        "english": "en",
        "hindi": "hi",
        "marathi": "mr",
        "odia": "or",
        # direct short codes
        "en": "en",
        "hi": "hi",
        "mr": "mr",
        "or": "or",
    }
    return mapping.get(lang, lang)


def _http_post_json(url: str, payload: dict, headers: Optional[dict] = None, retries: int = 2, backoff_sec: float = 1.0) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except (HTTPError, URLError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_sec * (attempt + 1))
            else:
                raise
    # should not reach
    raise last_err or RuntimeError("Unknown HTTP error")


def detect_language(api_url: str, text: str, api_key: Optional[str]) -> Optional[str]:
    # Use a sample of the text to avoid heavy payload for detection
    sample = text[:2000]
    payload = {"q": sample}
    if api_key:
        payload["api_key"] = api_key
    try:
        result = _http_post_json(api_url.rstrip("/") + "/detect", payload)
        # result is a list of {language, confidence}
        if isinstance(result, list) and result:
            best = max(result, key=lambda r: r.get("confidence", 0))
            return best.get("language")
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}")
    return None


def split_into_chunks(text: str, max_chars: int = 4500) -> List[str]:
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    # Prefer splitting on line boundaries
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            line = "\n"  # keep paragraph breaks
        if current_len + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def translate_text(api_url: str, text: str, source: Optional[str], target: str, api_key: Optional[str]) -> str:
    payload = {
        "q": text,
        "source": source or "auto",
        "target": target,
        "format": "text",
    }
    if api_key:
        payload["api_key"] = api_key
    try:
        result = _http_post_json(api_url.rstrip("/") + "/translate", payload)
        translated = result.get("translatedText") if isinstance(result, dict) else None
        if not translated:
            raise RuntimeError(f"Unexpected translation response: {result}")
        return translated
    except Exception as e:
        # Fallback path using MyMemory if available
        if _FALLBACK_AVAILABLE:
            # Try Google first (often more reliable); then MyMemory
            try:
                src = (source or "auto")
                if src == "auto":
                    gt = GoogleTranslator(target=target)
                else:
                    gt = GoogleTranslator(source=src, target=target)
                return gt.translate(text)
            except Exception as ge:
                try:
                    src = (source or "auto")
                    mm = MyMemoryTranslator(source=src, target=target)
                    return mm.translate(text)
                except Exception as me:
                    raise RuntimeError(
                        f"Primary and both fallbacks failed: {e} | Google: {ge} | MyMemory: {me}"
                    )
        raise


def _split_speaker_prefix(line: str) -> tuple[str, str]:
    """Return (prefix, content) if line starts with a speaker label like
    'Person:' or 'Person 2:' else ('', line). Preserves original spacing after colon.
    """
    m = re.match(r"^(\s*Person(?:\s+\d+)?\s*:\s*)(.*)$", line)
    if m:
        return m.group(1), m.group(2)
    return "", line


def build_default_output(input_path: str) -> Path:
    out_dir = Path("translated")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(input_path).stem
    return out_dir / f"{base}_translated_en_{ts}.txt"


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate a TXT file to English using LibreTranslate")
    parser.add_argument("--input", required=True, help="Path to input .txt file")
    parser.add_argument("--source", help="Source language code or name (hi/mr/or or 'auto')", default=None)
    parser.add_argument("--target", help="Target language code", default="en")
    parser.add_argument("--api-url", help="LibreTranslate base URL", default=os.getenv("LIBRETRANSLATE_URL", "https://libretranslate.com"))
    parser.add_argument("--api-key", help="LibreTranslate API key (optional)", default=os.getenv("LIBRETRANSLATE_API_KEY"))
    parser.add_argument("--output", help="Optional output path for translated text")
    parser.add_argument("--max-chars", type=int, default=4500, help="Max characters per request chunk")
    parser.add_argument("--line-by-line", action="store_true", help="Translate line-by-line to preserve formatting and speaker labels")
    parser.add_argument("--preserve-speaker-labels", action="store_true", help="When line-by-line, keep 'Person:' labels intact")
    parser.add_argument("--style", choices=["default", "diarized"], default="default", help="Preset output style; 'diarized' implies line-by-line with speaker labels")
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"❌ Input file not found: {input_path}")
        return 1

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read input: {e}")
        return 1

    source_norm = _normalize_lang_code(args.source)
    if not source_norm or source_norm == "auto":
        detected = detect_language(args.api_url, content, args.api_key)
        source_lang = detected or "auto"
        print(f"🌐 Source language: {source_lang}")
    else:
        source_lang = source_norm
        print(f"🌐 Source language (specified): {source_lang}")

    # Style presets
    style = getattr(args, "style", "default")
    line_by_line = (getattr(args, "line_by_line", False) or style == "diarized")
    preserve_labels = (getattr(args, "preserve_speaker_labels", False) or style == "diarized")
    if line_by_line:
        # Translate each line to preserve formatting and optional speaker labels
        lines = content.splitlines()
        translated_lines: List[str] = []
        for idx, line in enumerate(lines, start=1):
            if not line.strip():
                translated_lines.append("")
                continue
            prefix = ""
            core = line
            if preserve_labels:
                prefix, core = _split_speaker_prefix(line)
            try:
                translated_core = translate_text(args.api_url, core, source_lang, args.target, args.api_key)
            except Exception as e:
                print(f"❌ Translation failed on line {idx}: {e}")
                return 1
            translated_lines.append(f"{prefix}{translated_core}".strip())
        output_text = "\n".join(translated_lines)
    else:
        chunks = split_into_chunks(content, max_chars=args.max_chars)
        translated_parts: List[str] = []
        for i, chunk in enumerate(chunks, start=1):
            print(f"🔁 Translating chunk {i}/{len(chunks)} (len={len(chunk)})...")
            try:
                translated = translate_text(args.api_url, chunk, source_lang, args.target, args.api_key)
                translated_parts.append(translated)
            except Exception as e:
                print(f"❌ Translation failed on chunk {i}: {e}")
                return 1
        output_text = "\n".join(part.strip() for part in translated_parts if part.strip())

    # Normalize whitespace while preserving line breaks
    output_text = "\n".join(s.strip() for s in output_text.splitlines())

    out_path = Path(args.output) if args.output else build_default_output(input_path)
    try:
        out_dir = out_path.parent
        if out_dir and not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"\n📝 Saved translated text to: {out_path}")
    except Exception as e:
        print(f"❌ Failed to write output: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())