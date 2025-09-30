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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import sqlite3
from typing import Dict, Any
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


# --- SQLite helpers ---
DB_PATH = str(Path("data") / "ocr.db")

def _ensure_db(db_path: str = DB_PATH) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # ideas table stores the raw submission and file metadata
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            language TEXT,
            file_path TEXT,
            file_url TEXT,
            entrepreneur_id TEXT,
            mentor_feedback TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )
    # ocr_texts table may already exist from pdf_to_txt.py
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ocr_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT,
            text_hash TEXT,
            text_content TEXT,
            created_at TEXT,
            language TEXT,
            title TEXT
        )
        """
    )
    # reports table stores the final evaluation/report from prompt.py
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER,
            ocr_id INTEGER,
            report_text TEXT,
            created_at TEXT,
            FOREIGN KEY(idea_id) REFERENCES ideas(id),
            FOREIGN KEY(ocr_id) REFERENCES ocr_texts(id)
        )
        """
    )
    # uploads table stores raw files uploaded via API
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT,
            stored_path TEXT,
            mime_type TEXT,
            size_bytes INTEGER,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def _migrate_ocr_table_columns(db_path: str = DB_PATH) -> None:
    """Ensure ocr_texts has columns expected by pdf_to_txt across older schemas."""
    # Make sure DB and table exist
    _ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ocr_texts)")
    existing = {row[1] for row in cur.fetchall()}
    required = [
        ("source_path", "TEXT"),
        ("text_hash", "TEXT"),
        ("text_content", "TEXT"),
        ("created_at", "TEXT"),
        ("language", "TEXT"),
        ("title", "TEXT"),
    ]
    for name, coltype in required:
        if name not in existing:
            cur.execute(f"ALTER TABLE ocr_texts ADD COLUMN {name} {coltype}")
    conn.commit()
    conn.close()

def _migrate_ideas_table_columns(db_path: str = DB_PATH) -> None:
    """Ensure ideas has columns needed for local app replacing Firestore."""
    _ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ideas)")
    existing = {row[1] for row in cur.fetchall()}
    required = [
        ("entrepreneur_id", "TEXT"),
        ("mentor_feedback", "TEXT"),
    ]
    for name, coltype in required:
        if name not in existing:
            cur.execute(f"ALTER TABLE ideas ADD COLUMN {name} {coltype}")
    conn.commit()
    conn.close()

def _insert_idea(payload: Dict[str, Any], db_path: str = DB_PATH) -> int:
    _ensure_db(db_path)
    _migrate_ideas_table_columns(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ideas (title, description, language, file_path, file_url, entrepreneur_id, mentor_feedback, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("title"),
            payload.get("description"),
            payload.get("language"),
            payload.get("path") or payload.get("file_path"),
            payload.get("file_url"),
            payload.get("uid"),
            payload.get("mentor_feedback"),
            "submitted",
            datetime.now().isoformat(),
        ),
    )
    idea_id = cur.lastrowid
    conn.commit()
    conn.close()
    return idea_id

def _insert_report(idea_id: int, ocr_id: int, report_text: str, db_path: str = DB_PATH) -> int:
    _ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reports (idea_id, ocr_id, report_text, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (idea_id, ocr_id, report_text, datetime.now().isoformat()),
    )
    report_id = cur.lastrowid
    conn.commit()
    conn.close()
    return report_id

def _insert_upload(original_name: str, stored_path: str, mime_type: str | None, size_bytes: int, db_path: str = DB_PATH) -> int:
    _ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO uploads (original_name, stored_path, mime_type, size_bytes, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (original_name, stored_path, mime_type or "application/octet-stream", size_bytes, datetime.now().isoformat()),
    )
    upload_id = cur.lastrowid
    conn.commit()
    conn.close()
    return upload_id

