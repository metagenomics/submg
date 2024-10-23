# monitor.py
import customtkinter as ctk
from tkinter import scrolledtext
import threading
from .base import BasePage
from ..core import submit_through_gui

class MonitorPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submission Monitor")
        self.controller = controller

        # Create a content frame within the main area defined by BasePage
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=0)  # Top half
        content_frame.grid_rowconfigure(1, weight=1)  # Bottom half (Log monitor)
        content_frame.grid_columnconfigure(0, weight=1)

        # Create the top frame for Summary and Buttons/Input Fields
        top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        top_frame.grid_rowconfigure(0, weight=1)
        top_frame.grid_columnconfigure(0, weight=1)  # Summary frame
        top_frame.grid_columnconfigure(1, weight=1)  # Buttons/Input fields frame

        # Summary Frame
        summary_frame = ctk.CTkFrame(top_frame)
        summary_frame.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=0)
        summary_frame.grid_columnconfigure(0, weight=1)

        summary_label = ctk.CTkLabel(summary_frame,
                                     text="Submission Summary",
                                     font=("Arial", 16))
        summary_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.summary_text = ctk.CTkLabel(summary_frame,
                                         text="",
                                         font=("Arial", 14),
                                         justify="left")
        self.summary_text.grid(row=1, column=0, sticky="w", padx=10, pady=0)
        self.update_summary()

        # Buttons and Input Fields Frame
        input_frame = ctk.CTkFrame(top_frame)
        input_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=0)
        input_frame.grid_rowconfigure(0, weight=1)
        input_frame.grid_rowconfigure(1, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)

        # Username and Password Fields
        username_label = ctk.CTkLabel(input_frame, text="ENA Username:", font=("Arial", 14))
        username_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.username_entry = ctk.CTkEntry(input_frame)
        self.username_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        password_label = ctk.CTkLabel(input_frame, text="ENA Password:", font=("Arial", 14))
        password_label.grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.password_entry = ctk.CTkEntry(input_frame, show="*")
        self.password_entry.grid(row=0, column=3, sticky="ew", padx=10, pady=10)

        # Mode Switch
        self.mode_switch = ctk.CTkSwitch(
            input_frame,
            text="Use Test Server",
            font=("Arial", 14),
            variable=self.controller.submission_mode,
            onvalue="1",
            offvalue="0"
        )
        self.mode_switch.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Start Submission Button
        start_button = ctk.CTkButton(
            input_frame,
            text="Start Submission",
            font=("Arial", 14),
            command=self.start_submission
        )
        start_button.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        self.start_button = start_button

        # Logging Monitor Frame (bottom half of the page)
        log_frame = ctk.CTkFrame(content_frame)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Logging Text Box
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            font=("Courier", 12),
            bg="white",
            fg="black",
            state="normal",  # Change to normal initially to allow appending text
            height=14,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.log_text.configure(state="disabled")  # Disable editing after initialization

    def update_summary(self, max_display_len=30):
        """Update the summary text with submission data from the controller."""
        # Make a string of the submission items
        submission_items = []
        for item, will_submit in self.controller.submission_items.items():
            if will_submit:
                submission_items.append(item.capitalize())
        submission_items = ", ".join(submission_items)

        # Limit the length of the paths
        if self.controller.file_path:
            config = self.controller.truncate_display_path(self.controller.file_path,
                                                        max_display_len)
        else:
            config = "Not selected"
        if self.controller.staging_dir_path:
            staging = self.controller.truncate_display_path(self.controller.staging_dir_path,
                                                            max_display_len)
        else:
            staging = "Not selected"

        submission_data = (
            f"Config:\t{config}\n"
            f"Staging:\t{staging}\n"
            f"Submission Items:\n"
            f"\t{submission_items}"
        )
        self.summary_text.configure(text=submission_data)

    def start_submission(self):
        """Handle the submission logic here."""
        # Disable all the input fields and buttons
        self.disable_input_fields()

        # Check if the user entered a username and password
        if not self.username_entry.get() or not self.password_entry.get():
            self.log_message("Please enter a username and password.")
            self.enable_input_fields()
            return

        # Run submit_through_gui in a separate thread
        submission_thread = threading.Thread(target=self.run_submission)
        submission_thread.daemon = True  # Ensures the thread will exit when the main program does
        submission_thread.start()

    def run_submission(self):
        """Run the submission process in a separate thread."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            submit_through_gui(config_path=self.controller.file_path,
                               output_dir=self.controller.staging_dir_path,
                               listener=self.log_message,
                               development_service=self.controller.submission_mode.get(),
                               verbosity=1,
                               submit_samples=self.controller.submission_items["samples"],
                               submit_reads=self.controller.submission_items["reads"],
                               submit_assembly=self.controller.submission_items["assembly"],
                               submit_bins=self.controller.submission_items["bins"],
                               submit_mags=self.controller.submission_items["mags"],
                               username=username,
                               password=password)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Enable all the input fields and buttons after completion or error
            self.enable_input_fields()

    def disable_input_fields(self):
        """Disable all input fields and buttons."""
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.mode_switch.configure(state="disabled")
        self.start_button.configure(state="disabled")

    def enable_input_fields(self):
        """Enable all input fields and buttons."""
        self.username_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.mode_switch.configure(state="normal")
        self.start_button.configure(state="normal")

    def log_message(self, message):
        """Append a message to the log monitor."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def initialize(self):
        """Called whenever monitor renders the page"""
        self.update_summary()
        self.log_message("Ready to submit.\n")