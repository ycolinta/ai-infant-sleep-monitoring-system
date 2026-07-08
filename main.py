# CS Independent study
# AI Infant Sleep Monitoring System

import os
from dotenv import load_dotenv
from google import genai


def main():
    print("AI Infant Sleep Monitoring System!")


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# print(api_key is not None)

uploaded_file = client.files.upload(file="images/image03.jpeg")

interaction = client.interactions.create(
    model="gemini-2.5-flash",
    input=[
        {"type": "text", "text": """
        You are assisting with the assessment of infant sleep environments for a computer science research project.
        Analyze the infant sleep environment shown in this image.
        Based only on the visible information, determine whether the image shows:
        
        - No apparent safety concerns.
        - Possible safety concerns.
        - Serious safety concerns.
        
        Exactly one of these categories must be selected as true. The other two categories must be false.
        
       Briefly explain the observations that led to your assessment in the explanation field.

        Return each of the responses as JSON.
        """},
        {
            "type": "image",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type
        }
    ]
)
print(interaction.output_text)


if __name__ == "__main__":
    main()
