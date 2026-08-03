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
        # PhotoImage object reference required for Tkinter
        self.image_for_tk = None
        # Radio buttons to share this variable to identify the assessment selected
        self.assessment_var = tk.StringVar()

        # Configure main application window
        self.root.title("Parent Sleep Safety Assessment")
        self.root.geometry("850x800")

        self.create_widgets()

        # Display the first image when records are found
        if self.image_records:
            self.display_current_image()

        else:
            # Nothing to assess
            messagebox.showinfo("No captured images to assess!")
            # Close gui
            self.root.destroy()

    def create_widgets(self):
        """
        Creates and positions the GUI widgets.
        1. Image progression (Image 1 of x)
        2. Image filename
        3. Image display
        4. Three assessment options (no concern, possible, serious)
        5. Explanation box
        6. Save and continue/next button
        """
