# home.py
import customtkinter as ctk
from .base import BasePage
import webbrowser
from tkinter.messagebox import askyesno

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Home")

        self.ena_register_study_address = "https://ena-docs.readthedocs.io/en/latest/submit/study.html"

        # Create main_frame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="ew")  # Horizontal stretching only

        # Configure grid
        self.grid_rowconfigure(1, weight=0)  # No vertical scaling, content stays at the top
        main_frame.grid_rowconfigure(0, weight=0)  # Content row, no vertical scaling
        main_frame.grid_columnconfigure(0, weight=1)  # Left column for text scales horizontally
        main_frame.grid_columnconfigure(1, weight=1)  # Right column for image scales horizontally

        # Left side - Text field with lorem ipsum
        info_text = (
            "subMG aids in the submission of metagenomic study data to the "
            "European Nucleotide Archive (ENA). "
            "The tool can be used to submit various combinations of samples, "
            "reads, (co-)assemblies, bins and MAGs. "
            "\n\n"
            "After you enter your (meta)data in a configuration form, subMG "
            "derives additional information where required, creates "
            "samplesheets and manifests and finally uploads everything to your "
            "ENA account. "
            "\n\n"
            "Before you can start, you need a registered study in the ENA. "
            "If you do not have one yet, click the 'Register Study' button."
            "\n\n"
            "If you don't have a configuration form ready, start with the "
            "'Prepare Submission' option. Otherwise, proceed to 'Submit Data'."
            )
        text_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=400  # Adjust wraplength as needed
        )
        text_label.grid(row=0, column=0, padx=20, pady=20, sticky="new")  # Stretches horizontally

        # Right side - Image
        flow_img = controller.flow_img
        image_label = ctk.CTkLabel(
            main_frame,
            image=flow_img,
            text=""  # No text
        )
        image_label.grid(row=0, column=1, padx=20, pady=20, sticky="new")  # Stretches horizontally

        # Buttons - Place them below the content, spanning both columns
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=1, pady=10, sticky="ew")

        # Configure the button_frame columns to center the buttons
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        # Button 3 - Register Study (opens https://ena-docs.readthedocs.io/en/latest/submit/study.html in the web browser)
        register_study_button = ctk.CTkButton(
            button_frame,
            text_color="#3a7ebf",
            hover_color="#b6d5de",
            fg_color="transparent",
            border_color="#3a7ebf", 
            border_width=1,
            text="Register Study",
            font=('Arial',self.controller.fontsize),
            command=self.register_study
        )
        register_study_button.grid(row=0, column=0, padx=20, sticky="ew")

        # Button 1 - Prepare Submission
        prepare_button = ctk.CTkButton(
            button_frame,
            text="Prepare Submission",
            font=('Arial',self.controller.fontsize),
            command=lambda: controller.show_page("ConfigOutlinePage")
        )
        prepare_button.grid(row=0, column=1, padx=0, sticky="ew")

        # Button 2 - Submit Data
        submit_button = ctk.CTkButton(
            button_frame,
            text="Submit Data",
            font=('Arial',self.controller.fontsize),
            command=self.switch_to_submission
        )
        submit_button.grid(row=0, column=2, padx=20, sticky="ew")
    
    def register_study(self):
        msg = ("This will open the ENA documentation in your web browser. "
               "\n\nContinue?")
        if askyesno("Register Study", msg):
            webbrowser.open(self.ena_register_study_address)

    def switch_to_submission(self):
        # Ask user if they are sure they want to submit data. Explain
        # that this option is only if they have a configuration file
        # ready.
        msg = ("To directly submit data, you need to have a configuration "
                "file already prepared. If you don't have one, please use "
                "the 'Prepare Submission' option instead. "
                "\n\nContinue?")
        if askyesno("Submit Data", msg):
            self.controller.show_page("SubmissionPage")