def _update_idea_status(idea_id: int, status: str, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE ideas SET status=? WHERE id=?", (status, idea_id))
    conn.commit()
    conn.close()


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


@app.post("/ideas")
def submit_idea(payload: dict):
    """
    Accepts idea submission and triggers OCR + evaluation pipeline.

    JSON body:
    {
        "title": "...",
        "description": "...",
        "language": "en",
        "path": "C:\\...\\file.pdf"  # local file path (preferred)
        "file_url": "https://..."       # optional; if provided but path missing, pipeline will skip OCR
    }

    Returns JSON with IDs and output paths.
    """
    title = payload.get("title")
    description = payload.get("description")
    language = payload.get("language") or "en"
    path = payload.get("path") or payload.get("file_path")
    uid = payload.get("uid")

    if not title or not description:
        raise HTTPException(status_code=400, detail="'title' and 'description' are required")

    # Insert idea row
    idea_id = _insert_idea({
        "title": title,
        "description": description,
        "language": language,
        "path": path,
        "file_url": payload.get("file_url"),
        "uid": uid,
    })

    # If a local path is provided and exists, process PDF
    ocr_output_file = None
    ocr_id = None
    extracted_text = None

    try:
        if path and os.path.isfile(path) and _is_pdf(path):
            # Defensive DB migration so pdf_to_txt can insert expected columns
            _migrate_ocr_table_columns(DB_PATH)
            detector = pdf_to_txt.PDFTextDetector(use_gemini_structuring=True)
            extracted_text = detector.process_pdf_text_detection(
                path,
                page_range=None,
                ocr_only=False,
                show_intermediate=False,
                output_file=None,
                structure_text=True,
                auto_save=True,
                output_dir="pdf_text",
                save_to_db=True,
                db_path=DB_PATH,
            )
            # Save a copy in filesystem for reference
            ocr_output_file = _save_text(Path("pdf_text"), Path(path).stem, extracted_text, "extracted")

            # Try to locate the inserted OCR row by matching latest entry with source_path
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT id FROM ocr_texts WHERE source_path=? ORDER BY id DESC LIMIT 1",
                    (path,),
                )
                row = cur.fetchone()
                ocr_id = row[0] if row else None
            except sqlite3.OperationalError:
                # Fallback if older schema without source_path
                cur.execute("SELECT id FROM ocr_texts ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                ocr_id = row[0] if row else None
            finally:
                conn.close()
            _update_idea_status(idea_id, "ocr_complete")
        else:
            _update_idea_status(idea_id, "submitted")
    except Exception as e:
        _update_idea_status(idea_id, "ocr_failed")
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")

    # If we have extracted text, run evaluation via prompt.py (Gemini)
    report_id = None
    report_text = None
    try:
        if extracted_text:
            from prompt import StartupEvaluator  # local import to avoid heavy import at module load
            evaluator = StartupEvaluator()
            results = evaluator.evaluate_idea(extracted_text)
            # Format full text report
            report_text = evaluator._format_file_content(results, extracted_text)
            report_id = _insert_report(idea_id, ocr_id or 0, report_text, DB_PATH)
            _update_idea_status(idea_id, "evaluated")
        else:
            _update_idea_status(idea_id, "pending_evaluation")
    except Exception as e:
        _update_idea_status(idea_id, "evaluation_failed")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

    return {
        "status": "ok",
        "idea_id": idea_id,
        "ocr_id": ocr_id,
        "report_id": report_id,
        "ocr_output_file": ocr_output_file,
        "message": "Idea processed successfully" if report_id else "Idea submitted; OCR/evaluation pending",
    }


@app.get("/ideas")
def list_ideas(uid: Optional[str] = None):
    """List ideas; optionally filter by entrepreneur_id (uid)."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if uid:
        cur.execute("SELECT * FROM ideas WHERE entrepreneur_id=? ORDER BY id DESC", (uid,))
    else:
        cur.execute("SELECT * FROM ideas ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [{k: row[k] for k in row.keys()} for row in rows]


@app.get("/ideas/{idea_id}")
def get_idea(idea_id: int):
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM ideas WHERE id=?", (idea_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {k: row[k] for k in row.keys()}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), process_pdf: bool = True):
    """Accepts ppt/pdf/img uploads, saves to data/uploads, records in SQLite, and optionally processes PDFs."""
    try:
        _ensure_db(DB_PATH)
        # Prepare paths
        uploads_dir = Path("data") / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(file.filename or "uploaded_file").name
        stored_path = uploads_dir / f"{timestamp}_{safe_name}"

        # Read and write file
        content = await file.read()
        stored_path.write_bytes(content)

        # Insert upload metadata
        upload_id = _insert_upload(safe_name, str(stored_path), file.content_type, len(content), DB_PATH)

        report_id = None
        ocr_id = None
        idea_id = None

        # If it's a PDF and processing is requested, run OCR + evaluation
        suffix = Path(safe_name).suffix.lower()
        if process_pdf and suffix == ".pdf":
            # Create a lightweight idea row to link downstream artifacts
            idea_id = _insert_idea({
                "title": safe_name,
                "description": f"Uploaded file {safe_name}",
                "language": "en",
                "path": str(stored_path),
                "file_url": None,
            })
            try:
                detector = pdf_to_txt.PDFTextDetector(use_gemini_structuring=True)
                extracted_text = detector.process_pdf_text_detection(
                    str(stored_path),
                    page_range=None,
                    ocr_only=False,
                    show_intermediate=False,
                    output_file=None,
                    structure_text=True,
                    auto_save=True,
                    output_dir="pdf_text",
                    save_to_db=True,
                    db_path=DB_PATH,
                )
                # Locate latest OCR row for this stored_path (fallback if schema differs)
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                try:
                    cur.execute(
                        "SELECT id FROM ocr_texts WHERE source_path=? ORDER BY id DESC LIMIT 1",
                        (str(stored_path),),
                    )
                    row = cur.fetchone()
                    ocr_id = row[0] if row else None
                except sqlite3.OperationalError:
                    cur.execute("SELECT id FROM ocr_texts ORDER BY id DESC LIMIT 1")
                    row = cur.fetchone()
                    ocr_id = row[0] if row else None
                finally:
                    conn.close()

                # Evaluate via prompt.py
                from prompt import StartupEvaluator
                evaluator = StartupEvaluator()
                results = evaluator.evaluate_idea(extracted_text)
                report_text = evaluator._format_file_content(results, extracted_text)
                report_id = _insert_report(idea_id or 0, ocr_id or 0, report_text, DB_PATH)
                _update_idea_status(idea_id or 0, "evaluated")
            except Exception as e:
                if idea_id:
                    _update_idea_status(idea_id, "ocr_or_eval_failed")
                raise HTTPException(status_code=500, detail=f"Upload processing failed: {e}")

        return {
            "status": "ok",
            "upload_id": upload_id,
            "stored_path": str(stored_path),
            "mime_type": file.content_type,
            "idea_id": idea_id,
            "ocr_id": ocr_id,
            "report_id": report_id,
            "message": "Uploaded and processed" if report_id else "Uploaded",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@app.get("/reports/{report_id}")
def get_report(report_id: int):
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE id=?", (report_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {k: row[k] for k in row.keys()}


@app.post("/ideas/{idea_id}/feedback")
def add_mentor_feedback(idea_id: int, payload: dict):
    """Attach mentor feedback to an idea and mark as reviewed."""
    feedback = payload.get("feedback")
    if not feedback:
        raise HTTPException(status_code=400, detail="'feedback' is required")
    _ensure_db(DB_PATH)
    _migrate_ideas_table_columns(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE ideas SET mentor_feedback=?, status=? WHERE id=?",
        (feedback, "reviewed", idea_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Feedback added"}


@app.get("/stats")
def get_stats():
    """Return simple statistics to drive admin dashboard without Firestore."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ideas")
    total_ideas = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM reports")
    total_reports = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM uploads")
    total_uploads = cur.fetchone()[0]
    conn.close()
    return {
        "totalIdeas": total_ideas,
        "totalReports": total_reports,
        "totalUploads": total_uploads,
    }


@app.get("/activities")
def recent_activities(limit: int = 5):
    """Return recent upload/evaluation activities for admin dashboard."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Use uploads table as activity source
    cur.execute("SELECT * FROM uploads ORDER BY id DESC LIMIT ?", (limit,))
    uploads = cur.fetchall()
    conn.close()
    activities = []
    for row in uploads:
        r = {k: row[k] for k in row.keys()}
        activities.append({
            "id": r.get("id"),
            "type": "upload",
            "timestamp": r.get("created_at"),
            "name": r.get("original_name"),
            "mime_type": r.get("mime_type"),
            "size_bytes": r.get("size_bytes"),
        })
    return activities