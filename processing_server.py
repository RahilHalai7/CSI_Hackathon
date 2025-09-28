"""
Processing Server

Exposes a simple REST API to route submitted documents to the appropriate
Python processing script based on file type:
- Audio (wav/mp3/m4a) -> asr.py for speech-to-text
- PDF -> pdf_to_txt.py for text extraction and optional structuring

Run locally:
  uvicorn processing_server:app --host 127.0.0.1 --port 8000

POST /process
  JSON body: { "path": "<local_file_path>", "language": "en" }
  Returns: { "status": "ok", "type": "audio|pdf|unsupported", "output": "<txt path>", "message": "..." }
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Local script imports
import asr  # type: ignore
import pdf_to_txt  # type: ignore

app = FastAPI(title="CSI Hackathon Processing Server")

# Allow requests from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_audio(path: str) -> bool:
    return Path(path).suffix.lower() in {".wav", ".mp3", ".m4a", ".aac"}


def _is_pdf(path: str) -> bool:
    return Path(path).suffix.lower() == ".pdf"


def _save_text(output_dir: Path, base_name: str, text: str, suffix: str) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"{base_name}_{suffix}_{timestamp}.txt"
    out_path.write_text(text, encoding="utf-8")
    return str(out_path)


@app.get("/")
def health():
    return {"status": "ok", "message": "Processing server is running"}


@app.post("/process")
def process_document(payload: dict):
    path = payload.get("path")
    language: Optional[str] = payload.get("language")

    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="Valid 'path' to local file is required")

    try:
        if _is_audio(path):
            text, speaker_count = asr.transcribe_audio_google(path, language=language)
            output = _save_text(Path("pdf_text"), Path(path).stem, text, "google_stt")
            return {
                "status": "ok",
                "type": "audio",
                "output": output,
                "speaker_count": speaker_count,
                "message": "Audio processed via Google STT",
            }

        if _is_pdf(path):
            detector = pdf_to_txt.PDFTextDetector(use_gemini_structuring=True)
            # This will auto-save if auto_save=True and output_file is None
            structured_text = detector.process_pdf_text_detection(
                path,
                page_range=None,
                ocr_only=False,
                show_intermediate=False,
                output_file=None,
                structure_text=True,
                auto_save=True,
            )
            # If process_pdf_text_detection returns the text, ensure we save as well
            output = _save_text(Path("pdf_text"), Path(path).stem, structured_text, "extracted")
            return {
                "status": "ok",
                "type": "pdf",
                "output": output,
                "message": "PDF processed via OCR/Text and structured",
            }

        return {
            "status": "unsupported",
            "type": "unsupported",
            "message": "Only audio (wav/mp3/m4a) and PDF are supported",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")