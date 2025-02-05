# base.py
import os
os.environ['XMODIFIERS'] = "@im=none"
import customtkinter as ctk
import webbrowser
from tkinter.messagebox import askyesno


class BasePage(ctk.CTkFrame):
    def __init__(self, parent, controller, title_text):
        super().__init__(parent)
        self.submg_repo = "https://github.com/ttubb/submg/"
        self.controller = controller
        self.configure(fg_color="transparent")  # Set the root window's background to transparent

        # Configure grid for the main frame
        self.grid_rowconfigure(0, weight=0)  # Header row stays fixed height
        self.grid_rowconfigure(1, weight=1)  # Main content fills the remaining space
        self.grid_columnconfigure(0, weight=1)  # Content area can expand horizontally

        # Header row
        self.create_header(title_text)
        

    def create_header(self, title_text):
        """ Creates elements from a header. We use this in all pages (and 
            all pages inherit from BasePage).
        """
        # Create a header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0,
                          column=0,
                          sticky="nsew",
                          padx=10,
                          pady=10)  # Stays at the top, full width

        # Configure the header frame grid
        header_frame.grid_columnconfigure(0, weight=0)  # Left logo stays fixed
        header_frame.grid_columnconfigure(1, weight=1)  # Title expands as the window is resized
        header_frame.grid_columnconfigure(2, weight=0)  # Right logo stays fixed

        logos_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logos_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # Left logo
        logo_label_subMG = ctk.CTkLabel(
            logos_frame,
            image=self.controller.logo_img_subMG,
            text=""
        )
        logo_label_subMG.grid(row=0, column=0, padx=5, pady=15, sticky="e")

        # Title label
        title_label = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=("Arial", 22)
        )
        title_label.grid(row=0, column=1, padx=0, pady=10, sticky="nsew")  # Expands with resizing

        # Buttons
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.grid(row=0,
                          column=2,
                          padx=0,
                          pady=0,
                          sticky="nsew")
        # Home Button
        home_button = ctk.CTkButton(
            button_frame,
            text_color="#3a7ebf",
            hover_color="#b6d5de",
            fg_color="transparent",
            border_color="#3a7ebf", 
            border_width=1,
            text="Home", 
            font=('Arial',14),
            command=self.controller.go_home
        )
        home_button.grid(row=0, column=0, padx=0, pady=2, sticky="n")
        manual_button = ctk.CTkButton(
            button_frame,
            text_color="#3a7ebf",
            hover_color="#b6d5de",
            fg_color="transparent",
            border_color="#3a7ebf", 
            border_width=1,
            text="Manual", 
            font=('Arial',14),
            command=self.manual
        )
        manual_button.grid(row=1, column=0, padx=0, pady=2, sticky="s")

        # Ensure the header frame stays at the top
        header_frame.grid_rowconfigure(0, weight=0)  # Fixed height for the header
    
    def manual(self):
        """ Triggered when the "Manual" button is clicked. Opens the subMG
            documentation in the user's web browser.
        """
        msg = ("This will open the subMG documentation in your web browser. "
               "\n\nContinue?")
        if askyesno("Register Study", msg):
            webbrowser.open_new(self.submg_repo)

