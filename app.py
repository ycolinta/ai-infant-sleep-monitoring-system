import requests
from datetime import datetime
from pathlib import Path

from database import insert_image
from ai_processing import process_img_ai

PROJECT_FOLDER = Path(__file__).parent
IMAGES_FOLDER = PROJECT_FOLDER / "images"

# Raspberry Pi's endpoint
PI_ADDRESS = "http://raspberrypi.local:5000/capture"


def capture_img_from_pi():
    """
    Make a request to Raspberry Pi to capture an image
    and save it in the laptop project's images folder
    """
    IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = IMAGES_FOLDER / f"capture_{timestamp}.jpg"

    try:
        # After 30 seconds, raise exception
        response = requests.post(PI_ADDRESS, timeout=30)

        # Raises http error
        response.raise_for_status()

        with image_path.open("wb") as image_file:
            # Write JPEG bytes received from RPi to file object image_file
            image_file.write(response.content)

        print(f"Image received and saved {image_path}")

        return image_path

    except requests.RequestException as error:
        print(f"Error capturing image from Raspberry Pi: {error}")
        return None


def main():

    image_path = capture_img_from_pi()

    if image_path is None:
        return

    # Insert newly captured image to db
    image_id = insert_image(image_path)

    print(f"Image inserted into database. ID: {image_id}")

    print(f"Next step AI processing for: {image_path.name}")
    process_img_ai(image_id, image_path)
    print(f"AI processing finished for: {image_path.name}")


if __name__ == "__main__":
    main()