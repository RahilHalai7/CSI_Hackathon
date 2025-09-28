import os
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydub import AudioSegment
import wave
import io
from typing import Optional, Set, Tuple, List
from google.cloud import speech_v1 as speech


def _normalize_language_code(lang: str | None) -> str:
    """Normalize language to Google STT codes. Default to en-US if None.

    Accepts short codes like 'en', 'hi', 'mr' and maps to en-US, hi-IN, mr-IN.
    """
    if not lang:
        return "en-US"
    lang = lang.strip()
    short_to_full = {
        "en": "en-US",
        "hi": "hi-IN",
        "mr": "mr-IN",
        "or": "or-IN",  # Odia
        "odia": "or-IN",  # Odia alias
        "bn": "bn-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "gu": "gu-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "pa": "pa-IN",
        "ur": "ur-IN",
    }
    return short_to_full.get(lang, lang)


def convert_to_wav_mono_16k(input_path: str) -> str:
    """Convert input audio to mono 16kHz WAV and return path to temp file."""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    out_dir = Path("audio")
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_path = out_dir / "temp.wav"
    audio.export(temp_path, format="wav")
    return str(temp_path)


def transcribe_audio_google(
    input_path: str,
    language: str | None = None,
    diarize: bool = False,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    chunk_secs: int = 58,
) -> Tuple[str, Optional[int]]:
    """Transcribe an audio file using Google Cloud Speech-to-Text.

    - Ensures audio is WAV mono @ 16kHz (LINEAR16)
    - Returns plain text transcript
    """
    language_code = _normalize_language_code(language)

    client = speech.SpeechClient()

    def _recognize_bytes(audio_bytes: bytes, sample_rate: int) -> Tuple[list[str], Set[int], List[str]]:
        audio = speech.RecognitionAudio(content=audio_bytes)
        diarization_cfg = None
        if diarize:
            # Provide sane defaults if hints not provided
            if min_speakers is None and max_speakers is None:
                min_speakers_local = 2
                max_speakers_local = 4
            else:
                min_speakers_local = min_speakers
                max_speakers_local = max_speakers
            diarization_cfg = speech.SpeakerDiarizationConfig()
            # CRITICAL: must enable diarization explicitly
            diarization_cfg.enable_speaker_diarization = True
            if min_speakers_local is not None:
                diarization_cfg.min_speaker_count = min_speakers_local
            if max_speakers_local is not None:
                diarization_cfg.max_speaker_count = max_speakers_local

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=diarize,
            diarization_config=diarization_cfg,
        )
        response = client.recognize(config=config, audio=audio)
        parts: list[str] = []
        speaker_tags: Set[int] = set()
        diarized_lines: List[str] = []
        for result in response.results:
            if result.alternatives:
                alt = result.alternatives[0]
                parts.append(alt.transcript)
                if diarize and hasattr(alt, "words") and alt.words:
                    # Build simple segments grouped by speaker_tag
                    current_tag = None
                    current_words: List[str] = []
                    for w in alt.words:
                        tag = getattr(w, "speaker_tag", 0)
                        word_text = getattr(w, "word", "")
                        if tag:
                            speaker_tags.add(int(tag))
                        if current_tag is None:
                            current_tag = tag or 0
                            current_words = [word_text]
                        elif tag == current_tag:
                            current_words.append(word_text)
                        else:
                            # Flush previous segment
                            label = f"Person {current_tag}" if current_tag else "Person"
                            diarized_lines.append(f"{label}: {' '.join(current_words).strip()}")
                            # Start new segment
                            current_tag = tag or 0
                            current_words = [word_text]
                    if current_words:
                        label = f"Person {current_tag}" if current_tag else "Person"
                        diarized_lines.append(f"{label}: {' '.join(current_words).strip()}")
        return parts, speaker_tags, diarized_lines

    # Determine WAV path and sample rate
    input_ext = Path(input_path).suffix.lower()
    wav_path: str
    if input_ext == ".wav":
        wav_path = input_path
        with wave.open(wav_path, "rb") as w:
            sample_rate = w.getframerate()
            nframes = w.getnframes()
            duration_sec = nframes / float(sample_rate)
    else:
        wav_path = convert_to_wav_mono_16k(input_path)
        with wave.open(wav_path, "rb") as w:
            sample_rate = w.getframerate()  # should be 16000
            nframes = w.getnframes()
            duration_sec = nframes / float(sample_rate)

    # If audio is longer than ~chunk_secs, split to stay below Google STT sync limit
    if duration_sec >= float(chunk_secs):
        transcripts: list[str] = []
        all_speaker_tags: Set[int] = set()
        with wave.open(wav_path, "rb") as w:
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            framerate = w.getframerate()

            # ~chunk_secs seconds per chunk
            chunk_frames = int(framerate * chunk_secs)
            total_frames = w.getnframes()
            frames_read = 0

            while frames_read < total_frames:
                frames_to_read = min(chunk_frames, total_frames - frames_read)
                chunk_data = w.readframes(frames_to_read)
                frames_read += frames_to_read

                # Write chunk WAV to memory
                buf = io.BytesIO()
                with wave.open(buf, "wb") as out_wav:
                    out_wav.setnchannels(channels)
                    out_wav.setsampwidth(sampwidth)
                    out_wav.setframerate(framerate)
                    out_wav.writeframes(chunk_data)
                audio_bytes = buf.getvalue()

                parts, tags, diar_lines = _recognize_bytes(audio_bytes, framerate)
                if diarize and diar_lines:
                    transcripts.append("\n".join(diar_lines))
                elif parts:
                    transcripts.append(" ".join(parts))
                all_speaker_tags |= tags

        final_text = "\n".join(t.strip() for t in transcripts if t.strip())
        detected_count = len(all_speaker_tags) if diarize else None
        return final_text, detected_count
    else:
        # Short audio: single request
        with open(wav_path, "rb") as f:
            content = f.read()
        parts, tags, diar_lines = _recognize_bytes(content, sample_rate)
        if diarize and diar_lines:
            final_text = "\n".join(diar_lines)
        else:
            final_text = "\n".join(t.strip() for t in parts if t.strip())
        detected_count = len(tags) if diarize else None
        return final_text, detected_count

    response = client.recognize(config=config, audio=audio)
    transcripts: list[str] = []
    for result in response.results:
        if result.alternatives:
            transcripts.append(result.alternatives[0].transcript)

    return "\n".join(t.strip() for t in transcripts if t.strip())


