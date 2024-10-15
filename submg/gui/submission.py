# submission.py
import customtkinter as ctk
from tkinter import filedialog
from tkinter.messagebox import showinfo
from .base import BasePage
from ..modules.utility import validate_parameter_combination


class SubmissionPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submission Setup")

        # Create mainFrame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew")  # Allow main frame to stretch both vertically and horizontally

        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Allow main frame to expand
        main_frame.grid_columnconfigure(0, weight=1)  # Equal sizing for info label
        main_frame.grid_columnconfigure(1, weight=1)  # Equal sizing for middle frame
        main_frame.grid_columnconfigure(2, weight=1)  # Equal sizing for right frame (Submission Items)

        # Info Label
        info_label = ctk.CTkLabel(
            main_frame,
            text="Pick your config file and choose which data you want to "
                 "submit. "
                 "\n\n"
                 "ENA provides a development service to trial your submission "
                 "before uploading your data to the production server. We "
                 "strongly suggest submitting to the production server only "
                 "after a test submission with identical parameters was "
                 "successful. Disable the \"Use Test Server\" switch to submit "
                 "to the production server."
                 "\n\n"
                 "Your study has to exist on the server you are submitting to. ",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        info_label.grid(row=0, column=0, padx=(20,0), pady=20, sticky="nw")  # Align to the top-left corner

        middle_frame = ctk.CTkFrame(main_frame)
        middle_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        middle_frame.grid_columnconfigure(0, weight=1)  # Stretch the right frame

        middle_label = ctk.CTkLabel(
            middle_frame,
            text="Input / Output",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        middle_label.grid(row=0, column=0, padx=10, pady=(5, 0), columnspan=2, sticky="n")

        # File Picker
        self.file_path = ctk.StringVar("")
        self.display_path = ctk.StringVar("")
        self.display_path.set("No file selected")

        file_picker_button = ctk.CTkButton(
            middle_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Config File", 
            command=self.pick_file
        )
        file_picker_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # File path display
        file_path_label = ctk.CTkLabel(
            middle_frame, 
            font=('Arial',self.controller.fontsize),
            textvariable=self.display_path,  # Will display the selected file path
            anchor="w"
        )
        file_path_label.grid(row=1, column=1, padx=10, pady=0, sticky="ew")

        # Dir picker
        self.staging_dir_path = ctk.StringVar("")
        self.staging_dir_display = ctk.StringVar("")
        self.staging_dir_display.set("No directory selected")

        staging_dir_picker_button = ctk.CTkButton(
            middle_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Staging Directory", 
            command=self.pick_staging_dir
        )
        staging_dir_picker_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Staging dir path display
        staging_dir_label = ctk.CTkLabel(
            middle_frame, 
            font=('Arial',self.controller.fontsize),
            textvariable=self.staging_dir_display,  # Will display the selected dir path
            anchor="w"
        )
        staging_dir_label.grid(row=2, column=1, padx=10, pady=0, sticky="ew")

        # Checkboxes
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=2, padx=(0,20), pady=10, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)  # Stretch the frame

        right_label = ctk.CTkLabel(
            right_frame,
            text="Submission Items",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        right_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="n")

        self.checkbox_samples = ctk.CTkCheckBox(right_frame,
                                                text="Submit Samples")
        self.checkbox_samples.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_reads = ctk.CTkCheckBox(right_frame,
                                                text="Submit Reads")
        self.checkbox_reads.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_assembly = ctk.CTkCheckBox(right_frame,
                                                text="Submit Assembly")
        self.checkbox_assembly.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_bins = ctk.CTkCheckBox(right_frame,
                                                text="Submit Binned Contigs")
        self.checkbox_bins.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_mags = ctk.CTkCheckBox(right_frame,
                                                text="Submit MAGs")
        self.checkbox_mags.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        start_frame = ctk.CTkFrame(self, fg_color="transparent")
        start_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        start_frame.grid_columnconfigure(0, weight=1)  # Stretch

        start_button = ctk.CTkButton(
            start_frame, 
            font=('Arial',self.controller.fontsize),
            text="Continue", 
            command=self.continue_submission
        )
        start_button.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

    def pick_file(self):
        # Open file dialog and store the selected file path
        max_display_len = 12
        file_path = filedialog.askopenfilename(title="Choose Config File")
        if file_path:
            self.file_path.set(file_path)
            display_path = self.controller.truncate_display_path(file_path,
                                                                 max_display_len)
            self.display_path.set(display_path)

    def pick_staging_dir(self):
        # Use tkFileDialog.askdirectory() to select a directory
        max_display_len = 12
        dir_path = filedialog.askdirectory(title="Choose Output Directory")
        if dir_path:
            self.staging_dir_path.set(dir_path)
            display_path = self.controller.truncate_display_path(dir_path,
                                                                 max_display_len)
            self.staging_dir_display.set(display_path)

    def continue_submission(self):
        # Do we have config & path?
        config_file = self.file_path.get()
        staging_dir = self.staging_dir_path.get()
        if not config_file:
            showinfo(
                ("Invalid Parameters"),
                "Please select a config file.",
            )
            return
        if not staging_dir:
            showinfo(
                ("Invalid Parameters"),
                "Please select a staging directory.",
            )
            return
        
        # Is the parameter combination valid?
        if not validate_parameter_combination(
            submit_samples=self.checkbox_samples.get(),
            submit_reads=self.checkbox_reads.get(),
            submit_assembly=self.checkbox_assembly.get(),
            submit_bins=self.checkbox_bins.get(),
            submit_mags=self.checkbox_mags.get(),
            exit_on_invalid=False,
        ):
            showinfo(
                ("Invalid Parameters"),
                "The combination of submission items is not valid. "
                "Please consider the 'submission modes' section of the manual "
                "for more information.",
            )
            return
        
        # Set the submission data
        self.controller.set_submission_data(
            file_path=config_file,
            staging_dir_path=staging_dir,
            submission_items={
                "samples": self.checkbox_samples.get(),
                "reads": self.checkbox_reads.get(),
                "assembly": self.checkbox_assembly.get(),
                "bins": self.checkbox_bins.get(),
                "mags": self.checkbox_mags.get(),
            },
        )
        
        # Redirect to MonitorPage
        self.controller.show_page("MonitorPage")

    def initialize(self):
        """Called whenever monitor renders the page"""
        pass