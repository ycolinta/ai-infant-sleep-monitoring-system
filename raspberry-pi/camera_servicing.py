from flask import Flask, send_file
from datetime import datetime
from camera_script import capture_img
from pathlib import Path

CAPTURE_FOLDER = Path(__file__).parent / "captured_images"

app = Flask(__name__)


# ---------------------------- HOME ----------------------------
@app.route("/")
def index():
    # A string for now
    return "Infant Sleep Monitoring System"


# ---------------------------- CAPTURE ----------------------------
@app.route("/capture", methods=["POST"])
def capture():

    # Make sure the folder where images captured will go exists
    CAPTURE_FOLDER.mkdir(exist_ok=True)

    # Create a unique file name for each image captured
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = CAPTURE_FOLDER / f"capture_{timestamp}.jpg"

    # Capture the image 
    capture_img(image_path)

    # Return image to the client 
    return send_file(
        image_path,
        mimetype="image/jpeg",
        as_attachment=False
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
