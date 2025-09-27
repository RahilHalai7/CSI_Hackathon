import whisper
from pydub import AudioSegment

# Path to your MP3 file
audio_path = "audio/test_audio.mp3"

# Convert MP3 to WAV (Whisper works better with WAV)
audio = AudioSegment.from_mp3(audio_path)
wav_path = "audio/temp.wav"
audio.export(wav_path, format="wav")

# Load the Whisper model
model = whisper.load_model("base")  # small/base/medium/large

# Transcribe
result = model.transcribe(wav_path)

# Print the transcription
print("Transcription:")
print(result["text"])
