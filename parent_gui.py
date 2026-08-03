import tkinter as tk

from pathlib import Path
from tkinter import messagebox
from PIL import Image, ImageTk

from database import get_images_by_ids, insert_response

# Main project folder
PROJECT_FOLDER = Path(__file__).parent

# Parent model name stored in the database's Model table.
PARENT_MODEL_NAME = "Human-Parent Assessor"

class ParentAssessmentGUI:
    """
    Displays the images captured during a monitoring session
    and collects a parent safety assessment for each image.
    """
    def __init__(self, root, image_ids):
        self.root = root # storing the main Tkinter window
        self.image_records = get_images_by_ids(image_ids)

        # Begin with first image in the list
        self.current_index = 0



