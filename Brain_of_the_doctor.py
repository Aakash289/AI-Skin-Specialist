# Anthropic's official SDK, used to talk to the Claude API
import anthropic
# Loads key-value pairs from a .env file into environment variables
from dotenv import load_dotenv
# Standard library: file paths, environment variables
import os
# Standard library: encodes binary data (images, video frames) into text-safe base64
import base64
# Standard library: guesses a file's MIME type (e.g. image/png) from its filename
import mimetypes
# OpenCV, used here to open video files and pull individual frames out of them
import cv2

# Load environment variables from a .env file located in the same folder as this script,
# regardless of what directory the script is actually run from
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Read the Claude API key out of the environment (comes from the .env file above)
api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    # Fail loudly and early if the key is missing, rather than letting a
    # confusing error happen later when the API is actually called
    raise RuntimeError("CLAUDE_API_KEY environment variable is not set")

# Create one shared Anthropic client using the loaded API key.
# This client object is reused by every function below rather than
# being recreated on each call.
client = anthropic.Anthropic(api_key=api_key)


def encode_file(filepath):
    # Reads any file's raw bytes and converts them into a base64 string,
    # which is the format Claude's API expects for embedded media
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def get_media_type(filepath, fallback):
    # Tries to detect the file's MIME type from its extension (e.g. "image/jpeg").
    # If detection fails (returns None), falls back to a default type instead.
    media_type, _ = mimetypes.guess_type(filepath)
    return media_type or fallback


def extract_frames(video_filepath, max_frames=5):
    """
    Pulls evenly spaced frames out of a video and returns them as
    base64-encoded JPEG strings, since Claude can't read video directly.
    """
    # Open the video file for reading using OpenCV
    cap = cv2.VideoCapture(video_filepath)
    # Ask OpenCV how many total frames the video contains
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        # If OpenCV couldn't read any frames, the file is likely missing,
        # corrupted, or in an unsupported format, so stop here with a clear error
        cap.release()
        raise ValueError(f"Could not read any frames from {video_filepath}")

    # Calculate how many frames to skip between each sample, so the frames
    # taken are spread evenly across the whole video rather than bunched at the start
    step = max(total_frames // max_frames, 1)
    frames_base64 = []

    # Walk through the video in steps, jumping to specific frame positions
    for i in range(0, total_frames, step):
        # Move the video "playhead" to frame number i
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        # Read the frame at that position
        success, frame = cap.read()
        if not success:
            # Skip this position if the frame couldn't be read for some reason
            continue
        # Encode the frame (currently raw pixel data) into JPEG format in memory
        success, buffer = cv2.imencode(".jpg", frame)
        if success:
            # Convert the JPEG bytes into a base64 string and store it
            frames_base64.append(base64.b64encode(buffer).decode("utf-8"))
        if len(frames_base64) >= max_frames:
            # Stop early once we've collected enough frames
            break

    # Release the video file handle now that we're done reading from it
    cap.release()
    return frames_base64


def brain_of_the_doctor(patient_text, image_filepath=None, video_filepath=None):
    # System-style instructions telling Claude how to behave: tone, response
    # length, and formatting rules (no markdown, since output gets turned into audio)
    prompt = (
        "You are a confident, natural doctor specializing in skin care. Speak with the reassurance, clarity, and authority of a real doctor. "
        "Limit your entire response to two or three sentences maximum. "
        "Do not use any special characters, symbols, asterisks, or markdown formatting in your response because it will be converted directly to audio.\n\n"
        f"Patient text: {patient_text}"
    )

    # This list will hold everything sent to Claude as the message content:
    # media blocks (image or video frames) plus the text prompt
    content = []

    if video_filepath:
        # If a video was provided, extract a handful of representative frames from it
        frames = extract_frames(video_filepath)
        # Add each frame to the message as its own image block, so Claude can
        # look at multiple moments from the video, not just a single picture
        for frame_data in frames:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": frame_data,
                },
            })
    elif image_filepath:
        # Otherwise, if a single image was provided instead, add just that one
        # image block, using its real file type when possible
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": get_media_type(image_filepath, "image/png"),
                "data": encode_file(image_filepath),
            },
        })

    # Always add the text prompt last, after any images/frames, so Claude
    # sees the visual content first and the instructions/question right after
    content.append({"type": "text", "text": prompt})

    # Send everything to Claude and get back a response
    response = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5"),
        max_tokens=1000,
        messages=[{"role": "user", "content": content}],
    )

    # Claude's reply comes back as a list of content blocks; grab the text
    # from the first block, which is the doctor's spoken response
    return response.content[0].text


if __name__ == "__main__":
    # This block only runs when the file is executed directly (not when imported
    # elsewhere, like in main.py), and exists purely for quick manual testing
    folder = os.path.dirname(__file__)

    image_path = os.path.join(folder, "sample-image.jpeg")
    video_path = os.path.join(folder, "test-video.mp4")

    # Only run the image test if a sample image file actually exists in the folder
    if os.path.exists(image_path):
        print("--- Image test ---")
        print(brain_of_the_doctor(
            patient_text="What do you see in the image?",
            image_filepath=image_path,
        ))

    # Only run the video test if a sample video file actually exists in the folder
    if os.path.exists(video_path):
        print("--- Video test ---")
        print(brain_of_the_doctor(
            patient_text="What do you see in the video?",
            video_filepath=video_path,
        ))

    # If neither test file is present, say so instead of silently doing nothing
    if not os.path.exists(image_path) and not os.path.exists(video_path):
        print("No sample-image.jpeg or test-video.mp4 found in this folder, skipping tests.")