def main() -> int:
    load_dotenv()  # Load GOOGLE_APPLICATION_CREDENTIALS from .env if present

    parser = argparse.ArgumentParser(description="Transcribe audio using Google Cloud Speech-to-Text")
    parser.add_argument("--input", required=True, help="Path to input audio file (wav/mp3/m4a)")
    parser.add_argument("--output", help="Optional path to save transcript (txt)")
    parser.add_argument("--language", help="Language code (e.g., en-US, mr-IN, hi-IN)", default=None)
    parser.add_argument("--diarize", action="store_true", help="Enable speaker diarization and report detected speaker count")
    parser.add_argument("--min-speakers", type=int, default=None, help="Optional minimum number of speakers for diarization")
    parser.add_argument("--max-speakers", type=int, default=None, help="Optional maximum number of speakers for diarization")
    parser.add_argument("--chunk-secs", type=int, default=58, help="Chunk duration (seconds) for long audio files")
    parser.add_argument("--output-style", choices=["plain", "diarized"], default="plain", help="Format transcript output: plain lines or diarized 'Person N:' style")
    args = parser.parse_args()

    # Credential check for Google Cloud STT
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS not set. Set it in environment or .env for Google Cloud STT.")

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"❌ Input file not found: {input_path}")
        return 1

    try:
        transcript_text, speaker_count = transcribe_audio_google(
            input_path,
            language=args.language,
            diarize=(args.diarize or args.output_style == "diarized"),
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
            chunk_secs=args.chunk_secs,
        )
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return 1

    if not transcript_text.strip():
        print("⚠️ No transcript returned.")
    else:
        print("✅ Transcription complete\n")
        if args.diarize and speaker_count is not None:
            print(f"Detected speakers: {speaker_count}\n")
        print(transcript_text)

    if args.output:
        out_path = Path(args.output)
        out_dir = out_path.parent
        if out_dir and not out_dir.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"\n📝 Saved transcript to: {out_path}")
    else:
        # Save to pdf_text/ with timestamp by default
        default_dir = Path("pdf_text")
        default_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = Path(input_path).stem
        out_path = default_dir / f"{base}_google_stt_{ts}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        print(f"\n📝 Saved transcript to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
