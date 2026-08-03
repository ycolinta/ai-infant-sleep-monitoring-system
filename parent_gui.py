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
        self.progress_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 20)
        )
        self.progress_label.pack(pady=(15, 5))

        # This label holds the image
        self.image_label = tk.Label(self.root)
        self.image_label.pack(padx=20, pady=10)

        # Section heading above the parent assessment options.
        assessment_title = tk.Label(
            self.root,
            text="Parent Assessment",
            font=("Arial", 14, "bold")
        )
        assessment_title.pack(pady=(10, 5))

        # The three radio buttons share assessment_var.
        # Selecting one automatically deselects the others.
        tk.Radiobutton(
            self.root,
            text="No apparent safety concerns",
            variable=self.assessment_var,
            value="no_apparent_safety_concerns",
            font=("Arial", 11)
        ).pack(anchor="w", padx=100)

        tk.Radiobutton(
            self.root,
            text="Possible safety concerns",
            variable=self.assessment_var,
            value="possible_safety_concerns",
            font=("Arial", 11)
        ).pack(anchor="w", padx=100)

        tk.Radiobutton(
            self.root,
            text="Serious safety concerns",
            variable=self.assessment_var,
            value="serious_safety_concerns",
            font=("Arial", 11)
        ).pack(anchor="w", padx=100)

        # Label above the explanation box
        explanation_label = tk.Label(
            self.root,
            text="Explanation:",
            font=("Arial", 11)
        )
        explanation_label.pack(anchor="w", padx=100, pady=(15, 5))

        # Multi-line box for the parent's explanation
        self.explanation_text = tk.Text(
            self.root,
            width=70,
            height=5,
            wrap="word"
        )
        self.explanation_text.pack(padx=100, pady=(0, 15))

        # Saves the assessment and loads the next image
        tk.Button(
            self.root,
            text="Save Assessment and View Next Image",
            command=self.save_assessment,
            font=("Arial", 11),
            padx=15,
            pady=8
        ).pack(pady=10)

    def display_current_image(self):
        """
        Loads and displays the image at the current position.
        """

        image_record = self.image_records[self.current_index]

        # The database stores a path relative to the project folder.
        image_path = PROJECT_FOLDER / image_record["file_path"]

        if not image_path.exists():
            messagebox.showerror(f"Image {image_path} Not Found")
            return

        try:
            # Open the JPEG and create a memory copy.
            with Image.open(image_path) as source_image:
                image = source_image.copy()

        except OSError as error:
            messagebox.showerror(f"Image Error. Could not be opened {error}")
            return

        # Resize the image so it fits in the GUI
        # while preserving its original proportions.
        image.thumbnail((750, 450), Image.Resampling.LANCZOS)

        # Convert the Pillow image into a Tkinter image
        self.displayed_photo = ImageTk.PhotoImage(image)

        # Show the image inside image_label
        self.image_label.configure(image=self.displayed_photo)

        # Show progress, such as "Image 1 of 3"
        self.progress_label.configure(
            text=(
                f"Image {self.current_index + 1} "
                f"of {len(self.image_records)}"
            )
        )

        # Clear the previous image's inputs
        self.assessment_var.set("")
        self.explanation_text.delete("1.0", tk.END)

    def save_assessment(self):
        """
        Validates and stores the parent assessment.
        Then displays the next image.
        """

        selected_assessment = self.assessment_var.get()

        # Require one category to be selected
        if not selected_assessment:
            messagebox.showwarning("Assessment Required", "Please select one safety assessment.")
            return

        # Read the explanation entered by the parent
        explanation = self.explanation_text.get("1.0", tk.END).strip()

        # Require an explanation
        if not explanation:
            messagebox.showwarning("Explanation Required", "Please enter a brief explanation or NA.")
            return

        image_record = self.image_records[self.current_index]

        # Convert the selected category into the same format
        # used by the AI model responses.
        response_obj = {
            "no_apparent_safety_concerns": (
                    selected_assessment
                    == "no_apparent_safety_concerns"
            ),
            "possible_safety_concerns": (
                    selected_assessment
                    == "possible_safety_concerns"
            ),
            "serious_safety_concerns": (
                    selected_assessment
                    == "serious_safety_concerns"
            ),
            "explanation": explanation
        }

        # Insert the parent assessment into the Response table
        inserted = insert_response(
            image_record["image_id"],
            PARENT_MODEL_NAME,
            response_obj
        )

        if not inserted:
            messagebox.showerror("Assessment Not Saved", "The parent assessment could not be inserted.")
            return

        # Move to the next image
        self.current_index += 1

        if self.current_index < len(self.image_records):
            self.display_current_image()
        else:
            messagebox.showinfo("Assessments Complete", "All captured images have been assessed.")
            self.root.destroy()


def open_parent_gui(image_ids):
    """
    Opens the GUI for the images created during
    the completed monitoring session.
    """

    root = tk.Tk()

    ParentAssessmentGUI(root, image_ids)

    root.mainloop()