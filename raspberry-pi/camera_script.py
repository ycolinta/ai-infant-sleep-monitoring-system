from picamera2 import Picamera2
from pathlib import Path
from datetime import datetime

# Folder that captures Raspberry Pi's camera shots
CAPTURE_FOLDER = Path(__file__).parent / "captured_images"

def capture_img(image_path):
    """
    Function that captures an image using the Raspberry Pi camera
    and saves it to the provided image path parameter.
    """

    # Verify destination folder exists
    image_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the Picamera2 camera object
    picam2 = Picamera2()

    try:
        # Generate a configuration suitable for capturing a high-resolution still image
        # Size is from camera's listed capability
        config = picam2.create_still_configuration(main={"size": (4608, 2592)})

        # Apply still image configuration with configure() method
        picam2.configure(config)

        # Start the camera
        picam2.start()

        # Allow the camera to automatically focus before capturing
        picam2.autofocus_cycle()

        # Capture and save the image with capture_file() method
        picam2.capture_file(str(image_path))

    finally:
        # Stop and close camera when done
        picam2.stop()
        picam2.close()

    # Return image path so Flask can send the image back to AI image processing functions
    return image_path


def main():

    # Create unique file name for each image using current timestamp
    file_name = f"capture_{timestamp}.jpg"

    # Define the location and filename for the captured image
    image_path = CAPTURE_FOLDER / file_name

    saved_path = capture_img(image_path)

    print(f"Test image saved: {saved_path}")


if __name__ == "__main__":
    main()
