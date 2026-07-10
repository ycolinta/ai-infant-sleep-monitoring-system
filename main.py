# CS Independent study
# AI Infant Sleep Monitoring System

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

IMAGES = Path(__file__).parent / 'images'
GEMINI_OUTPUT = Path(__file__).parent / 'gemini_2_5_flash_outputs'
PROMPT = """
You are assisting with the assessment of child sleep environments for a computer science research project.
        Analyze the child sleep environment shown in this image.
        Based only on the visible information, determine whether the image shows:
        
        - No apparent safety concerns.
        - Possible safety concerns.
        - Serious safety concerns.
        
        Exactly one category must be true. The other two must be false.
        
        Briefly explain the observations that led to your assessment in the explanation field.

        Return each of the responses as JSON.
"""


def process_image(client, image_path):
    """
    Takes a Gemini client and image path, creates an Interaction session record
    using the prompt and image, and returns the model's response text.
    """
    uploaded_img = client.files.upload(file=image_path)
    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=[
            {
                "type": "text",
                "text": PROMPT
            },
            {
            "type": "image",
            "uri": uploaded_img.uri,
            "mime_type": uploaded_img.mime_type
            }
        ]
    )

    return interaction.output_text


def save_output(output_text, output_path):
    """
    Takes AI's response text and writes it to a file
    in JSON format at the specified output path.
    """
    string_to_obj = json.loads(output_text)
    with output_path.open("w", encoding="utf-8") as out_file:
        json.dump(string_to_obj, out_file, indent=4)


def main():

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable")

    client = genai.Client(api_key=api_key)

    img_ext_allowed = {
        ".jpg",
        ".jpeg",
        "png"
    }

    for image_path in IMAGES.iterdir():
        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = GEMINI_OUTPUT / f"{image_path.stem}.json"

        print(f"Processing {image_path.name}")










if __name__ == "__main__":
    main()
