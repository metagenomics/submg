# controller.py
import customtkinter as ctk
from PIL import Image
import importlib.resources as pkg_resources

from .home import HomePage
from .configOutline import ConfigOutlinePage
from .configForm import ConfigFormPage
from .submission import SubmissionPage
from .monitor import MonitorPage


class MyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("subMG")

        

        # Set the window as resizable (both horizontally and vertically)
        self.resizable(True, True)

        # Sizing
        self.logoHeight = 50
        self.imageWidth_flow = 600
        self.imageWidth_submodes = 350
        self.fontsize = 15

        # Submission data
        self.file_path = None
        self.staging_dir_path = None
        self.submission_mode = ctk.StringVar(value="1")
        self.submission_items = {
            "samples": False,
            "reads": False,
            "assembly": False,
            "bins": False,
            "mags": False,
        }

        # Config data
        self.config_items = {
            "samples": 0,
            "unpaired_reads": 0,
            "paired_reads": 0,
            "assembly": False,
            "bins": False,
            "mags": False,
        }

        # Load and resize images
        self.load_and_resize_images()

        # Configure grid for the root window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a container frame using grid layout
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(2, weight=1)

        # Dictionary to hold the pages
        self.pages = {}

        # Create the pages and store them in the dictionary
        for PageClass in (HomePage,
                          ConfigOutlinePage,
                          ConfigFormPage,
                          SubmissionPage,
                          MonitorPage):
            page_name = PageClass.__name__
            page = PageClass(parent=container, controller=self)
            self.pages[page_name] = page

            # Place all pages in the same location in the grid
            page.grid(row=0, column=0, sticky="nsew")

        # Show the home page initially
        self.show_page("HomePage")

    def show_page(self, page_name):
        # Bring the selected page to the front
        page = self.pages[page_name]
        page.tkraise()
        page.initialize()

    def resize_image(self, path, width=None, height=None):
        """Resizes an image while preserving its aspect ratio."""
        image = Image.open(path)

        if height and not width:
            aspect_ratio = image.width / image.height
            width = int(height * aspect_ratio)
        elif width and not height:
            aspect_ratio = image.height / image.width
            height = int(width * aspect_ratio)
        elif not width and not height:
            print("Warning: No width or height provided. Returning original image.")
            ctkImage = ctk.CTkImage(light_image=Image.open(path))

        # Resize the image
        ctkImage = ctk.CTkImage(light_image=Image.open(path), size=(width, height))
        return ctkImage

    def load_and_resize_images(self):
        """Loads and resizes images for the application."""

        # Load and resize the images using pkg_resources
        with pkg_resources.path('submg.resources', 'gui_logo.png') as logo_path:
            self.logo_img_subMG = self.resize_image(logo_path, height=self.logoHeight - 15)

        with pkg_resources.path('submg.resources', 'nfdi4microbiota_light.png') as microbiota_path:
            self.logo_img_microbiota = self.resize_image(microbiota_path, height=self.logoHeight)

        with pkg_resources.path('submg.resources', 'gui_flow.png') as flow_path:
            self.flow_img = self.resize_image(flow_path, width=self.imageWidth_flow)

        with pkg_resources.path('submg.resources', 'submission_modes_dark.png') as nodes_path:
            self.submodes_img = self.resize_image(nodes_path, width=self.imageWidth_submodes)

    def set_submission_data(self, file_path, staging_dir_path, submission_items):
        self.file_path = file_path
        self.staging_dir_path = staging_dir_path
        self.submission_items = submission_items

    def set_config_data(self, config_items):
        self.config_items = config_items

    def truncate_display_path(self, path, max_display_len):
        """Truncates a path for display."""
        if len(path) > max_display_len:
            return "..." + path[-max_display_len:]
        return path
      
# Run the application
def main():
    app = MyApp()
    app.mainloop()
