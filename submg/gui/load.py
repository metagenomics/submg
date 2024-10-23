# load.py
import customtkinter as ctk
from tkinter import filedialog
from tkinter.messagebox import showinfo
from .base import BasePage
from ..modules.utility import validate_parameter_combination


class LoadConfigPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submission Setup")

        # Create mainFrame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew")  # Allow main frame to stretch both vertically and horizontally

        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Allow main frame to expand
        main_frame.grid_columnconfigure(0, weight=2)  # Equal sizing for info label
        main_frame.grid_columnconfigure(1, weight=1)

        # Info Label
        info_label = ctk.CTkLabel(
            main_frame,
            text="You can open an existing config file from the disk. "
                 "\n\n"
                 "Depending on your config file, the tool might automatically "
                 "derive which data you want to submit. Otherwise, please "
                 "choose the correct submission options manually."
                 "\n\n"
                 "You have to pick a staging directory on your local disk. "
                 "This directory will be used to store temporary files and "
                 "record all logs written during submission. Please select "
                 "an empty directory for this."
                 "\n\n"
                 "Your study has to exist on the server you are submitting to. ",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=450
        )
        info_label.grid(row=0, column=1, padx=(20, 20), pady=20, sticky="w")  # Align to the top-left corner

        # File Picker
        picker_frame = ctk.CTkFrame(main_frame)
        picker_frame.grid(row=0,
                          column=0,
                          padx=10,
                          pady=10,
                          sticky="nsew")
        picker_frame.grid_columnconfigure(0, weight=0)  # Stretch the right frame
        picker_frame.grid_columnconfigure(1, weight=3)
        

        # Title
        middle_label = ctk.CTkLabel(
            picker_frame,
            text="Input / Output",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        middle_label.grid(row=0, column=0, padx=10, pady=(10, 10), columnspan=2, sticky="n")

        # Pickers
        self.file_path = ctk.StringVar("")
        self.display_path = ctk.StringVar("")
        self.display_path.set("No file selected")

        file_picker_button = ctk.CTkButton(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Config File", 
            command=self.pick_file
        )
        file_picker_button.grid(row=1, column=0, padx=10, pady=(10,0), sticky="ew")

        # File path display
        file_path_label = ctk.CTkLabel(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            textvariable=self.display_path,  # Will display the selected file path
            anchor="e"
        )
        file_path_label.grid(row=1, column=1, padx=10, pady=(10,0), sticky="ew")

        # Dir picker
        self.staging_dir_path = ctk.StringVar("")
        self.staging_dir_display = ctk.StringVar("")
        self.staging_dir_display.set("No directory selected")

        staging_dir_picker_button = ctk.CTkButton(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Staging Directory", 
            command=self.pick_staging_dir
        )
        staging_dir_picker_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Staging dir path display
        staging_dir_label = ctk.CTkLabel(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            textvariable=self.staging_dir_display,  # Will display the selected dir path
            anchor="e",
        )
        staging_dir_label.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Checkboxes
        self.checkbox_frame = ctk.CTkFrame(main_frame)
        #checkbox_frame.grid(row=2, column=1, padx=(10,10), pady=10, sticky="nsew")
        self.checkbox_frame.grid_columnconfigure(0, weight=1)  # Stretch the frame

        right_label = ctk.CTkLabel(
            self.checkbox_frame,
            text="Submission Items",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        right_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="n")

        self.checkbox_samples = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Samples")
        self.checkbox_samples.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_reads = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Reads")
        self.checkbox_reads.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_assembly = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Assembly")
        self.checkbox_assembly.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_bins = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Binned Contigs")
        self.checkbox_bins.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_mags = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit MAGs")
        self.checkbox_mags.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        start_frame = ctk.CTkFrame(self, fg_color="transparent")
        start_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
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
        max_display_len = 30
        file_path = filedialog.askopenfilename(title="Choose Config File")
        if file_path:
            self.file_path.set(file_path)
            display_path = self.controller.truncate_display_path(file_path,
                                                                 max_display_len)
            self.display_path.set(display_path)
            self.checkbox_frame.grid(row=2, column=0, padx=(10,10), pady=10, sticky="nsew")

    def pick_staging_dir(self):
        # Use tkFileDialog.askdirectory() to select a directory
        max_display_len = 30
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