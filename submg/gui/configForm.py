# pages/config_form_page.py
import customtkinter as ctk
import yaml
from tkinter import Scrollbar, Canvas
from tkinter.messagebox import showerror
from .base import BasePage
from ..modules.statConf import YAMLCOMMENTS, YAMLEXAMPLES, YAML_PRETTYNAMES, YAML_MULTI_FILEKEYS, YAML_SINGLE_FILEKEYS

class ConfigFormPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Form")

        # Create main_frame to hold canvas and help_frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)

        # Formatting
        self.item_font_size = 12
        self.title_font_size = 15
        self.item_x_padding = 10
        self.item_y_padding = 2

        # Create canvas and scrollbar for scrolling form_frame
        self.canvas = Canvas(self.main_frame)
        self.canvas.configure(bg="#F0F0F0")
        self.scrollbar = Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Help text frame, to the right of the canvas. For now, just has a placeholder label
        self.help_frame = ctk.CTkFrame(self.main_frame)
        self.help_frame.grid(row=0, column=2, padx=10, pady=0, sticky="nsew")
        help_label = ctk.CTkLabel(self.help_frame,
                                  wraplength=400,
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
                                  justify='left')
        help_label.grid(row=0,
                        column=0,
                        sticky="nsew",
                        padx=10,
                        pady=0)

        asterisk_label = ctk.CTkLabel(self.help_frame,
                                      text="*comma-separated list",
                                      justify='left',
                                      font=("Arial", 12))
        asterisk_label.grid(row=1, column=0, padx=10, pady=(20,0), sticky="w")

        # Create form_frame and configure its grid inside the canvas
        self.form_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.form_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Configure the grid layout to expand properly
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_rowconfigure(0, weight=1)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # The dictionary that will keep the form structure and user input
        self.form_data = {}
        self.frame_row_counter = 1

    def load_form(self, form_path):
        """ Read a yaml form from the specified path. Check if it
            is a valid form. Translate it into a dictionary that 
            will later be rendered
        """
        with open(form_path, 'r') as file:
            self.original_form_data = yaml.safe_load(file)

        print("\n\nORIGINAL FORM DATA")
        for k,v in self.original_form_data.items():
            print(k,v)
        print("\n\n")

    def save_config(self, form_path):
        """ Save the configuration to a yaml file """
        pass

    def render_form(self):
        """ Render the form based on the loaded yaml data """

        # Frame for basic items
        self.basic_frame = ctk.CTkFrame(self.form_frame)
        self.basic_frame_rowcounter = 0
        self.basic_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.basic_frame.grid_columnconfigure(0, weight=1)
        self.basic_frame.grid_columnconfigure(1, weight=3)
        # Title label for the frame
        title_label = ctk.CTkLabel(self.basic_frame,
                                   text="Core",
                                   font=("Arial", self.title_font_size))
        title_label.grid(row=self.basic_frame_rowcounter,
                         column=0,
                         sticky="w",
                         pady=self.item_y_padding,
                         padx=self.item_x_padding)
        self.basic_frame_rowcounter += 1

        for key, value in self.original_form_data.items():
            # Check if the value is a dictionary, a list, a string or None
            print(f"\n Processing key {key} with value")
            if isinstance(value, dict):
                print("\tshits a dict")
                new_frame = ctk.CTkFrame(self.form_frame)
                new_frame.grid(row=self.frame_row_counter, column=0, sticky="nsew", padx=10, pady=10)
                new_frame.grid_columnconfigure(0, weight=1)
                new_frame.grid_columnconfigure(1, weight=3)
                self.frame_row_counter += 1
                self.form_data[key] = {"type": "nested",
                                       "frame": new_frame,
                                       "row_counter": 0,
                                       "items": {}}
                # Give the frame a title
                title_label = ctk.CTkLabel(new_frame,
                                           text=YAML_PRETTYNAMES[key],
                                           font=("Arial", self.title_font_size))
                title_label.grid(row=0,
                                 column=0,
                                 sticky="w",
                                 padx=self.item_x_padding,
                                 pady=self.item_y_padding)
                self.form_data[key]["row_counter"] += 1

                for subkey, subvalue in value.items():
                    self.create_nested_item(key, subkey, subvalue)
            else: # We have either a basic item or a nested list
                print("\tshits not a dict")
                if isinstance(value, list):
                    print("\tshits a list")
                    print(value)
                    # Is it a basic item or a list of dictionaries?
                    if len(value) > 0 and all(isinstance(item, dict) for item in value):
                        # These are nested dictionaries
                        print("\tEverything in there is dicts though")
                        self.create_list_of_nested_items(key, value)
                    elif (len(value) == 0) or (not isinstance(value[0], dict)):
                        # These is a basic item list
                        print("\tcalling basicitem with islist=True for", key)
                        self.basic_item(key, value, islist=True)
                    else:
                        # Make a popup error message
                        print("\tInvalid form data. Please check the yaml file.")
                        showerror("Error", "Invalid form data. Please check the yaml file.")
                        return
                else:
                    print("\tshits not a list")
                    # This is a basic item
                    self.basic_item(key, value, islist=False)

    def create_list_of_nested_items(self, key, itemlist):
        counter = 0
        for item in itemlist:
            counter += 1
            numbered_key = f"{key} #{counter}"
            new_frame = ctk.CTkFrame(self.form_frame)
            new_frame.grid(row=self.frame_row_counter, column=0, sticky="nsew", padx=10, pady=10)
            new_frame.grid_columnconfigure(0, weight=1)
            new_frame.grid_columnconfigure(1, weight=3)
            self.frame_row_counter += 1
            self.form_data[numbered_key] = {"type": "nested_numbered",
                                             "frame": new_frame,
                                             "row_counter": 0,
                                             "items": {}}
            # Give the frame a title
            title = f"{YAML_PRETTYNAMES[key]} #{counter}"
            title_label = ctk.CTkLabel(new_frame,
                                        text=title,
                                        font=("Arial", self.title_font_size))
            title_label.grid(row=0,
                                column=0,
                                sticky="w",
                                padx=self.item_x_padding,
                                pady=self.item_y_padding)
            self.form_data[numbered_key]["row_counter"] += 1

            for subkey, subvalue in item.items():
                self.create_nested_item(numbered_key, subkey, subvalue)

    def basic_item(self, key, value, islist):
        # Create a regular item in the basic_frame
        text = YAML_PRETTYNAMES[key]
        if islist:
            text += "*"
            print(f"Basic item {key} is a list, text is {text}")
        else:
            print(f"Basic item {key} is not a list, text is {text}")
        label = ctk.CTkLabel(self.basic_frame, text=text)
        label.grid(row=self.basic_frame_rowcounter,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)
        entry = ctk.CTkEntry(self.basic_frame)
        entry.grid(row=self.basic_frame_rowcounter,
                   column=1,
                   sticky="nsew",
                   pady=self.item_y_padding,
                   padx=self.item_x_padding)
        self.basic_frame_rowcounter += 1

        # Add a value and write to form_data
        if isinstance(value, list):
            value = [str(x) for x in value]
            value = ", ".join(value)
            entry.insert(0, value)
            self.form_data[key] = {"type": "basiclist", "widget": entry}
        else:
            if value is not None:
                entry.insert(0, str(value))
            self.form_data[key] = {"type": "basic", "widget": entry}

    def create_nested_item(self, parent_key, key, value):
        """ Create a regular item """
        frame = self.form_data[parent_key]["frame"]
        row_counter = self.form_data[parent_key]["row_counter"]

        text = YAML_PRETTYNAMES[key]
        if isinstance(key, list):
            text += "*"

        label = ctk.CTkLabel(frame, text=text)
        label.grid(row=row_counter,
                   column=0,
                   sticky="w",
                   pady=self.item_y_padding,
                   padx=(self.item_x_padding, 0))

        entry = ctk.CTkEntry(frame)
        entry.grid(row=row_counter,
                   column=1,
                   sticky="nsew",
                   pady=self.item_y_padding,
                   padx=self.item_x_padding)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=3)

        self.form_data[parent_key]["row_counter"] += 1

        if isinstance(value, list):
            value = [str(x) for x in value]
            value = ", ".join(value)
            entry.insert(0, value)
            self.form_data[parent_key]["items"][key] = {"type": "list", "widget": entry}

        else:
            if value is not None:
                entry.insert(0, str(value))
            self.form_data[parent_key]["items"][key] = {"type": "basic", "widget": entry}

    def _on_frame_configure(self, event):
        """ Update the scroll region for the canvas whenever the form frame changes size """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """ Adjust the form_frame width to match the canvas width """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def get_comment(self, item_name):
        """ For a specific form item, get the comment text """
        pass

    def get_example(self, item_name):
        """ For a specific form item, get the example text """
        pass

    def save_config(self, form_path):
        """ Save the configuration to a yaml file """
        pass

    def got_to_submission(self):
        """ Go to the submission page """
        pass

    def initialize(self):
        """Called whenever controller renders the page"""
        form_path = self.controller.config_items["form_path"]
        self.load_form(form_path)
        self.render_form()
