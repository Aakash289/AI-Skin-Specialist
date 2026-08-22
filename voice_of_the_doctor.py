# Step1: Create API keys

# Step2: Create Client and send request
# Deepgram's client, used here for text-to-speech (converting the doctor's
# written response into spoken audio)
from deepgram import DeepgramClient
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (like API keys) from a .env file in the current directory
load_dotenv()

# The folder this script lives in, used to build reliable file paths
# regardless of where the script is run from
BASE_DIR = Path(__file__).resolve().parent
# Default location to save the doctor's generated audio response if no
# specific output path is given
DEFAULT_DOCTOR_AUDIO = BASE_DIR / "doctor_response.mp3"

def convert_text_to_doctor_audio(text, output_filepath=DEFAULT_DOCTOR_AUDIO):
    # Read the Deepgram API key from the environment
    deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
    # Create a Deepgram client using that key
    deepgram = DeepgramClient(api_key=deepgram_api_key)
    # Send the doctor's text to Deepgram's text-to-speech engine, requesting
    # a specific voice model and MP3 output
    audio = deepgram.speak.v1.audio.generate(
        text=text,
        model=os.environ.get("DEEPGRAM_TTS_MODEL", "aura-2-thalia-en"),
        encoding="mp3",
    )

    # Make sure the output path is a proper Path object (handles the case
    # where a plain string is passed in instead)
    output_filepath = Path(output_filepath)
    # Write the generated audio out to disk, chunk by chunk, as it streams back
    with output_filepath.open("wb") as file:
        for chunk in audio:
            file.write(chunk)

    # Return the path to the saved audio file so the caller knows where it went
    return output_filepath

# Used to launch the system's audio player and detect which OS we're running on
import subprocess
import platform

def play_audio(audio_filepath):
    # Ensure the path is a plain string, since some OS-level calls expect that
    audio_filepath = str(audio_filepath)

    # Pick the correct command to open/play the audio file depending on the
    # operating system this script is running on
    if platform.system() == "Darwin":
        # macOS: use the built-in afplay command-line tool
        subprocess.run(["afplay", audio_filepath], check=False)
    elif platform.system() == "Windows":
        # Windows: open the file with whatever the default app for MP3s is
        os.startfile(audio_filepath)
    else:
        # Linux: use xdg-open, which opens the file with the system's default app
        subprocess.run(["xdg-open", audio_filepath], check=False)


"""text = "Hi, my name is Aakash, who are you?."
api_key = os.environ.get("DEEPGRAM_API_KEY")
deepgram = DeepgramClient(api_key=api_key)
audio = deepgram.speak.v1.audio.generate(
    text=text,
    model="aura-2-thalia-en",
    encoding="mp3",
)
# Step3: Save audio
from pathlib import Path

audio_file="test-output.mp3"
audio_path = Path(__file__).with_name(audio_file)
with audio_path.open("wb") as file:
    for chunk in audio:
        file.write(chunk)

# Step4: Play audio
import platform
import subprocess


if platform.system() == "Darwin":  # macOS
    subprocess.run(["afplay", str(audio_path)])
elif platform.system() == "Windows":
    os.startfile(audio_path)
else:  # Linux
    subprocess.run(["xdg-open", str(audio_path)])"""