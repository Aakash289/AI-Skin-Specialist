# Standard library: used to print timestamped status messages while recording/transcribing
import logging
# Third-party library that wraps microphone access and speech capture
import speech_recognition as sr
# Used to convert raw recorded audio (WAV) into a compressed MP3 file
from pydub import AudioSegment
# Lets us treat in-memory bytes as a file-like object, so we don't need a temp file on disk
from io import BytesIO

# Configure logging so every log message shows a timestamp, severity level, and message text
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def record_audio(file_path, timeout=20, phrase_time_limit=None):
    """
    Simplified function to record audio from the microphone and save it as an MP3 file.

    Args:
    file_path (str): Path to save the recorded audio file.
    timeout (int): Maximum time to wait for a phrase to start (in seconds).
    phrase_time_lfimit (int): Maximum time for the phrase to be recorded (in seconds).
    """
    # Create a speech recognizer instance, which handles listening and capturing audio
    recognizer = sr.Recognizer()
    
    # Open the default microphone as the audio input source
    with sr.Microphone() as source:
        logging.info("Adjusting for ambient noise...")
        # Briefly listens to background noise so the recognizer can calibrate
        # its sensitivity before actually capturing speech
        recognizer.adjust_for_ambient_noise(source, duration=1)
        logging.info("Start speaking now...")
        
        # Record the audio
        # Waits up to `timeout` seconds for speech to start, then records for
        # up to `phrase_time_limit` seconds once speech begins
        audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        logging.info("Recording complete.")
        
        # Convert the recorded audio to an MP3 file
        # The recognizer gives back audio in WAV format by default, so first
        # get the raw WAV bytes, then load them into pydub as an in-memory file
        wav_data = audio_data.get_wav_data()
        audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
        # Export/compress the WAV audio into an MP3 file at the given path
        audio_segment.export(file_path, format="mp3", bitrate="128k")
        
        logging.info(f"Audio saved to {file_path}")

# Where the recorded patient audio will be saved
audio_filepath="patient_voice_test.mp3"
# Actually trigger the microphone recording using the function defined above
record_audio(audio_filepath, timeout=20, phrase_time_limit=10)

# Convert audio to text.

# Groq's client, used here purely for its Whisper-based speech-to-text API
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables (like API keys) from a .env file in the current directory
load_dotenv()

def transcribe_patient_voice(audio_filepath):
    # Read the Groq API key from the environment
    groq_api_key = os.environ.get("GROQ_API_KEY")

    # Create a Groq client using that key
    client = Groq(api_key=groq_api_key)
    # Open the recorded MP3 file in binary mode and send it to Groq's
    # transcription endpoint, forcing English so results aren't misdetected
    # as another language
    with open(audio_filepath, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=os.environ.get("WHISPER_MODEL", "whisper-large-v3"),
            language="en",
        )

    # Return just the transcribed text from the response object
    return transcription.text


# Run the transcription on the audio file we just recorded, and print the result
text = transcribe_patient_voice(audio_filepath)
print(text)