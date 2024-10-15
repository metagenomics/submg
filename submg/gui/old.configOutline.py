# pages/configOutline.py
import customtkinter as ctk
from .base import BasePage

from tkinter import messagebox 


class ConfigOutlinePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Outline")


        mainFrame = ctk.CTkFrame(self, fg_color="transparent")
        mainFrame.grid(row=1, column=0, sticky="ew")  # Horizontal stretching only
        
        mainFrame.grid_rowconfigure(0, weight=0)  # Content row, no vertical scaling
        mainFrame.grid_rowconfigure(1, weight=0)  # Content row, no vertical scaling
        mainFrame.grid_columnconfigure(0, weight=0)  # Left column for text scales horizontally
        mainFrame.grid_columnconfigure(1, weight=1)  # Right column for image scales horizontally


        leftFrame = ctk.CTkFrame(mainFrame, fg_color="transparent")
        leftFrame.grid(row=0, column=0, sticky="ew")  # Horizontal stretching only
        # No stretching, content stays at the top
        leftFrame.grid_rowconfigure(0, weight=0)
        leftFrame.grid_columnconfigure(0, weight=1)

        # Add an infotext
        info_text = (
            "Choose which data to submit. Valid submission combinations are "
            "illustrated below. You will need a registered study in the ENA "
            "before you can start peparing your submission. "
        )
        text_label = ctk.CTkLabel(
            leftFrame,
            text=info_text,
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=500  # Adjust wraplength as needed
        )
        text_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="n")

        # Add submission modes image
        #submodes_img = controller.submodes_img
        #image_label = ctk.CTkLabel(
        #    mainFrame,
        #    image=submodes_img,
        #    text=""  # No text
        #)
        #image_label.grid(row=0, column=1, padx=20, pady=20, sticky="new")


        # Checkbox for "Samples"
        self.samples_checkbox = ctk.CTkCheckBox(leftFrame,
                                                text="Samples",
                                                command=self.toggle_samples_field)
        self.samples_checkbox.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        # Samples help button
        samples_help_button = ctk.CTkButton(
            leftFrame,
            text="?",
            font=("Arial", self.controller.fontsize),
            command=lambda: messagebox.showinfo(
                "Help",
                "Select this option if you want to submit samples."
            )
        )
        samples_help_button.grid(row=1, column=1, padx=20, pady=20, sticky="w")


        # Field to enter the number (initially hidden)
        self.samples_entry = ctk.CTkEntry(leftFrame,
                                          placeholder_text="Enter number of samples")
        self.samples_entry.grid(row=1, column=2, sticky="w")
        self.samples_entry.grid_remove()  # Initially hide the entry field



        # Buttons
        button_frame = ctk.CTkFrame(mainFrame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=1, pady=20, sticky="ew")

        # Configure the button_frame columns to center the buttons
        button_frame.grid_columnconfigure(0, weight=0)
        button_frame.grid_columnconfigure(1, weight=0)



    def toggle_samples_field(self):
        # Show or hide the entry field based on checkbox state
        if self.samples_checkbox.get() == 1:
            self.samples_entry.grid()  # Show the entry field
        else:
            self.samples_entry.grid_remove()  # Hide the entry field

    def initialize(self):
        """Called whenever monitor renders the page"""
        pass