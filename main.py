def main():
    print("AI Infant Sleep Monitoring System!")

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

# print(api_key is not None)

uploaded_file = client.files.upload(file="images/test_img1.jpeg")

interaction = client.interactions.create(
    model="gemini-2.5-flash",
    input=[
        {"type": "text", "text": "Caption this image."},
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