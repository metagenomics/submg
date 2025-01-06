# Importing necessary modules
import customtkinter as ctk
import yaml
import platform

from tkinter import filedialog
from tkinter.messagebox import showinfo, showerror
from submg.gui.base import BasePage
from submg.modules.utility import validate_parameter_combination


class LoadConfigPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submission Setup")

        # Create mainFrame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew")  # Allow main frame to stretch both vertically and horizontally

        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Allow main frame to expand
        main_frame.grid_columnconfigure(0, weight=1)  # Equal sizing for info label
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Image Label
        image_frame = ctk.CTkFrame(main_frame)
        image_frame.grid(row=0,
                         column=1,
                         rowspan=2,
                         padx=10,
                         pady=(0,10),
                         sticky="ns")
        image_label = ctk.CTkLabel(
            image_frame,
            image=self.controller.submodes_img,
            text="",
        )
        image_label.grid(row=1,
                         column=0,
                         padx=10,
                         pady=(0,0))
        
        image_title = ctk.CTkLabel(
            image_frame,
            text="Valid Submission Combinations",
            font=("Arial", 16),
            justify='left',
            wraplength=450
        )
        image_title.grid(row=0,
                         column=0,
                         padx=(0,15),
                         pady=(5,10),
                         sticky="ne")

        # Info Label
        info_label = ctk.CTkLabel(
            main_frame,
            text="Please choose an existing config file from your disk. "
                 "\n\n"
                 "Depending on your config file, the tool might automatically "
                 "derive which data you want to submit. Otherwise, please "
                 "choose the correct submission items manually."
                 "\n\n"
                 "You have to pick a staging directory on your local disk. "
                 "This directory will be used to store temporary files and "
                 "record all logs written during submission. Please select "
                 "an empty directory for this."
                 "\n\n"
                 "Your study has to exist on the server you are submitting to. ",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=650
        )
        info_label.grid(row=0,
                        column=0,
                        padx=10,
                        pady=10,
                        sticky="nw")  # Align to the top-left corner

        # bl_frame
        bl_frame = ctk.CTkFrame(main_frame,
                                fg_color="transparent")
        bl_frame.grid(row=1,
                      column=0,
                      padx=(20,0),
                      pady=10,
                      sticky="nsew")
        bl_frame.grid_columnconfigure(0, weight=1)  # Stretch the left frame
        bl_frame.grid_columnconfigure(1, weight=1)
        bl_frame.grid_rowconfigure(0, weight=1)

        # File Picker
        picker_frame = ctk.CTkFrame(bl_frame)
        picker_frame.grid(row=0,
                          column=0,
                          padx=0,
                          pady=0,
                          sticky="nsew")
        picker_frame.grid_columnconfigure(0, weight=1)  # Stretch the right frame
        

        # Title
        middle_label = ctk.CTkLabel(
            picker_frame,
            text="Input / Output",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=350
        )
        middle_label.grid(row=0, column=0, padx=10, pady=(10, 10), columnspan=2, sticky="n")

        self.file_path = ""
        self.staging_dir_path = ""

        file_picker_button = ctk.CTkButton(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Config File", 
            command=self.pick_config
        )
        file_picker_button.grid(row=1, column=0, padx=10, pady=(10,0), sticky="ew")

        self.file_path_label = ctk.CTkLabel(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="No file selected",  # Will display the selected file path
            anchor="w"
        )
        self.file_path_label.grid(row=2, column=0, padx=10, pady=(0,20), sticky="ew")

        staging_dir_picker_button = ctk.CTkButton(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="Pick Staging Directory", 
            command=self.pick_staging_dir
        )
        staging_dir_picker_button.grid(row=3, column=0, padx=10, pady=(10,0), sticky="ew")

        self.staging_dir_label = ctk.CTkLabel(
            picker_frame, 
            font=('Arial',self.controller.fontsize),
            text="No directory selected",  # Will display the selected dir path
            anchor="w",
        )
        self.staging_dir_label.grid(row=4, column=0, padx=10, pady=(0,20), sticky="ew")

        # Checkboxes
        self.checkbox_frame = ctk.CTkFrame(bl_frame)
        self.checkbox_frame.grid(row=0, column=1, padx=(10,10), pady=0, sticky="nsew")
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
                                                text="Submit Samples",
                                                state="disabled")
        self.checkbox_samples.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_reads = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Reads",
                                                state="disabled")
        self.checkbox_reads.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_assembly = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Assembly",
                                                state="disabled")
        self.checkbox_assembly.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_bins = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit Binned Contigs",
                                                state="disabled")
        self.checkbox_bins.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_mags = ctk.CTkCheckBox(self.checkbox_frame,
                                                text="Submit MAGs",
                                                state="disabled")
        self.checkbox_mags.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.edit_button = ctk.CTkButton(
            button_frame,
            font=('Arial',self.controller.fontsize),
            text="Edit Config",
            command=lambda: self.controller.show_page("ConfigFormPage"),
            state="disabled"
        )
        self.edit_button.grid(row=0, column=0, padx=0, pady=(0,10), sticky="ew")

        self.start_button = ctk.CTkButton(
            button_frame, 
            font=('Arial',self.controller.fontsize),
            text="Submit with Config", 
            command=self.continue_submission,
            state="disabled"
        )
        self.start_button.grid(row=0, column=1, padx=(5,0), pady=(0,10), sticky="ew")

    def initialize_vars(self):
        # Initialize variables
        self.max_display_len = 30
        self.file_path = ""
        self.staging_dir_path = ""
        self.file_path_label.configure(text="No file selected")
        self.staging_dir_label.configure(text="No directory selected")
        if "form_path" in self.controller.config_items and self.controller.config_items["form_path"]:
            self.file_path = self.controller.config_items["form_path"]
            self.file_path_label.configure(
                text=self.controller.truncate_display_path(
                     self.file_path,
                     self.max_display_len)
            )

    def global_disable(self):
        """ Disable all checkboxes and the start and edit buttons"""
        self.checkbox_samples.configure(state="disabled")
        self.checkbox_reads.configure(state="disabled")
        self.checkbox_assembly.configure(state="disabled")
        self.checkbox_bins.configure(state="disabled")
        self.checkbox_mags.configure(state="disabled")

        if not self.file_path:
            self.file_path_label.configure(text="No file selected")
        
        self.staging_dir_label.configure(text="No directory selected")

        self.checkbox_samples.deselect()
        self.checkbox_reads.deselect()
        self.checkbox_assembly.deselect()
        self.checkbox_bins.deselect()
        self.checkbox_mags.deselect()

        self.edit_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
    
    def pick_config(self):
        file_path = filedialog.askopenfilename(title="Choose Config File")
        if file_path:
            display_path = self.controller.truncate_display_path(
                file_path,
                self.max_display_len)
            self.file_path_label.configure(text=display_path)
            self.file_path = file_path
            self.load_config()

    def load_config(self):
        """ Open a file dialog to select a config file.
            Derive a submission outline if possible.
        """
        if self.file_path:
            # Try loading the yaml
            try:
                with open(self.file_path, "r") as file:
                    config = yaml.safe_load(file)
            except Exception as e:
                showinfo(
                    ("Invalid Config File"),
                    f"Could not load the config file. Error: {e}",
                )
                return
            
            # Check whether this is a Windows system
            if platform.system().lower() == "windows":
                # If it is: Check if the config is Windows compatible
                # (issue: pysam doesn't work on Windows, so we cannot process BAM files)
                if "BAM_FILES" in config:
                    showerror(
                        "Invalid Config File",
                        "This configuration file is set up to derive coverage from BAM files. This is not supported on Windows systems."
                    )
                    return
            
            # Enable the checkboxes
            self.checkbox_samples.configure(state="normal")
            self.checkbox_reads.configure(state="normal")
            self.checkbox_assembly.configure(state="normal")
            self.checkbox_bins.configure(state="normal")
            self.checkbox_mags.configure(state="normal")

            # Enable the edit button
            self.edit_button.configure(state="normal")

            if 'submission_outline' in config:
                # Set the checkboxes according to the config
                outline_items = config['submission_outline']
                if 'samples' in outline_items:
                    self.checkbox_samples.select()
                if 'reads' in outline_items:
                    self.checkbox_reads.select()
                if 'assembly' in outline_items:
                    self.checkbox_assembly.select()
                if 'bins' in outline_items:
                    self.checkbox_bins.select()
                if 'mags' in outline_items:
                    self.checkbox_mags.select()
                # Set the submission outline in the controller
                self.controller.submission_items = {
                    "samples": 'samples' in outline_items,
                    "reads": 'reads' in outline_items,
                    "assembly": 'assembly' in outline_items,
                    "bins": 'bins' in outline_items,
                    "mags": 'mags' in outline_items,
                }
                
         
            else:
                showinfo(
                    ("No Outline Items"),
                    "The config file does not contain an 'outline_items' "
                    "defining which data you intend to submit. "
                    "Please select the submission items manually.",
                )

            self.controller.config_items['form_path'] = self.file_path

            # Enable the start button if staging directory is also selected
            if self.staging_dir_path:
                self.start_button.configure(state="normal")

    def pick_staging_dir(self):
        # Use tkFileDialog.askdirectory() to select a directory
        dir_path = filedialog.askdirectory(title="Choose Output Directory")
        if dir_path:
            self.staging_dir_path = dir_path
            display_path = self.controller.truncate_display_path(dir_path,
                                                                 self.max_display_len)
            self.staging_dir_label.configure(text=display_path)

            # Enable the start button if config file is also selected
            if self.file_path:
                self.start_button.configure(state="normal")

    def continue_submission(self):
        # Do we have config & path?
        config_file = self.file_path
        staging_dir = self.staging_dir_path
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
        self.initialize_vars()
        self.global_disable()
        if self.file_path:
            self.load_config()