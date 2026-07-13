# CS Independent study
# AI Infant Sleep Monitoring System

import json
import os
import time
import base64

from pathlib import Path
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

IMAGES = Path(__file__).parent / 'images'
GEMINI_OUTPUT = Path(__file__).parent / 'gemini_2_5_flash_outputs'
OPENAI_OUTPUT = Path(__file__).parent / 'openai_outputs'
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


def process_image_gemini(client, image_path):
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


def process_image_openai(client, image_path):
    """
    Sends one image and the prompt to GPT-4.1 mini
    and returns the model's response text.
    """

    with image_path.open("rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": PROMPT
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,"f"{image_data}"
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "infant_sleep_safety_assessment",
                "strict": True,
                "schema": RESPONSE_SCHEMA
            }
        }
    )

    return response.output_text


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

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not gemini_api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")

    gemini_client = genai.Client(api_key=gemini_api_key)
    openai_client = OpenAI(api_key=openai_api_key)

    img_ext_allowed = {
        ".jpg",
        ".jpeg"
    }

    ###### Running gemini
    for image_path in sorted(IMAGES.iterdir()):
        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = GEMINI_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping Gemini's flash model for {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name} with Gemini.")

        # handling exception

        try:
            response_text = process_image_gemini(gemini_client, image_path)

            print("GEMINI RAW RESPONSE:")
            print(repr(response_text))

            save_output(response_text, output_path)
            print(f"Saved: {output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name} with Gemini. Error: {error}")
        finally:
            time.sleep(15)

    ###### Running OpenAI
    for image_path in sorted(IMAGES.iterdir()):

        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = OPENAI_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping OpenAI's mini model for {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name} with OpenAI")

        try:
            response_text = process_image_openai(openai_client,image_path)

            print("OPENAI RAW RESPONSE:")
            print(repr(response_text))

            save_output(response_text, output_path)
            print(f"Saved: {output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name} with OpenAI. Error: {error}")
        finally:
            time.sleep(15)


if __name__ == "__main__":
    main()
