import requests
import time

from datetime import datetime
from pathlib import Path

from database import insert_image, get_comparison_table, print_comparison_table, summarize_session_comparisons, print_summary_comparisons
from ai_processing import process_img_ai
from parent_gui import open_parent_gui

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
    by AI models. Returns image_id of the captures images.
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

    return image_id


def run_monitoring_session(interval_minutes, duration_hours):
    """
    Runs monitoring cycle function repeatedly for the set duration.
    Returns a list containing the image IDs created during the run.
    """

    interval_seconds = interval_minutes * 60

    total_cycles = int((duration_hours * 60) / interval_minutes)

    session_img_ids = []

    print(
        f"Starting monitoring session.\n"
        f"Duration: {duration_hours} hours\n"
        f"Interval: {interval_minutes} minutes\n"
        f"Total captures: {total_cycles}"
    )

    for cycle in range(total_cycles):

        image_id = run_monitoring_cycle()

        if image_id is not None:
            session_img_ids.append(image_id)

        # Wait only if another monitoring cycle will be executed.
        # After the final image, exit the program immediately.
        if cycle < total_cycles - 1:
            print(f"Waiting {interval_minutes} minutes.")
            time.sleep(interval_seconds)

    print("\nMonitoring session complete.")

    return session_img_ids


def main():
    # to add frequency here
    session_img_ids = run_monitoring_session(interval_minutes=1, duration_hours=1/60)

    if not session_img_ids:
        return

    open_parent_gui(session_img_ids)

    comparison_rows = get_comparison_table(session_img_ids)

    print_comparison_table(comparison_rows)

    model_summary = summarize_session_comparisons(comparison_rows)

    print_summary_comparisons(model_summary)


if __name__ == "__main__":
    main()