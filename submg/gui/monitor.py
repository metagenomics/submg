# monitor.py
import os
os.environ['XMODIFIERS'] = "@im=none"
import customtkinter as ctk
from tkinter import scrolledtext
from tkinter import messagebox
import multiprocessing
import queue
from submg.gui.base import BasePage
from submg.core import submit_through_gui

def submission_wrapper(config_path, output_dir, development_service, verbosity,
                      submit_samples, submit_reads, submit_assembly,
                      submit_bins, submit_mags, username, password, log_queue):
    """
    Wrapper function to run submit_through_gui and send log messages to a queue.
    """
    def listener(message):
        log_queue.put(message)
    
    try:
        submit_through_gui(
            config_path=config_path,
            output_dir=output_dir,
            listener=listener,
            development_service=development_service,
            verbosity=verbosity,
            submit_samples=submit_samples,
            submit_reads=submit_reads,
            submit_assembly=submit_assembly,
            submit_bins=submit_bins,
            submit_mags=submit_mags,
            username=username,
            password=password
        )
    except Exception as e:
        log_queue.put(f"Error: {e}")


class MonitorPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Submission Monitor")
        self.controller = controller

        # Track whether a submission is currently running
        self.submission_process = None
        self.submission_running = False

        # Initialize the process and queue
        self.log_queue = multiprocessing.Queue()

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
        top_frame.grid_columnconfigure(0, weight=3)  # Allocated more weight to summary_frame
        top_frame.grid_columnconfigure(1, weight=2)  # Allocated less weight to buttons/input fields

        # Summary Frame
        summary_frame = ctk.CTkFrame(top_frame)
        summary_frame.grid(row=0,
                           column=0,
                           sticky="nsew",
                           padx=(10, 5),  # Adjusted padding for better layout
                           pady=0)
        summary_frame.grid_rowconfigure(0, weight=0)
        summary_frame.grid_rowconfigure(1, weight=1)
        summary_frame.grid_rowconfigure(2, weight=0)
        summary_frame.grid_columnconfigure(0, weight=1)

        summary_label = ctk.CTkLabel(summary_frame,
                                     text="Submission Summary",
                                     font=("Arial", 16))
        summary_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        # Add buttons to 'Edit Config' and 'Edit Outline'
        summary_button_frame = ctk.CTkFrame(summary_frame,
                                            fg_color="transparent")
        summary_button_frame.grid(row=2,
                                  column=0,
                                  sticky="ew",
                                  padx=10,  # Added horizontal padding
                                  pady=(10, 0))
        summary_button_frame.grid_columnconfigure(0, weight=1)
        summary_button_frame.grid_columnconfigure(1, weight=1)

        self.edit_config_button = ctk.CTkButton(summary_button_frame,
                                           text="Edit Config",
                                           text_color="#3a7ebf",
                                           hover_color="#b6d5de",
                                           fg_color="transparent",
                                           border_color="#3a7ebf", 
                                           border_width=1,
                                           font=("Arial", 14),
                                           command=lambda: controller.show_page("ConfigFormPage"))
        self.edit_config_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0,10))

        self.edit_outline_button = ctk.CTkButton(summary_button_frame,
                                            text="Edit Outline",
                                            font=("Arial", 14),
                                            text_color="#3a7ebf",
                                            hover_color="#b6d5de",
                                            fg_color="transparent",
                                            border_color="#3a7ebf", 
                                            border_width=1,
                                            command=lambda: controller.show_page("LoadConfigPage"))
        self.edit_outline_button.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0,10))

        self.summary_text = ctk.CTkLabel(summary_frame,
                                         text="",
                                         font=("Arial", 14),
                                         justify="left",
                                         anchor="w",
                                         wraplength=400)  # Added wraplength for better text display
        self.summary_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=0)
        self.update_summary()

        # Buttons and Input Fields Frame
        input_frame = ctk.CTkFrame(top_frame)
        input_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=0)
        input_frame.grid_rowconfigure(0, weight=0)  # Username and Password
        input_frame.grid_rowconfigure(1, weight=0)  # Mode Switch
        input_frame.grid_rowconfigure(2, weight=1)  # Spacer
        input_frame.grid_rowconfigure(3, weight=0)  # Buttons Frame
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(2, weight=1)
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
        self.mode_switch.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="w")

        # Buttons Frame
        input_button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_button_frame.grid(row=3, column=0, columnspan=4, padx=0, pady=0, sticky="ew")
        # Configure grid columns to distribute space equally
        for i in range(4):
            input_button_frame.grid_columnconfigure(i, weight=1)

        # Cancel button
        cancel_button = ctk.CTkButton(
            input_button_frame,
            text="Stop Submission",
            font=("Arial", 14),
            fg_color=self.controller.colors['red'],
            command=self.stop_submission
        )
        cancel_button.grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=10, sticky="nsew")
        self.stop_button = cancel_button  # NEW: keep a direct reference

        # Start Submission Button
        start_button = ctk.CTkButton(
            input_button_frame,
            text="Start Submission",
            font=("Arial", 14),
            command=self.start_submission
        )
        start_button.grid(row=0, column=2, columnspan=2, padx=(5, 10), pady=10, sticky="nsew")
        self.start_button = start_button  # already present

        # Initial state: no submission running
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

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

        # Start polling the log queue
        self.after(100, self.poll_log_queue)


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
        if self.submission_process and self.submission_process.is_alive():
            self.log_message("A submission is already running.")
            return

        # Disable all the input fields and buttons
        self.disable_input_fields()

        # Check if the user entered a username and password
        if not self.username_entry.get() or not self.password_entry.get():
            self.log_message("Please enter a username and password.")
            self.enable_input_fields()
            return

        # Write a message
        self.log_message("\n\tSTARTING SUBMISSION THROUGH GUI...")

        # Create a new queue for this submission
        self.log_queue = multiprocessing.Queue()

        # Create and start the submission process
        self.submission_process = multiprocessing.Process(
            target=submission_wrapper,
            args=(
                self.controller.file_path,
                self.controller.staging_dir_path,
                self.controller.submission_mode.get(),
                1,  # verbosity
                self.controller.submission_items.get("samples", False),
                self.controller.submission_items.get("reads", False),
                self.controller.submission_items.get("assembly", False),
                self.controller.submission_items.get("bins", False),
                self.controller.submission_items.get("mags", False),
                self.username_entry.get(),
                self.password_entry.get(),
                self.log_queue
            )
        )
        self.submission_process.start()
        self.submission_running = True


    def poll_log_queue(self):
        """Poll the log queue for new messages and update the log monitor."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_message(message)
        except queue.Empty:
            pass
        except Exception as e:
            self.log_message(f"Queue Error: {e}")
        finally:
            # Check if the submission process has finished
            if self.submission_process is not None and not self.submission_process.is_alive():
                if self.submission_running:
                    # Handle completion exactly once
                    self.handle_submission_completion()

            # Continue polling after 100 ms
            self.after(100, self.poll_log_queue)


    def handle_submission_completion(self):
        """Handle UI updates and popup when the submission process finishes."""
        self.submission_running = False

        # Capture and clear process object
        exitcode = self.submission_process.exitcode
        self.submission_process = None

        # Reset UI
        self.enable_input_fields()

        # Log completion and message user
        self.log_message(f"Submission process finished with exit code {exitcode}.")
        if exitcode == 0:
            messagebox.showinfo(
                "Submission completed",
                "The submission process has completed.\n\n"
                "Please review the log output in the Submission Monitor."
            )
        else:
            messagebox.showerror(
                "Submission failed",
                "The submission process terminated with an error.\n\n"
                "Please review the log output in the Submission Monitor."
            )


    def stop_submission(self):
        """Stop the submission process, update UI accordingly, inform the user."""
        if self.submission_process and self.submission_process.is_alive():
            self.log_message("Stopping submission...")
            self.submission_process.terminate()
            self.submission_process.join()
            self.log_message("Submission stopped.")
            self.submission_running = False
            self.submission_process = None

            # Reset UI to idle state
            self.enable_input_fields()

            # Inform user
            messagebox.showinfo(
                "Submission stopped",
                "The submission process was stopped by the user."
            )
        else:
            self.log_message("No active submission to stop.")
            # When nothing is running, ensure UI is in idle state
            self.enable_input_fields()



    def disable_input_fields(self):
        """Disable all input fields and buttons, enable only the Stop button."""
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.mode_switch.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.edit_config_button.configure(state="disabled")
        self.edit_outline_button.configure(state="disabled")
        self.disable_header_buttons()


    def enable_input_fields(self):
        """Enable all input fields and buttons, disable only the Stop button."""
        self.username_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.mode_switch.configure(state="normal")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.edit_config_button.configure(state="normal")
        self.edit_outline_button.configure(state="normal")
        self.enable_header_buttons()

    def log_message(self, message):
        """Append a message to the log monitor."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")


    def initialize(self):
        """Called whenever monitor renders the page"""
        self.update_summary()
        if not self.submission_running:
            self.log_message("Ready to submit.\n")


    def children_recursive(self, widget, input_button_frame=False):
        """Helper method to recursively find children widgets."""
        for child in widget.winfo_children():
            if input_button_frame and isinstance(child, ctk.CTkFrame):
                yield child
            else:
                yield from self.children_recursive(child, input_button_frame)
