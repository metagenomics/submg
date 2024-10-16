# pages/config_form_page.py
import customtkinter as ctk
import yaml
from tkinter import filedialog
from tkinter.messagebox import showerror
from .base import BasePage
from ..modules.statConf import YAMLCOMMENTS, GUIEXAMPLES, GUILINKS, YAML_PRETTYNAMES, YAML_MULTI_FILEKEYS, YAML_SINGLE_FILEKEYS
import webbrowser

class ConfigFormPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Form")

        # Create main_frame to hold form_frame and help_frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, padx=(5,0), pady=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=10)
        self.main_frame.grid_columnconfigure(1, weight=0)

        # Formatting
        self.item_font_size = 12
        self.title_font_size = 15
        self.item_x_padding = 10
        self.item_y_padding = 2
        self.frame_x_padding = 0
        self.frame_y_padding = 5

        # # Get the initial width of main_frame
        # self.update_idletasks()  # Ensures layout updates before calculating dimensions
        # main_frame_width = self.main_frame.winfo_width()

        # # Set initial widths for the frames
        # form_frame_width = int(main_frame_width * 0.7)  # 70% of main_frame width
        # help_frame_width = int(main_frame_width * 0.3)  # 30% of main_frame width

        # Create the form_frame as a CTkScrollableFrame
        self.form_frame = ctk.CTkScrollableFrame(self.main_frame,
                                                 fg_color="transparent",)
        self.form_frame.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
        self.form_frame.grid_rowconfigure(0, weight=0)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # Help text frame, to the right of the form_frame
        self.help_frame = ctk.CTkFrame(self.main_frame,
                                       fg_color="transparent")
        self.help_frame.grid(row=0,
                             column=1,
                             padx=5,
                             pady=0,
                             sticky="nsew")
        self.help_frame.grid_rowconfigure(0, weight=0)
        self.help_frame.grid_rowconfigure(1, weight=0)
        self.help_frame.grid_columnconfigure(0, weight=1)

        self.help_title = ctk.CTkLabel(
            self.help_frame,
            text="Help & Examples\n"+80*" ",
            font=("Arial", self.title_font_size))
        self.help_title.grid(
            row=0,
            column=0,
            sticky="new",
            padx=10,
            pady=(10,0)
        )

        self.help_label = ctk.CTkLabel(
            self.help_frame,
            wraplength=400,
            text=(
                "Click on the question mark next to an item to get more "
                "information."
            ),
            justify='left'
        )
        self.help_label.grid(
            row=1,
            column=0,
            sticky="nw",
            padx=10,
            pady=(0,0)
        )

        self.example_label = ctk.CTkLabel(
            self.help_frame,
            wraplength=300,
            text="",
            justify='left',
            font=("Courier", 12)
        )
        self.example_label.grid(
            row=2,
            column=0,
            sticky="nw",
            padx=10,
            pady=0
        )

        self.hyperlink_miniframe = ctk.CTkFrame(self.help_frame, fg_color="transparent")
        self.hyperlink_miniframe.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

        # The dictionary that will keep the form structure and user input
        self.form_data = {}
        self.picked_files = {}
        self.picked_filelists = {}
        self.frame_row_counter = 1


    def show_help(self, key):
        """Fetch the help text from YAMLCOMMENTS and display it in help_frame."""
        # Show the help text
        help_text = YAMLCOMMENTS.get(key, "No help available for this item.")
        help_text += "\n\n\nExample:"
        self.help_label.configure(text=help_text)

        # Show an example
        example_text = GUIEXAMPLES.get(key, "No example available")
        self.example_label.configure(text=example_text)

        # Remove all buttons in the hyperlink mini frame
        for widget in self.hyperlink_miniframe.winfo_children():
            widget.destroy()
        # For each link in GUILINKS, create a button styled like a hyperlink
        links = GUILINKS.get(key, {})
        row = 0
        for link_text, link_url in links.items():
            link_text = f"Browser: {link_text}"
            hyperlink_button = ctk.CTkButton(
                self.hyperlink_miniframe,
                text=link_text,
                text_color="#3a7ebf",
                hover_color="#b6d5de",
                fg_color="transparent",
                border_color="#3a7ebf", 
                border_width=1,
                font=("Arial", 12),
                command=lambda url=link_url: webbrowser.open_new(url)
            )
            hyperlink_button.grid(row=row, column=0, padx=5, pady=5, sticky="nsew")
            row += 1


    def create_asterisk_label(self, frame, row_count):
        """ Create a label with an asterisk """
        label = ctk.CTkLabel(frame,
                             text="*comma-separated list",
                             justify='left',
                             font=("Arial", 12))
        label.grid(row=row_count,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)

    def load_form(self, form_path):
        """ Read a yaml form from the specified path. Check if it
            is a valid form. Translate it into a dictionary that 
            will later be rendered
        """
        with open(form_path, 'r') as file:
            self.original_form_data = yaml.safe_load(file)

        #print("\n\nORIGINAL FORM DATA")
        #for k,v in self.original_form_data.items():
        #    print(k,v)
        #print("\n\n")

    def render_form(self):
        """ Render the form based on the loaded yaml data """

        # Frame for core items
        self.core_frame = ctk.CTkFrame(self.form_frame)
        self.core_frame_rowcounter = 0
        self.core_frame.grid(row=0,
                              column=0,
                              sticky="nsew",
                              padx=self.frame_x_padding,
                                pady=self.frame_y_padding)
        self.core_frame.grid_columnconfigure(0, weight=1)
        self.core_frame.grid_columnconfigure(1, weight=3)
        # Title label for the frame
        title_label = ctk.CTkLabel(self.core_frame,
                                   text="Core",
                                   font=("Arial", self.title_font_size))
        title_label.grid(row=self.core_frame_rowcounter,
                         column=0,
                         sticky="w",
                         pady=self.item_y_padding,
                         padx=self.item_x_padding)
        self.core_frame_rowcounter += 1

        core_has_lists = False

        for key, value in self.original_form_data.items():
            # Check if the value is a dictionary, a list, a string or None
            if isinstance(value, dict):
                item_has_lists = False
                new_frame = ctk.CTkFrame(self.form_frame)
                new_frame.grid(row=self.frame_row_counter,
                               column=0,
                               sticky="nsew",
                               padx=self.frame_x_padding,
                               pady=self.frame_y_padding)
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
                    if isinstance(subvalue, list):
                        item_has_lists = True
                if item_has_lists:
                    self.create_asterisk_label(new_frame, self.form_data[key]["row_counter"])
            else: # We have either a core item or a nested list
                if isinstance(value, list):
                    # Is it a core item or a list of dictionaries?
                    if len(value) > 0 and all(isinstance(item, dict) for item in value):
                        # These are nested dictionaries
                        self.create_list_of_nested_items(key, value)
                    elif (len(value) == 0) or (not isinstance(value[0], dict)):
                        # These is a core item list
                        self.create_core_item(key, value)
                        core_has_lists = True
                    else:
                        # Make a popup error message
                        showerror("Error", "Invalid form data. Please check the yaml file.")
                        return
                else:
                    # This is a non-list core item
                    self.create_core_item(key, value)
        if core_has_lists:
            self.create_asterisk_label(self.core_frame, self.core_frame_rowcounter)


    def create_list_of_nested_items(self, key, itemlist):
        counter = 0
        # Create a numbered frame with entry fields for each item
        for item in itemlist:
            has_lists = False # are any of the subvalues lists?
            counter += 1
            numbered_key = f"{key} #{counter}"
            new_frame = ctk.CTkFrame(self.form_frame)
            new_frame.grid(row=self.frame_row_counter,
                           column=0,
                           sticky="nsew",
                            padx=self.frame_x_padding,
                            pady=self.frame_y_padding)
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
                if isinstance(subvalue, list):
                    has_lists = True
            if has_lists:
                self.create_asterisk_label(new_frame, self.form_data[numbered_key]["row_counter"])


    def create_string_entry(self, frame, row_count, parent_key, key, value):
        """ Create a label and a string entry field.
            Put in the default value.
            Add the entry to form_data.
        """
        # Create the left label
        text = YAML_PRETTYNAMES[key]
        if isinstance(value, list):
            text += "*"
        label = ctk.CTkLabel(frame, text=text)
        label.grid(row=row_count,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=(self.item_y_padding, 0))
        
        # Create the entry field
        entry = ctk.CTkEntry(frame)
        entry.grid(row=row_count,
                   column=1,
                   sticky="nsew",
                   pady=(self.item_y_padding, 0),
                   padx=self.item_x_padding)
        
        # Put default values into the field and write to form_data
        if isinstance(value, list):
            value = [str(x) for x in value]
            value = ", ".join(value)
            entry.insert(0, value)
            if parent_key == 'Core':
                self.form_data[key] = {"type": "corelist", "widget": entry}
            else:
                self.form_data[parent_key]["items"][key] = {"type": "list",
                                                            "widget": entry}
        else:
            if value is not None:
                entry.insert(0, str(value))
            if parent_key == 'Core':
                self.form_data[key] = {"type": "core", "widget": entry}
            else:
                self.form_data[parent_key]["items"][key] = {"type": "core",
                                                            "widget": entry}

        # Add a help button
        help_button = ctk.CTkButton(frame,
                                    text="?",
                                    width=30,
                                    command=lambda: self.show_help(key))
        help_button.grid(row=row_count,
                         column=2,
                         sticky="w",
                         pady=0, 
                         padx=(0,self.item_x_padding))

    def create_single_filepicker(self, frame, row_count, parent_key, key, value):
        """ Create a single-item filepicker with a label, a button and a
            picked-file-label.
            Read in the list of filepaths from value and write them to form_data
        """
        # Crteate the left label
        text = YAML_PRETTYNAMES[key]
        label = ctk.CTkLabel(frame, text=text)
        label.grid(row=row_count,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)
        
        # Create a frame for the pick button and the picked-file-label
        miniframe = ctk.CTkFrame(frame, fg_color="transparent")
        miniframe.grid(row=row_count,
                       column=1,
                       sticky="nsew",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)
        miniframe.grid_columnconfigure(0, weight=1)
        miniframe.grid_columnconfigure(1, weight=3)
        miniframe.grid_rowconfigure(0, weight=1)

        # Create the picked-file-label
        pathlabel = ctk.CTkLabel(miniframe,
                                 text="Not selected",
                                 wraplength=100)	
        pathlabel.grid(row=0,
                       column=1,
                       sticky="e",
                       pady=self.item_y_padding,
                       padx=0)
        
        # Create file picker button
        button = ctk.CTkButton(miniframe,
                               text="Pick file",
                               width=50,
                               command=lambda: self.pick_file(parent_key,
                                                              key,
                                                              pathlabel))
        button.grid(row=0,
                    column=0,
                    sticky="w",
                    pady=0,
                    padx=self.item_x_padding)

        # Set form_data
        self.form_data[parent_key]["items"][key] = {"type": "singlefile",
                                                    "widget": None}

        # Read in the path from value
        if value is not None:
            if not parent_key in self.picked_files:
                self.picked_files[parent_key] = {}
            self.picked_files[parent_key][key] = value
            self.form_data[parent_key]["items"][key] = {"type": "singlefile",
                                                        "widget": None,
                                                        "path": value}
            truncated_path = self.controller.truncate_display_path(value, max_display_len=30)
            pathlabel.configure(text=truncated_path)

    def create_multi_filepicker(self, frame, row_count, parent_key, key, value):
        """ Create a multi-item filepicker with a label, a button and a
            number-of-picked-files-label
        """
        # Create the left label
        text = YAML_PRETTYNAMES[key]
        label = ctk.CTkLabel(frame, text=text)
        label.grid(row=row_count,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)

        # Create a frame for the pick button, clear button and
        # number-of-picked-files label
        miniframe = ctk.CTkFrame(frame, fg_color="transparent")
        miniframe.grid(row=row_count,
                       column=1,
                       sticky="nsew",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)
        miniframe.grid_columnconfigure(0, weight=1)
        miniframe.grid_columnconfigure(1, weight=1)
        miniframe.grid_columnconfigure(2, weight=3)
        miniframe.grid_rowconfigure(0, weight=0)
        
        # Create the number-of-picked-files label
        pathlabel = ctk.CTkLabel(miniframe,
                                 text="0 files picked",
                                 wraplength=100)
        pathlabel.grid(row=0,
                       column=2,
                       sticky="e",
                       pady=self.item_y_padding,
                       padx=0)

        # Create file picker button
        button = ctk.CTkButton(miniframe,
                               text="Pick file",
                               width=50,
                               command=lambda: self.pick_multifile(parent_key,
                                                                   key,
                                                                   pathlabel))
        button.grid(row=0,
                    column=0,
                    sticky="w",
                    pady=self.item_y_padding,
                    padx=0)

        # Create clear button
        clear_button = ctk.CTkButton(miniframe,
                                     text="Clear files",
                                     width=50,
                                     command=lambda: self.clear_files(parent_key,
                                                                      key,
                                                                      pathlabel))
        clear_button.grid(row=0,
                          column=1,
                          sticky="w",
                          pady=0,
                          padx=(self.item_x_padding,0))

        # Set form data
        if parent_key == 'Core':
            self.form_data[key] = {"type": "multifile",
                                   "widget": None}
        else:
            self.form_data[parent_key]["items"][key] = {"type": "multifile",
                                                        "widget": None}

        # Read in the paths from value
        if value is not None:
            for path in value:
                if not parent_key in self.picked_filelists:
                    self.picked_filelists[parent_key] = {}
                if not key in self.picked_filelists[parent_key]:
                    self.picked_filelists[parent_key][key] = []
                if path not in self.picked_filelists[parent_key][key]:
                    self.picked_filelists[parent_key][key].append(path)
                    pathlabel.configure(text=f"{len(self.picked_filelists[parent_key][key])} files picked")

    def create_core_item(self, key, value):
        if key in YAML_SINGLE_FILEKEYS:
            # throw error: core items are not supposed to have single a filepicker
            showerror("Error", f"Core item {key} is not supposed to have a single-item filepicker")
            return
        elif key in YAML_MULTI_FILEKEYS:
            self.create_multi_filepicker(self.core_frame,
                                         self.core_frame_rowcounter,
                                         'Core',
                                         key,
                                         value)
        else:
            # Create a regular item in the core_frame
            self.create_string_entry(self.core_frame,
                                     self.core_frame_rowcounter,
                                     'Core',
                                     key,
                                     value)
        self.core_frame_rowcounter += 1

    def create_nested_item(self, parent_key, key, value):
        if key in YAML_SINGLE_FILEKEYS:
            filepicker = 'single'
        elif key in YAML_MULTI_FILEKEYS:
            filepicker = 'multi'
        else:
            filepicker = None

        frame = self.form_data[parent_key]["frame"]
        row_counter = self.form_data[parent_key]["row_counter"]

        if not filepicker:
            self.create_string_entry(frame, row_counter, parent_key, key, value)

        elif filepicker == 'single':
            self.create_single_filepicker(frame,
                                          row_counter,
                                          parent_key,
                                          key,
                                          value)
        elif filepicker == 'multi':
            self.create_multi_filepicker(frame, row_counter, parent_key, key, value)
                
        self.form_data[parent_key]["row_counter"] += 1

    def pick_multifile(self, parent_key, key, pathlabel):
        file_path = filedialog.askopenfilenames()

        if file_path:
            if not parent_key in self.picked_filelists:
                self.picked_filelists[parent_key] = {}
            if not key in self.picked_filelists[parent_key]:
                self.picked_filelists[parent_key][key] = []
            if file_path not in self.picked_filelists[parent_key][key]:
                self.picked_filelists[parent_key][key].append(file_path)
                pathlabel.configure(text=f"{len(self.picked_filelists[parent_key][key])} files picked")
            else:
                showerror("Error", "This file was already picked")

    def pick_file(self, parent_key, key, pathlabel):
        file_path = filedialog.askopenfilename()

        if file_path:
            if not parent_key in self.picked_files:
                self.picked_files[parent_key] = {}
            self.picked_files[parent_key][key] = file_path
            self.form_data[parent_key]["items"][key]["path"] = file_path
            truncated_path = self.controller.truncate_display_path(file_path, max_display_len=30)
            pathlabel.configure(text=truncated_path)
        else:
            pathlabel.configure(text="Not selected")

    def clear_files(self, parent_key, key, pathlabel):
        if parent_key in self.picked_filelists:
            if key in self.picked_filelists[parent_key]:
                self.picked_filelists[parent_key].pop(key)
                pathlabel.configure(text="0 files picked")

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
        
        # print("\n\n LE FORM DATA")
        # for k, v in self.form_data.items():
        #     print(k)
        #     for p,q in v.items():
        #         if p == "widget":
        #             print(p)
        #         else:
        #             print(p,q)

