import requests
import time

from datetime import datetime
from pathlib import Path

from database import insert_image
from ai_processing import process_img_ai

# Main project folder
PROJECT_FOLDER = Path(__file__).parent

# Folder where images received from Raspberry Pi are saved
IMAGES_FOLDER = PROJECT_FOLDER / "images"

# Raspberry Pi's endpoint
PI_ADDRESS = "http://raspberrypi.local:5000/capture"


def capture_img_from_pi():
    """
    Make a request to Raspberry Pi to capture an image
    and save the returned JPEG in the laptop project's images folder.
    Returns path location of saved image.
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


def run_monitoring_cycle():
    """
    This function runs a single infant monitoring cycle.
    One image is captured, inserted into database, processed
    by AI models, output responses stored.
    """

    image_path = capture_img_from_pi()

    # Stop the session of the image could not be captured
    if image_path is None:
        return False

    # Insert newly captured image to db
    image_id = insert_image(image_path)

    print(f"Image inserted into database. ID: {image_id}")

    print(f"Performing AI processing for: {image_path.name}")

    # Process the image and associate all outputs with its database ID
    process_img_ai(image_id, image_path)

    return True


def run_monitoring_session(interval_minutes, duration_hours):
    """
    Runs monitoring cycle function repeatedly for the set duration.
    """

    interval_seconds = interval_minutes * 60

    total_cycles = int((duration_hours * 60) / interval_minutes)

    print(
        f"Starting monitoring session.\n"
        f"Duration: {duration_hours} hours\n"
        f"Interval: {interval_minutes} minutes\n"
        f"Total captures: {total_cycles}"
    )

    for cycle in range(total_cycles):

        run_monitoring_cycle()

        # Wait only if another monitoring cycle will be executed.
        # After the final image, exit the program immediately.
        if cycle < total_cycles - 1:
            print(f"Waiting {interval_minutes} minutes.")

            time.sleep(interval_seconds)

    print("\nMonitoring session complete.")


def main():
    run_monitoring_cycle()
    # to add frequency here


if __name__ == "__main__":
    main()