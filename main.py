# CS Independent study
# AI Infant Sleep Monitoring System

import json
import os
import time
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

        Return only one valid JSON object. Do not include Markdown code fences or any text outside the JSON object.
        
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "no_apparent_safety_concerns": {
            "type": "boolean"
        },
        "possible_safety_concerns": {
            "type": "boolean"
        },
        "serious_safety_concerns": {
            "type": "boolean"
        },
        "explanation": {
            "type": "string"
        }
    },
    "required": [
        "no_apparent_safety_concerns",
        "possible_safety_concerns",
        "serious_safety_concerns",
        "explanation"
    ],
    "additionalProperties": False
}


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
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": RESPONSE_SCHEMA
        }
    )

    return interaction.output_text


def save_output(output_text, output_path):
    """
    Removes possible markdown code.
    Takes AI's response text and writes it to a file
    in JSON format at the specified output path.
    """
    cleaned_text = output_text.strip()

    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[len("```json"):]

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]

    cleaned_text = cleaned_text.strip()

    string_to_obj = json.loads(cleaned_text)
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
        ".png"
    }

    for image_path in sorted(IMAGES.iterdir()):
        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = GEMINI_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name}")

        # handling exception

        try:
            response_text = process_image(client, image_path)

            print("RAW RESPONSE:")
            print(repr(response_text))

            save_output(response_text, output_path)
            print(f"Saved: {output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name}. Error: {error}")
        finally:
            time.sleep(15)

        # break # Stop after attempting one image to see if program works


if __name__ == "__main__":
    main()
