# script to preview the camera before the actual run

import os
import requests

from pathlib import Path

PROJECT_FOLDER = Path(__file__).parent
PREVIEW_FOLDER = PROJECT_FOLDER / 'previews'

# Raspberry Pi's endpoint
PI_ADDRESS = "http://raspberrypi.local:5000/capture"


def capture_preview():
    """
    Requests an image from the Raspberry Pi,
    saves it as preview.jpg, and returns its path.
    """

    PREVIEW_FOLDER.mkdir(parents=True, exist_ok=True)

    image_path = PREVIEW_FOLDER / "preview.jpg"

    try:
        response = requests.post(PI_ADDRESS, timeout=30)

        response.raise_for_status()

        with image_path.open("wb") as image_file:
            image_file.write(response.content)

        print(f"Preview saved: {image_path}")

        return image_path

    except requests.RequestException as error:
        print(f"Could not capture camera preview: {error}")
        return None


def main():
    image_path = capture_preview()

    if image_path is None:
        return

    print("Opening preview image")

    os.startfile(str(image_path))


if __name__ == "__main__":
    main()