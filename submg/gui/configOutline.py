import os
import sys
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox, IntVar
from tkinter.messagebox import showinfo
from .base import BasePage
from ..modules.utility import validate_parameter_combination
from ..core import makecfg_through_gui

class ConfigOutlinePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Outline")
        self.controller = controller  # Store the controller for path truncation

        self.initialize_vars()

        # Create mainFrame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew")  # Allow main frame to stretch both vertically and horizontally

        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Allow main frame to expand
        main_frame.grid_columnconfigure(0, weight=1)  # Equal sizing for info label
        main_frame.grid_columnconfigure(1, weight=1)  # Equal sizing for middle frame

        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(10, 0), columnspan=2, sticky="nsew")
        left_frame.grid_rowconfigure(0, weight=1)  # Stretch the left frame

        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=(0, 10), pady=(0, 10), sticky="e")

        # Add an infotext
        info_label = ctk.CTkLabel(
            left_frame,
            text="Choose what data you intend to submit. Valid submission "
                 "combinations are illustrated on the right. "
                 "For some items (e.g. samples), you need to specify how many "
                 "of them you are submitting. "
                 "\n\n"
                 "You will need a registered study in the ENA "
                 "before you can start preparing your submission. "
                 "\n\n"
                 "Consult the manual for more information on submission items "
                 "and coverage options.",
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=650
        )
        info_label.grid(row=0,
                        column=0,
                        padx=(20, 20),
                        pady=(10, 10),
                        columnspan=2,
                        sticky="new")  # Align to the top-left corner

        checkbox_frame = ctk.CTkFrame(left_frame)
        checkbox_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.checkboxes_with_entries = []

        # Checkbox and corresponding input field for Samples
        self.checkbox_samples = ctk.CTkCheckBox(checkbox_frame, text="Submit Samples", command=self.toggle_entry_fields)
        self.checkbox_samples.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.entry_samples = ctk.CTkEntry(checkbox_frame, placeholder_text="how many")
        self.entry_samples.grid(row=1, column=1, padx=0, pady=0, sticky="e")
        self.checkboxes_with_entries.append((self.checkbox_samples, self.entry_samples))

        # Checkbox and corresponding input field for Paired Reads
        self.checkbox_paired_reads = ctk.CTkCheckBox(checkbox_frame, text="Submit Paired Read Sets", command=self.toggle_entry_fields)
        self.checkbox_paired_reads.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.entry_paired_reads = ctk.CTkEntry(checkbox_frame, placeholder_text="how many")
        self.entry_paired_reads.grid(row=2, column=1, padx=0, pady=0, sticky="e")
        self.checkboxes_with_entries.append((self.checkbox_paired_reads, self.entry_paired_reads))

        # Checkbox and corresponding input field for Unpaired Reads
        self.checkbox_unpaired_reads = ctk.CTkCheckBox(checkbox_frame, text="Submit Unpaired Read Sets", command=self.toggle_entry_fields)
        self.checkbox_unpaired_reads.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.entry_unpaired_reads = ctk.CTkEntry(checkbox_frame, placeholder_text="how many")
        self.entry_unpaired_reads.grid(row=3, column=1, padx=0, pady=0, sticky="e")
        self.checkboxes_with_entries.append((self.checkbox_unpaired_reads, self.entry_unpaired_reads))

        # Other checkboxes without entry fields
        self.checkbox_assembly = ctk.CTkCheckBox(checkbox_frame, text="Submit Assembly")
        self.checkbox_assembly.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_bins = ctk.CTkCheckBox(checkbox_frame, text="Submit Binned Contigs")
        self.checkbox_bins.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.checkbox_mags = ctk.CTkCheckBox(checkbox_frame, text="Submit MAGs")
        self.checkbox_mags.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        # Radio buttons for "Coverage from BAM" and "Coverage from TSV"
        coverage_frame = ctk.CTkFrame(left_frame)
        coverage_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.coverage_from_bam = ctk.CTkRadioButton(
            coverage_frame,
            text="Compute coverage from BAM",
            variable=self.coverage_option,
            value=1  # Set this as value 1
        )
        self.coverage_from_bam.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.coverage_from_tsv = ctk.CTkRadioButton(
            coverage_frame,
            text="Kown coverage (TSV/manual input)",
            variable=self.coverage_option,
            value=0  # Set this as value 0
        )
        self.coverage_from_tsv.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # Disable "Coverage from BAM" option on Windows
        if sys.platform == "win32":
            self.coverage_from_bam.configure(state="disabled")

        # File picker button and label
        file_picker_button = ctk.CTkButton(
            coverage_frame,
            text="Select Output File",
            command=self.select_output_file
        )
        file_picker_button.grid(row=0, column=0, padx=10, pady=(20, 0), sticky="sew")

        self.file_label = ctk.CTkLabel(coverage_frame, text="No file selected", anchor="sw")
        self.file_label.grid(row=1, column=0, padx=10, pady=(0,25), sticky="ew")

        self.checkbox_quality_cutoffs = ctk.CTkCheckBox(coverage_frame, text="Use MAG/Bin Quality Cutoffs")
        self.checkbox_quality_cutoffs.grid(row=4, column=0, padx=10, pady=(25,0), sticky="ew")

        # Continue button
        continue_button = ctk.CTkButton(
            main_frame,
            text="Continue",
            font=("Arial", self.controller.fontsize),
            command=self.continue_configuration
        )
        continue_button.grid(row=2,
                             column=0,
                             padx=10,
                             pady=(60, 10),
                             columnspan=3,
                             sticky="sew")

        # Add submission modes image
        submodes_img = controller.submodes_img

        right_label = ctk.CTkLabel(
            right_frame,
            text="Valid Submission Combinations",
            font=("Arial", 16),
            justify='left',
            wraplength=450
        )
        right_label.grid(row=0, column=0, padx=10, pady=0, sticky="ne")

        image_label = ctk.CTkLabel(
            right_frame,
            image=submodes_img,
            text=""  # No text
        )
        image_label.grid(row=1, column=0, padx=10, pady=0, sticky="nw")  # Stretches horizontally

        self.global_disable()

    def initialize_vars(self):
        """ Set all variables to default values
        """
        self.coverage_option = IntVar(value=0)  # Default to 'Coverage from BAM'
        self.output_file_path = None  # Store the output file path

    def global_disable(self):
        """ Uncheck all checkboxes, hide the entry fields and disable the continue button
        """
        for checkbox, entry in self.checkboxes_with_entries:
            checkbox.deselect()
            entry.grid_remove()

        self.checkbox_assembly.deselect()
        self.checkbox_bins.deselect()
        self.checkbox_mags.deselect()
        self.checkbox_quality_cutoffs.deselect()
        self.coverage_option.set(0)
        self.file_label.configure(text="No file selected")

        # Disable "Coverage from BAM" option on Windows
        if sys.platform == "win32":
            self.coverage_from_bam.configure(state="disabled")

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All Files", "*.*")]
        )
        
        if file_path:
            # Store the file path
            self.output_file_path = file_path
            # Truncate the path using the controller's method and update the label
            truncated_path = self.controller.truncate_display_path(file_path, max_display_len=20)
            self.file_label.configure(text=truncated_path)
        else:
            self.file_label.configure(text="No file selected")

    def continue_configuration(self):
        # For every checkbox with an entry field, check if the entry field contains an integer > 0
        for checkbox, entry in self.checkboxes_with_entries:
            if checkbox.get() and (not entry.get().isdigit() or int(entry.get()) < 1):
                messagebox.showinfo("Invalid Input", "Please enter a positive integer for the number of items.")
                return

        # Check if the combination of submission items is valid
        if not validate_parameter_combination(
            submit_samples=self.checkbox_samples.get(),
            submit_reads=(self.checkbox_paired_reads.get() or self.checkbox_unpaired_reads.get()),
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

        # Check if an output file has been selected
        if not self.output_file_path:
            showinfo(
                ("Invalid Parameters"),
                "Please select an output file.",
            )
            return

        # Check if quality cutoffs have been selected without submitting bins
        if self.checkbox_quality_cutoffs.get() and not self.checkbox_bins.get():
            showinfo(
                ("Invalid Parameters"),
                "Quality cutoffs can only be used when submitting bins.",
            )
            return

        # If the output file exists, the user has already agreed to overwrite it
        # So delete it before writing the new one.
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        
        # Set the submission data in controller
        sample_count = int(self.entry_samples.get()) if self.checkbox_samples.get() else 0
        unpaired_reads_count = int(self.entry_unpaired_reads.get()) if self.checkbox_unpaired_reads.get() else 0
        paired_reads_count = int(self.entry_paired_reads.get()) if self.checkbox_paired_reads.get() else 0
        self.controller.set_config_data(
            config_items={
                "samples": sample_count,
                "unpaired_reads": unpaired_reads_count,
                "paired_reads": paired_reads_count,
                "assembly": self.checkbox_assembly.get(),
                "bins": self.checkbox_bins.get(),
                "mags": self.checkbox_mags.get(),
                "form_path": self.output_file_path
            }
        )

        makecfg_through_gui(self.output_file_path,
                            submit_samples=sample_count,
                            submit_single_reads=unpaired_reads_count,
                            submit_paired_end_reads=paired_reads_count,
                            coverage_from_bam=(self.coverage_option.get() == 1),
                            known_coverage=(self.coverage_option.get() == 0),
                            submit_assembly=self.checkbox_assembly.get(),
                            submit_bins=self.checkbox_bins.get(),
                            submit_mags=self.checkbox_mags.get(),
                            quality_cutoffs=self.checkbox_quality_cutoffs.get())

        self.controller.show_page("ConfigFormPage")

    def toggle_entry_fields(self):
        for checkbox, entry in self.checkboxes_with_entries:
            if checkbox.get():
                entry.grid()
            else:
                entry.grid_remove()

    def initialize(self):
        self.initialize_vars()
        self.global_disable()