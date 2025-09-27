CSI Hackathon – OCR and ASR with Google Cloud

Overview
- Extract text from images using Google Cloud Vision (OCR).
- Transcribe speech from audio files using Google Cloud Speech-to-Text (ASR).
- Quick auth check to verify credentials are loaded.

Project Structure
- `ocr.py` – Image OCR via Google Cloud Vision.
- `asr.py` – Audio transcription via Google Cloud Speech-to-Text; auto converts MP3/M4A to WAV.
- `authentication.py` – Prints the authenticated service account email to confirm setup.
- `main.py` – Placeholder for orchestration (currently empty).
- `images/` – Sample images for testing.
- `audio/` – Sample audio files for testing.

Prerequisites
- Python 3.9+ recommended.
- A Google Cloud project with the Vision API and Speech-to-Text API enabled.
- A Service Account key (JSON) with permissions for Vision and Speech.
- `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to the key file.
- FFmpeg installed and available on PATH (required by `pydub` for audio conversion).

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
4) Install FFmpeg:
   - Download from https://www.gyan.dev/ffmpeg/builds/ or use a package manager.
   - Add the `bin` folder to your PATH and verify with `ffmpeg -version`.

Usage
- Verify authentication:
  - `python authentication.py`
  - Expected output includes the service account email.
- Run OCR on an image:
  - Update `image_path` in `ocr.py` or modify the script to pass a path.
  - `python ocr.py`
- Transcribe audio:
  - Update `audio_path` in `asr.py`.
  - `python asr.py`

Notes
- `asr.py` supports `.wav`, `.mp3`, and `.m4a`. Non-WAV inputs are converted to mono 16kHz WAV for best results.
- If you receive `Vision API Error` or `403` errors, ensure the APIs are enabled and the service account has correct roles.
- If `pydub` complains about FFmpeg not found, confirm PATH includes the FFmpeg `bin` directory.

Troubleshooting
- Credentials not found:
  - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key file.
  - Confirm the key has permissions for Vision and Speech.
- FFmpeg issues:
  - Run `ffmpeg -version`; if it fails, reinstall or fix PATH.
- API permissions:
  - Verify APIs are enabled in Google Cloud Console and IAM roles are assigned.

License
- Internal hackathon project; add a license if needed.