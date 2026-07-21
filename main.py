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
from anthropic import Anthropic

# main project folder
PROJECT_FOLDER = Path(__file__).parent

IMAGES = PROJECT_FOLDER / "images"
RESULTS_FOLDER = PROJECT_FOLDER / "results"

GEMINI_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_outputs"
GEMINI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_invalid_outputs"

OPENAI_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_outputs"
OPENAI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_invalid_outputs"

ANTHROPIC_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_outputs"
ANTHROPIC_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_invalid_outputs"

PROMPT = """
        You are assisting with the assessment of child sleep environments for a computer science research project.
        Analyze the child sleep environment shown in this image.
        
        Set exactly one of the following fields to true:
        
        - no_apparent_safety_concerns
        - possible_safety_concerns
        - serious_safety_concerns
        
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


ASSESSMENT_FIELDS = [
    "no_apparent_safety_concerns",
    "possible_safety_concerns",
    "serious_safety_concerns"
]


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


def process_image_anthropic(client, image_path):
    """
    Sends one image and the prompt to Anthropic AI
    and returns the model's response text.
    """

    with image_path.open("rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    )

    return response.content[0].text


def clean_output_text(output_text):
    """
    Removes possible Markdown code fences from AI output text.
    """
    cleaned_text = output_text.strip()

    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[len("```json"):]
    elif cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[len("```"):]

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]

    final_text = cleaned_text.strip()

    return final_text


def validate_output(output_obj):
    """
    Checks that the AI response follows the expected JSON format.
    """

    # Check that the output is a JSON object
    if not isinstance(output_obj, dict):
        raise ValueError("AI output must be a JSON object.")

    # Check that all required fields exist
    for field in ASSESSMENT_FIELDS:
        if field not in output_obj:
            raise ValueError(f"Missing field: {field}")

    if "explanation" not in output_obj:
        raise ValueError("Missing field: explanation")

    # Check that the assessment fields contain True or False
    for field in ASSESSMENT_FIELDS:
        if not isinstance(output_obj[field], bool):
            raise ValueError(f"{field} must be True or False.")

    # Check that explanation is a non-empty string
    if not isinstance(output_obj["explanation"], str):
        raise ValueError("Explanation must be a string.")

    if output_obj["explanation"].strip() == "":
        raise ValueError("Explanation cannot be empty.")

    # Count how many assessment categories are True
    true_count = 0

    for field in ASSESSMENT_FIELDS:
        if output_obj[field]:
            true_count += 1

    if true_count != 1:
        raise ValueError("Exactly one assessment category must be True only.")

    expected_fields = ASSESSMENT_FIELDS + [
        "explanation",
        "file_name"
    ]

    for field in output_obj:
        if field not in expected_fields:
            raise ValueError(f"Unexpected field: {field}")


def save_output(output_text, output_path, invalid_output_path, image_path):
    """
    Takes AI's response text and writes it to a file
    in JSON format at the specified output path. If invalid,
    saves to corresponding invalid output folder.
    """
    cleaned_text = clean_output_text(output_text)

    try:
        string_to_obj = json.loads(cleaned_text)

        validate_output(string_to_obj)

        string_to_obj["file_name"] = image_path.name

        # Create an output folder if it does not exist already
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as out_file:
            json.dump(string_to_obj, out_file, indent=4)

        return True

    except (json.JSONDecodeError, ValueError) as error:
        invalid_output = {
            "file_name": image_path.name,
            "explanation_error": str(error),
            "raw_response": output_text
        }
        invalid_output_path.parent.mkdir(parents=True, exist_ok=True)
        with invalid_output_path.open("w", encoding="utf-8") as invalid_output_file:
            json.dump(invalid_output, invalid_output_file, indent=4)

        return False


def main():

    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")

    if not anthropic_api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY environment variable")

    gemini_client = genai.Client(api_key=gemini_api_key)
    openai_client = OpenAI(api_key=openai_api_key)
    anthropic_client = Anthropic(api_key=anthropic_api_key)

    img_ext_allowed = {
        ".jpg",
        ".jpeg"
    }


    ###### Running gemini
    for image_path in sorted(IMAGES.iterdir()):
        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = GEMINI_OUTPUT / f"{image_path.stem}.json"
        invalid_output_path = GEMINI_INVALID_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping Gemini's flash model for {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name} with Gemini.")

        # output to be recorded either valid or invalid
        try:
            response_text = process_image_gemini(gemini_client, image_path)

            # print("GEMINI RAW RESPONSE:")
            # print(repr(response_text))

            valid_output = save_output(response_text, output_path, invalid_output_path, image_path)

            if valid_output:
                print(f"Saved valid output: {output_path}")
            else:
                print(f"Saved invalid output: {invalid_output_path}")

        # reached here for error in image processing
        except Exception as error:
            print(f"Could not process image {image_path.name} with Gemini. Error: {error}")
        finally:
            time.sleep(15)


    ###### Running OpenAI
    for image_path in sorted(IMAGES.iterdir()):

        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = OPENAI_OUTPUT / f"{image_path.stem}.json"
        invalid_output_path = OPENAI_INVALID_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping OpenAI's mini model for {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name} with OpenAI")

        try:
            response_text = process_image_openai(openai_client,image_path)

            # print("OPENAI RAW RESPONSE:")
            # print(repr(response_text))

            valid_output = save_output(response_text, output_path, invalid_output_path, image_path)

            if valid_output:
                print(f"Saved valid output: {output_path}")
            else:
                print(f"Saved invalid output: {invalid_output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name} with OpenAI. Error: {error}")
        finally:
            time.sleep(15)


    ###### Running Anthropic AI
    for image_path in sorted(IMAGES.iterdir()):

        if image_path.suffix.lower() not in img_ext_allowed:
            continue

        output_path = ANTHROPIC_OUTPUT / f"{image_path.stem}.json"
        invalid_output_path = ANTHROPIC_INVALID_OUTPUT / f"{image_path.stem}.json"

        if output_path.exists():
            print(f"Skipping Anthropic's model for {image_path.name}: output already exists.")
            continue

        print(f"Processing {image_path.name} with Anthropic")

        try:
            response_text = process_image_anthropic(anthropic_client, image_path)

            # print("ANTHROPIC RAW RESPONSE:")
            # print(repr(response_text))

            valid_output = save_output(response_text, output_path, invalid_output_path, image_path)

            if valid_output:
                print(f"Saved: {output_path}")
            else:
                print(f"Saved invalid output: {invalid_output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name} with Anthropic. Error: {error}")
        finally:
            time.sleep(15)


if __name__ == "__main__":
    main()
