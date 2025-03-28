# controller.py
import os
os.environ['XMODIFIERS'] = "@im=none"
import sys
import customtkinter as ctk
from tkinter.messagebox import askyesno
from PIL import Image
#import importlib.resources as pkg_resources



from submg.gui.home import HomePage
from submg.gui.configOutline import ConfigOutlinePage
from submg.gui.configForm import ConfigFormPage
from submg.gui.monitor import MonitorPage
from submg.gui.load import LoadConfigPage


class MyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("subMG")

        # Prevent system settings from affecting appearance
        ctk.set_appearance_mode("light")

        # Define global colors
        self.colors = {
            'red': '#a31a15'
        }

        # Set the window as resizable (both horizontally and vertically)
        self.resizable(True, True)

        self.initialize_vars()

        self.load_and_resize_images()

        # Configure grid for the root window - 1 row and 1 column
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a container frame using grid layout
        container = ctk.CTkFrame(self,
                                 fg_color="transparent")
        container.grid(row=0,
                       column=0,
                       padx=0,
                       pady=0,
                       sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create the pages and store them in a dictionary
        self.currentpage = None
        self.pages = {}
        for PageClass in (HomePage,
                          ConfigOutlinePage,
                          ConfigFormPage,
                          MonitorPage,
                          LoadConfigPage):
            page_name = PageClass.__name__
            page = PageClass(parent=container, controller=self)
            self.pages[page_name] = page

            # Place all pages in the same location in the grid
            page.grid(row=0, column=0, sticky="nsew")

        # Show the home page initially
        self.show_page("HomePage")

    def initialize_vars(self):
        # Sizing
        self.logoHeight = 50
        self.imageWidth_flow = 600
        self.imageWidth_submodes = 400
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
            "form_path": None,
        }
    
    def go_home(self):
        """ Ask user whether they really want to return. Clear all data. 
            Switch to the HomePage.
        """
        msg = ("Are you sure you want to return to the home page? "
               "All data that was not saved to a config file will be lost.")
           
        if askyesno("Return to Home", msg):
            self.initialize_vars()
            self.show_page("HomePage")

    def show_page(self, page_name):
        """ Switches the user over to the respective page.
        """
        #if self.currentpage:
        #    self.currentpage.destroy()
        page = self.pages[page_name]
        self.currentpage = page
        page.tkraise()
        page.initialize()


    def resource_path(self, package, resource):
        """Get the absolute path to a resource, compatible with PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            # When not running with PyInstaller, use the package's normal path
            import importlib.resources as pkg_resources
            with pkg_resources.path(package, resource) as resource_path:
                return str(resource_path)

        return os.path.join(base_path, package.replace('.', os.sep), resource)


    def resize_image(self, path, width=None, height=None):
        """ Resizes an image while preserving its aspect ratio
        """
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
        """Loads and resizes images for the application using resource_path."""

        # Retrieve and resize images
        logo_path = self.resource_path('submg.resources', 'gui_logo.png')
        self.logo_img_subMG = self.resize_image(logo_path, height=self.logoHeight - 15)

        microbiota_path = self.resource_path('submg.resources', 'nfdi4microbiota_light.png')
        self.logo_img_microbiota = self.resize_image(microbiota_path, height=self.logoHeight)

        flow_path = self.resource_path('submg.resources', 'gui_flow.png')
        self.flow_img = self.resize_image(flow_path, width=self.imageWidth_flow)

        nodes_path = self.resource_path('submg.resources', 'submission_modes_dark.png')
        self.submodes_img = self.resize_image(nodes_path, width=self.imageWidth_submodes)

    #     # Resize the image
    #     ctkImage = ctk.CTkImage(light_image=Image.open(path), size=(width, height))
    #     return ctkImage

    # def load_and_resize_images(self):
    #     """ Loads and resizes images for the application.
    #         Uses pkg_resources to load images from the resources folder.
    #     """

    #     with pkg_resources.path('submg.resources', 'gui_logo.png') as logo_path:
    #         self.logo_img_subMG = self.resize_image(logo_path, height=self.logoHeight - 15)

    #     with pkg_resources.path('submg.resources', 'nfdi4microbiota_light.png') as microbiota_path:
    #         self.logo_img_microbiota = self.resize_image(microbiota_path, height=self.logoHeight)

    #     with pkg_resources.path('submg.resources', 'gui_flow.png') as flow_path:
    #         self.flow_img = self.resize_image(flow_path, width=self.imageWidth_flow)

    #     with pkg_resources.path('submg.resources', 'submission_modes_dark.png') as nodes_path:
    #         self.submodes_img = self.resize_image(nodes_path, width=self.imageWidth_submodes)

    def set_submission_data(self, file_path, staging_dir_path, submission_items):
        self.file_path = file_path
        self.staging_dir_path = staging_dir_path
        self.submission_items = submission_items

    def set_config_data(self, config_items):
        self.config_items = config_items

    def truncate_display_path(self, path, max_display_len):
        """ Truncates a path from the left if it exceeds a certain length.
        """
        if len(path) > max_display_len:
            return "..." + path[-max_display_len:]
        return path
      
# Run the application
def main():
    app = MyApp()
    app.mainloop()

    if __name__ == "__main__":
        main()
