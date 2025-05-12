# home.py
import os
os.environ['XMODIFIERS'] = "@im=none"
import threading
import customtkinter as ctk
from submg.gui.base import BasePage
from submg.modules.webinWrapper import webin_cli_jar_available, get_persistent_storage_path
from submg.modules.webinDownload import check_java, download_webin_cli
from submg.modules.statConf import staticConfig

import webbrowser
from tkinter.messagebox import askyesno, showwarning

class HomePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Home")

        self.ena_register_study_address = "https://ena-docs.readthedocs.io/en/latest/submit/study.html"

        # Create main_frame and configure its grid
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1,
                        column=0,
                        padx=0,
                        pady=0,
                        sticky="nsew")  # Allow main frame to stretch both vertically and horizontally

        # Configure grid
        self.grid_rowconfigure(1, weight=1)  # Allow main frame to expand
        main_frame.grid_rowconfigure(0, weight=1)  # Content row, no vertical scaling
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
            "\n\n"
            "This interface is designed for submitting small datasets. If you "
            "intend to submit a large dataset (e.g. 20 samples, 40 sets of reads) "
            "consider using the Command Line Interface (submg-cli) instead."
            )
        text_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=("Arial", self.controller.fontsize),
            justify='left',
            wraplength=450,
        )
        text_label.grid(row=0, column=0, padx=5, pady=20, sticky="new")  # Stretches horizontally

        # Right side - Image
        flow_img = controller.flow_img
        image_label = ctk.CTkLabel(
            main_frame,
            image=flow_img,
            text=""  # No text
        )
        image_label.grid(row=0, column=1, padx=5, pady=20, sticky="new")  # Stretches horizontally

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, pady=10, sticky="ew")

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
            text="Create New Config",
            font=('Arial',self.controller.fontsize),
            command=lambda: controller.show_page("ConfigOutlinePage")
        )
        prepare_button.grid(row=0, column=1, padx=0, sticky="ew")

        # Button 2 - Submit Data
        submit_button = ctk.CTkButton(
            button_frame,
            text="Load Config",
            font=('Arial',self.controller.fontsize),
            command=self.load_config
        )
        submit_button.grid(row=0, column=2, padx=20, sticky="ew")

        self.check_webin_cli()

    def check_webin_cli(self):
        """ Checks if java and the correct version of webin-cli are available.
            If java is not available, the user is warned that only config
            editing is possible but submission will fail.
            If webin-cli is not available, the user is warned that submission
            will be impossible. Afterwards, the user is offered to download
            webin-cli. Then the function checks if it is now available and
            warns the user if it is not.
        """
        download_webin = False
        if not check_java(soft=True):
            java_version = staticConfig.java_version
            showwarning("Java not found", 
                        f"Java {java_version} or higher is required to submit "
                        f"data. Only configuration editing is possible. If you "
                        f"intend to submit data, please close this application "
                        f"and install Java {java_version} or higher.")
        if not webin_cli_jar_available():
            webin_cli_version = staticConfig.webin_cli_version
            showwarning("webin-cli not found", 
                        f"webin-cli-{webin_cli_version}.jar is required to "
                        f"submit data but was not found. You will not be able "
                        f"to submit data without downloading webin-cli first.")
            if askyesno("Download webin-cli",
                        "Would you like to download webin-cli now?"):
                download_webin = True
        if download_webin:
                # Create a non-blocking dialog
                dlg = ctk.CTkToplevel(self)
                dlg.title("Downloading webin-cli")
                dlg.geometry("400x100")
                dlg.resizable(False, False)

                ctk.CTkLabel(
                    dlg,
                    text="Downloading webin-cli, please wait…",
                    font=('Arial', self.controller.fontsize)
                ).pack(pady=(20, 5))

                pb = ctk.CTkProgressBar(dlg, mode='indeterminate')
                pb.pack(fill='x', padx=20, pady=(0, 20))
                pb.start()

                def _worker():
                    # Perform the download
                    download_webin_cli(staticConfig.webin_cli_version)

                    # Once done, close the dialog and check success on the main thread
                    def _on_done():
                        pb.stop()
                        dlg.destroy()

                        if not webin_cli_jar_available():
                            storage = get_persistent_storage_path()
                            showwarning(f"webin-cli not found", 
                                        f"Something went wrong and "
                                        f"webin-cli-{webin_cli_version}.jar stil cannot be "
                                        f"found. Please download webin-cli manually from "
                                        f"the ENA website and place it in the the following directory:\n"
                                        f"{storage}")

                    self.after(0, _on_done)

                threading.Thread(target=_worker, daemon=True).start()

    def register_study(self):
        """ Triggered when the user presses the 'Register Study' button. Opens
            the ENA documentation in their web browser.
        """
        msg = ("This will open the ENA documentation in your web browser. "
               "\n\nContinue?")
        if askyesno("Register Study", msg):
            webbrowser.open(self.ena_register_study_address)

    def load_config(self):
        self.controller.show_page("LoadConfigPage")

    def initialize(self):
        """Called whenever monitor renders the page"""
        pass
