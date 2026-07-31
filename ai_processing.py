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
from mistralai.client import Mistral

# main project folder
PROJECT_FOLDER = Path(__file__).parent

IMAGES = PROJECT_FOLDER / "images"
RESULTS_FOLDER = PROJECT_FOLDER / "results"

# Gemini's Flash model
GEMINI_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_outputs"
GEMINI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "gemini_invalid_outputs"

# OpenAI's GPT model
OPENAI_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_outputs"
OPENAI_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "openai_invalid_outputs"

# Anthropic's claude model
ANTHROPIC_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_outputs"
ANTHROPIC_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "anthropic_invalid_outputs"

# Mistral's model
MISTRAL_OUTPUT = RESULTS_FOLDER / "updated_run" / "mistral_outputs"
MISTRAL_INVALID_OUTPUT = RESULTS_FOLDER / "updated_run" / "mistral_invalid_outputs"

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


def process_image_mistral(client, image_path):
    """
    Sends one image and the prompt to Mistral
    and returns the model's response text.
    """

    with image_path.open("rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.complete(
        model="mistral-medium-3.5",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_data}"
                    }
                ]
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    return response.choices[0].message.content


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


def create_ai_clients():
    """Load API keys and create a client object for each AI model"""

    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

    if not gemini_api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")

    if not anthropic_api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY environment variable")

    if not mistral_api_key:
        raise ValueError("Missing MISTRAL_API_KEY environment variable")

    gemini_client = genai.Client(api_key=gemini_api_key)
    openai_client = OpenAI(api_key=openai_api_key)
    anthropic_client = Anthropic(api_key=anthropic_api_key)
    mistral_client = Mistral(api_key=mistral_api_key)

    return gemini_client, openai_client, anthropic_client, mistral_client


def process_img_ai(image_path):
    """
    Send one image to each AI model and save
    valid or invalid output response for each.
    """

    gemini_client, openai_client, anthropic_client, mistral_client = create_ai_clients()

    # Using tuple to package together attributes that all AI models have:
    ## model name
    ## client
    ## AI process function for each
    ## valid output folder for each
    ## valid output folder for each

    model_jobs = [
        (
            "Gemini",
            gemini_client,
            process_image_gemini,
            GEMINI_OUTPUT,
            GEMINI_INVALID_OUTPUT
        ),
        (
            "OpenAI",
            openai_client,
            process_image_openai,
            OPENAI_OUTPUT,
            OPENAI_INVALID_OUTPUT
        ),
        (
            "Anthropic",
            anthropic_client,
            process_image_anthropic,
            ANTHROPIC_OUTPUT,
            ANTHROPIC_INVALID_OUTPUT
        ),
        (
            "Mistral",
            mistral_client,
            process_image_mistral,
            MISTRAL_OUTPUT,
            MISTRAL_INVALID_OUTPUT
        )
    ]
    for (
        model_name,
        client,
        process_function,
        output_folder,
        invalid_output_folder
    ) in model_jobs:

        output_path = output_folder / f"{image_path.stem}.json"
        invalid_output_path = (invalid_output_folder / f"{image_path.stem}.json")

        print(f"Processing {image_path.name} with {model_name}.")

        try:
            response_text = process_function(client, image_path)

            valid_output = save_output(
                response_text,
                output_path,
                invalid_output_path,
                image_path
            )

            if valid_output:
                print(f"Saved valid output: {output_path}")
            else:
                print(f"Saved invalid output: {invalid_output_path}")

        except Exception as error:
            print(f"Could not process image {image_path.name} with {model_name}. Error:  {error}")


