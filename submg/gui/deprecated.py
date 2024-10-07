import importlib.resources as pkg_resources
from submg import resources
import customtkinter as ctk
from PIL import Image


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Sizing
        windowSize = "1280x768"
        logoHeight = 40
        imageWidth_flow = 700

        # Configure the window
        self.title("subMG Config Generator")
        self.geometry(windowSize)

        # Load and resize the images
        with pkg_resources.path(resources, 'gui_logo.png') as logo_path:
            self.logo_img_subMG = self.resize_image(logo_path, height=logoHeight - 10)

        with pkg_resources.path(resources, 'nfdi4microbiota_light.png') as microbiota_path:
            self.logo_img_microbiota = self.resize_image(microbiota_path, height=logoHeight)

        with pkg_resources.path(resources, 'gui_flow.png') as flow_path:
            self.flow_img = self.resize_image(flow_path, width=imageWidth_flow)

        # Create a container for pages
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")

        # Initialize frames (pages)
        self.frames = {}
        for F in (HomePage, SubmissionOutlinePage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the home page initially
        self.show_frame("HomePage")

    def resize_image(self, path, width=None, height=None):
        """Resizes an image while preserving its aspect ratio."""
        image = Image.open(path)

        if height and not width:
            aspect_ratio = image.width / image.height
            width = int(height * aspect_ratio)
            ctkImage = ctk.CTkImage(light_image=Image.open(path),
                                size=(width, height))
        elif width and not height:
            aspect_ratio = image.height / image.width
            height = int(width * aspect_ratio)
            ctkImage = ctk.CTkImage(light_image=Image.open(path),
                                size=(width, height))
        elif not width and not height:
            print("Warning: No width or height provided. Returning original image.")
            ctkImage = ctk.CTkImage(light_image=Image.open(path))
        else:
            ctkImage = ctk.CTkImage(light_image=Image.open(path),
                                size=(width, height))
            
        return ctkImage

    def show_frame(self, page_name):
        """Raise the frame (page) to the top to show it."""
        frame = self.frames[page_name]
        frame.tkraise()


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="transparent")
        self.controller = controller

        descriptionText = (
            "subMG is a tool for the submission of metagenomics study data to "
            "the European Nucleotide Archive (ENA). This service will guide you "
            "through the process of creating an input form (config) for the subMG "
            "command line tool."
            "\n\n"
            "Before you start, you need a study registered with the ENA."
            "\n\n"
            "After specifying the location of your files and providing "
            "appropriate metadata, you can download the configuration form for submitting "
            "your data."
        )
        titleText = "subMG Config Generator"
              
        logoLabel_subMG = ctk.CTkLabel(self,
                                       image=controller.logo_img_subMG,
                                       text="")
        logoLabel_subMG.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        logoLabel_microbiota = ctk.CTkLabel(self,
                                            image=controller.logo_img_microbiota,
                                            text="")
        logoLabel_microbiota.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        titleLabel = ctk.CTkLabel(self,
                                 text=titleText,
                                 font=("Arial", 22))
        titleLabel.grid(row=0, column=0, padx=10, pady=10, sticky="s")

        description_frame = ctk.CTkFrame(self)
        description_frame.grid(row=2, column=0, padx=10, pady=0, sticky="sw")
        descriptionLabel = ctk.CTkLabel(description_frame,
                                        text=descriptionText,
                                        wraplength=500,
                                        justify="left",
                                        font=("Arial", 14))
        descriptionLabel.grid(row=0, column=0, padx=10, pady=10, sticky="sw")

        flowLabel = ctk.CTkLabel(description_frame,
                                 image=controller.flow_img,
                                 text="")
        flowLabel.grid(row=0, column=1, padx=10, pady=10, sticky="ne")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=5, pady=10, sticky="ne")

        register_study_button = ctk.CTkButton(button_frame,
                                              text="Register Study",
                                              text_color="#3a7ebf",
                                              hover_color="#b6d5de",
                                              fg_color="transparent",
                                              border_color="#3a7ebf",
                                              border_width=1,
                                              command=self.open_register_study)
        register_study_button.grid(row=0, column=0, padx=5)

        start_button = ctk.CTkButton(button_frame,
                                     text="Prepare Submission",
                                     border_color="#3a7ebf",
                                     border_width=1,
                                     command=lambda: controller.show_frame("SubmissionOutlinePage"))
        start_button.grid(row=0, column=1, padx=5, pady=0)

        padding_frame = ctk.CTkFrame(self, fg_color="transparent")
        padding_frame.grid(row=4, column=0, padx=0, pady=100, sticky="se")

    def open_register_study(self):
        import webbrowser
        webbrowser.open("https://ena-docs.readthedocs.io/en/latest/submit/study/interactive.html")


class SubmissionOutlinePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="transparent")
        self.controller = controller

        label = ctk.CTkLabel(self, text="Submission Outline Page", font=("Arial", 22))
        label.grid(row=0, column=0, padx=20, pady=20)

        back_button = ctk.CTkButton(self, text="Back to Home",
                                    command=lambda: controller.show_frame("HomePage"))
        back_button.grid(row=1, column=0, padx=20, pady=10)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()


