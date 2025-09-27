import os
from google.cloud import speech
from pydub import AudioSegment
from google.oauth2 import service_account

def _load_credentials():
    """Load service account credentials from env or local swift-key.json."""
    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.isfile(env_path):
        return None
    repo_root = os.path.dirname(os.path.abspath(__file__))
    local_key = os.path.join(repo_root, "swift-key.json")
    if os.path.isfile(local_key):
        return service_account.Credentials.from_service_account_file(local_key)
    return None


def convert_to_wav(audio_path: str) -> str:
    """Convert MP3 or M4A to WAV format for Google Speech-to-Text."""
    file_name, ext = os.path.splitext(audio_path)
    ext = ext.lower()
    wav_path = file_name + "_converted.wav"

    if ext in [".wav"]:
        return audio_path  # Already WAV
    elif ext in [".mp3", ".m4a"]:
        audio = AudioSegment.from_file(audio_path, format=ext[1:])
        audio = audio.set_channels(1).set_frame_rate(16000)  # Mono 16kHz
        audio.export(wav_path, format="wav")
        return wav_path
    else:
        raise ValueError(f"Unsupported audio format: {ext}")

def transcribe_audio(audio_path: str) -> str:
    """Transcribe speech from an audio file using Google Cloud Speech-to-Text."""
    credentials = _load_credentials()
    client = speech.SpeechClient(credentials=credentials) if credentials else speech.SpeechClient()

    # Convert audio if needed
    wav_path = convert_to_wav(audio_path)

    with open(wav_path, "rb") as f:
        content = f.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-IN",
    )

    response = client.recognize(config=config, audio=audio)
    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    return transcript

if __name__ == "__main__":
    audio_path = r"C:\Users\RAHIL\Desktop\CSIHackathon\audio\test_audio2.m4a"  # or .mp3/.wav
    text = transcribe_audio(audio_path)
    print("✅ Transcribed Audio:\n")
    print(text)
