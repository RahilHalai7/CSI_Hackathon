CSI Hackathon – OCR + ASR Toolkit

Overview
- Extract text from images using Google Cloud Vision (OCR).
- Transcribe speech with Google Cloud Speech‑to‑Text (ASR) and optional speaker diarization.
- Multi‑language ASR tested for: English (`en-US`), Hindi (`hi-IN`), Marathi (`mr-IN`), Odia (`or-IN`), Gujarati (`gu-IN`).

Features
- Auto‑convert non‑WAV audio (MP3/M4A/MP4) to mono 16 kHz WAV via FFmpeg.
- Speaker‑attributed transcripts when `--diarize` is enabled (outputs lines like `Person 1: ...`).
- Language normalization accepts short codes (e.g., `en`, `hi`, `mr`, `gu`, `or`, `odia`).
- Saves transcripts under `pdf_text/` with timestamped filenames by default.

Prerequisites
- Python 3.9+.
- Google Cloud project with Speech‑to‑Text and Vision APIs enabled.
- Service Account JSON key with permissions for Speech/Vision.
- FFmpeg installed and on PATH (required for non‑WAV inputs).

Setup (Windows / PowerShell)
1) Create and activate a virtual environment:
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
2) Install dependencies:
   - `pip install -r requirements.txt`
3) Set credentials (current session):
   - `$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\path\\to\\your-key.json"`
   Or persistently:
   - `setx GOOGLE_APPLICATION_CREDENTIALS "C:\\path\\to\\your-key.json"`
4) Install FFmpeg and verify:
   - Add `ffmpeg` to PATH and run `ffmpeg -version`.

Project Structure
- `asr.py` — Audio transcription via Google Cloud STT; supports diarization; converts audio to WAV mono 16 kHz.
- `pdf_to_txt.py` — Extracts text from PDFs.
- `oldscripts/ocr.py` — Image OCR via Google Cloud Vision.
- `audio/` — Sample audio inputs.
- `pdf_text/` — Saved transcripts and extracted text.

ASR Usage
- Basic transcription:
  - `python asr.py --input audio/Audio_Marathi_sample1.wav --language mr-IN`
- Save to a specific file:
  - `python asr.py --input audio/Audio_Marathi_sample1.wav --language mr-IN --output pdf_text/marathi_transcript.txt`

Speaker Diarization
- Enable diarization and provide hints:
  - `python asr.py --input audio/Audio_Hindi_sample2.wav --language hi-IN --diarize --min-speakers 2 --max-speakers 4`
- When enabled, the output includes speaker‑labeled lines like:
  - `Person 1: ...`
  - `Person 2: ...`
- If hints are omitted, the script uses defaults (`min=2`, `max=4`).

Language Examples
- English (`en-US`):
  - `python asr.py --input audio/test_audio_en.wav --language en-US --diarize --min-speakers 1 --max-speakers 3`
- Hindi (`hi-IN`):
  - `python asr.py --input audio/Audio_Hindi_sample2.wav --language hi-IN --diarize --min-speakers 2 --max-speakers 4`
- Marathi (`mr-IN`):
  - `python asr.py --input audio/Audio_Marathi_sample1.wav --language mr-IN --diarize --min-speakers 2 --max-speakers 4`
- Odia (`or-IN`):
  - `python asr.py --input audio/Audio_Odia_sample2.wav --language or-IN --diarize --min-speakers 2 --max-speakers 6`
- Gujarati (`gu-IN`):
  - `python asr.py --input audio/Audio_Gujrati_sample1.wav --language gu-IN --diarize --min-speakers 2 --max-speakers 4`

Non‑WAV Inputs (MP3/M4A/MP4)
- The script converts inputs to mono 16 kHz WAV automatically if FFmpeg is on PATH.
- To pre‑convert manually:
  - `ffmpeg -y -i input.mp4 -vn -ac 1 -ar 16000 audio/converted.wav`

Saved Outputs
- By default, transcripts are saved to `pdf_text/<input_name>_google_stt_<timestamp>.txt`.
- Use `--output` to specify a custom path.

OCR Usage
- Run OCR on an image (see `oldscripts/ocr.py`):
  - Update the path in the script or adapt to take CLI arguments.
  - `python oldscripts/ocr.py`

Troubleshooting
- Credentials warnings:
  - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key and APIs are enabled.
- FFmpeg not found:
  - Install FFmpeg and verify `ffmpeg -version` works. Non‑WAV inputs require FFmpeg.
- Unsupported model errors:
  - The script uses Google’s default model selection per language (e.g., `gu-IN` works without specifying `latest_long`).
- Diarization detects 0–1 speakers:
  - Increase `--min-speakers` / `--max-speakers` and ensure clean audio. Some languages return sparse speaker tags; transcripts still output and can be post‑processed.

Notes
- Diarization quality varies by audio clarity and language; the script groups words by `speaker_tag` into labeled lines.
- For long audio, the script splits into ~58‑second chunks to stay within synchronous STT limits.

License
- Internal hackathon project; add a license if distributing publicly.