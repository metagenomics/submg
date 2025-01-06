# pages/config_form_page.py
import os
import customtkinter as ctk
import yaml
from tkinter import filedialog
from tkinter.messagebox import showerror, askyesno
from .base import BasePage
from submg.modules.configGen import write_gui_yaml
from submg.modules.statConf import YAMLCOMMENTS, GUICOMMENTS, GUIEXAMPLES, GUILINKS, YAML_PRETTYNAMES, YAML_MULTI_FILEKEYS, YAML_SINGLE_FILEKEYS, YAML_DIRKEYS, GUI_STATIC_ADDITIONAL_FIELDS
import webbrowser

class ConfigFormPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Form")

        # Static variables
        self.special_fieldnames = {
            'manifest': 'ADDITIONAL_MANIFEST_FIELDS',
            'samplesheet': 'ADDITIONAL_SAMPLESHEET_FIELDS',
        }


        self.item_font = 'Arial'
        self.title_font = 'Arial'
        self.item_font_size = 12
        self.title_font_size = 15
        self.item_x_padding = 10
        self.item_y_padding = 2
        self.frame_x_padding = 0
        self.frame_y_padding = 5

        # Create main_frame to hold form_frame and help_frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, padx=(5,5), pady=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.configure_frame_columns(self.main_frame, [10, 0])

        # Create the form_frame as a CTkScrollableFrame
        self.form_frame = ctk.CTkScrollableFrame(self.main_frame,
                                                 border_color="#8C8C8C",
                                                 border_width=2,
                                                 fg_color="transparent",)
        self.form_frame.grid(row=0,
                             column=0,
                             padx=5,
                             pady=(0,10),
                             rowspan=2,
                             sticky="nsew")
        self.padding_in_scrollable(self.form_frame)
        self.form_frame.grid_rowconfigure(0, weight=0)
        self.form_frame.grid_columnconfigure(0, weight=1)

        # Help text frame, to the right of the form_frame
        self.help_frame = ctk.CTkFrame(self.main_frame,
                                       border_color="#8C8C8C",
                                       border_width=2,
                                       fg_color="transparent")
        self.help_frame.grid(row=0,
                             column=1,
                             padx=5,
                             pady=(0,10),
                             sticky="nsew")
        self.help_frame.grid_rowconfigure(0, weight=0)
        self.help_frame.grid_rowconfigure(1, weight=0)
        self.help_frame.grid_columnconfigure(0, weight=1)

        self.help_title = ctk.CTkLabel(
            self.help_frame,
            text="Help & Examples\n"+80*" ",
            font=(self.title_font, self.title_font_size))
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
            font=(self.item_font, self.item_font_size),
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
            font=("Courier", self.item_font_size)
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

        # Buttons in the bottom right of the screen
        self.button_frame = ctk.CTkFrame(self.main_frame,
                                         fg_color="transparent")
        self.button_frame.grid(row=1,
                               column=1,
                               padx=5,
                               pady=(0,12),
                               sticky="nsew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.save_config_button = ctk.CTkButton(
            self.button_frame,
            text="Save as",
            command=lambda: self.save_config()
        )
        self.save_config_button.grid(row=1,
                                     column=0,
                                     padx=0,
                                     pady=(0,5),
                                     sticky="nsew")
        self.go_to_submission_button = ctk.CTkButton(
            self.button_frame,
            text="Go to Submission",
            command=lambda: self.go_to_submission()
        )
        self.go_to_submission_button.grid(row=2,
                                          column=0,
                                          padx=0,
                                          pady=(0,0),
                                          sticky="nsew")

        # The dictionary that will keep the form structure and user input
        self.form_data = {}
        self.frame_row_counter = 1

    def padding_in_scrollable(self, s_frame: ctk.CTkScrollableFrame):
        """Adds padding to scrollbar of a scrollable frame."""
        
        if scrollbar:=getattr(s_frame, "_scrollbar", None):
            padding = s_frame.cget("border_width") * 2
            ctk.CTkScrollbar.grid_configure(scrollbar, padx=(0, padding))   

    def show_help(self, key):
        """Fetch the help text from YAMLCOMMENTS and display it in help_frame."""
        # Show the help text
        help_text = self.get_comment(key)
        help_text += "\n\n\nExamples:"
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
                font=(self.item_font, 12),
                command=lambda url=link_url: webbrowser.open_new(url)
            )
            hyperlink_button.grid(row=row, column=0, padx=5, pady=5, sticky="nsew")
            row += 1

    def configure_frame_columns(self, frame, weighlist):
        """ Configure the columns of a frame """
        for i, weight in enumerate(weighlist):
            frame.grid_columnconfigure(i, weight=weight)


    def create_asterisk_label(self, frame, row_count):
        """ Create a label with an asterisk """
        label = ctk.CTkLabel(frame,
                             text="*comma-separated list",
                             justify='left',
                             font=(self.item_font, self.item_font_size-2, 'italic'))
        label.grid(row=row_count,
                   column=0,
                   sticky="w",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)

    def load_form(self, form_path):
        """ Read a yaml form from the specified path. Translate it into a
            dictionary that will later be rendered. Remove the
            submission_outline key from the dictionary.
        """
        with open(form_path, 'r') as file:
            self.original_form_data = yaml.safe_load(file)

        if 'submission_outline' in self.original_form_data:
            outline_items = self.original_form_data['submission_outline']
            for item in self.controller.submission_items.keys():
                if item in outline_items:
                    self.controller.submission_items[item] = True
                else:
                    self.controller.submission_items[item] = False
            self.original_form_data.pop('submission_outline')

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
        self.configure_frame_columns(self.core_frame, [1, 2, 0])
        # Title label for the frame
        title_label = ctk.CTkLabel(self.core_frame,
                                   text="Core",
                                   font=(self.title_font, self.title_font_size))
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

                self.form_data[key] = {"type": "nested",
                                        "frame": None,
                                        "row_counter": 0,
                                        "items": {}}

                new_frame  = self.make_form_fields(
                    title=YAML_PRETTYNAMES[key],
                    data=value,
                    parent_key=key)

                self.form_data[key]["frame"] = new_frame

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
            

    def additional_field_command(self,
                                 key,
                                 frame,
                                 manifest_or_samplesheet):
        """ Command to create an additional field """
        def command():
            self.create_additional_field(
                frame,
                key,
                manifest_or_samplesheet
            )
        return command

    
    def make_form_fields(self, title, data, parent_key):
        """ Create fields for a nested dictionary
        """
        item_has_lists = False
        
        # Create new frame
        new_frame = ctk.CTkFrame(self.form_frame)
        new_frame.grid(row=self.frame_row_counter,
                       column=0,
                       sticky="nsew",
                       padx=self.frame_x_padding,
                       pady=self.frame_y_padding)
        self.configure_frame_columns(new_frame, [1, 3, 0])
        self.frame_row_counter += 1

        # Create title label for frame
        title_label = ctk.CTkLabel(new_frame,
                                   text=title,
                                   font=(self.item_font, self.title_font_size))
        title_label.grid(row=0,
                         column=0,
                         sticky="w",
                         padx=self.item_x_padding,
                         pady=self.item_y_padding)
        self.form_data[parent_key]["row_counter"] += 1

        # Handle the regular fields, collect the additional fields
        additional_manifest_fields = "not found"
        additional_samplesheet_fields = "not found"
        for subkey, subvalue in data.items():
            if subkey == self.special_fieldnames['manifest']:
                additional_manifest_fields = subvalue
            elif subkey == self.special_fieldnames['samplesheet']:
                additional_samplesheet_fields = subvalue
            else:
                self.create_nested_item(parent_key, subkey, subvalue, new_frame)
                if isinstance(subvalue, list):
                    item_has_lists = True   

        # Handle the additional samplesheet fields
        if not additional_samplesheet_fields == "not found":
            self.form_data[parent_key]["items"]["additional_samplesheet_fields"] = {
                'counter': 0,
            }

            # Create a frame for the additional samplesheet fields
            additional_samplesheet_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
            additional_samplesheet_frame.grid(row=self.form_data[parent_key]["row_counter"],
                                                column=0,
                                                sticky="nsew",
                                                padx=0,
                                                pady=0,
                                                columnspan=3)
            self.configure_frame_columns(additional_samplesheet_frame, [1, 2, 0])
            self.form_data[parent_key]["row_counter"] += 1

            # Create a title label & help button
            title_label = ctk.CTkLabel(additional_samplesheet_frame,
                                        text="Additional Fields (Samplesheet)",
                                        font=(self.item_font, self.item_font_size+2))
            title_label.grid(row=0,
                                column=0,
                                sticky="w",
                                padx=self.item_x_padding,
                                pady=(20, self.item_y_padding))

            help_button = ctk.CTkButton(additional_samplesheet_frame,
                                        text="?",
                                        width=30,
                                        command=lambda: self.show_help(self.special_fieldnames['samplesheet']))
            help_button.grid(row=0,
                                column=2,
                                sticky="w",
                                pady=(20, self.item_y_padding),
                                padx=self.item_x_padding)
            
            # Create static fields for the items already existing in the config
            if isinstance(additional_samplesheet_fields, dict):
                for field, value in additional_samplesheet_fields.items():
                    self.create_additional_field(
                        additional_samplesheet_frame,
                        parent_key,
                        'additional_samplesheet_fields',
                        field_name=field,
                        field_value=value
                    )
                    # Counter is incremented in create_additional_field
                    # self.form_data[parent_key]["items"]["additional_samplesheet_fields"]['counter'] += 1
                    if isinstance(value, list):
                        item_has_lists = True
            # Create a button to allow users to add more fields
            add_samplesheet_field_button = ctk.CTkButton(
                new_frame,
                text="Add Samplesheet Field",
                width=15,
                command=self.additional_field_command(parent_key,
                                                      additional_samplesheet_frame,
                                                      'additional_samplesheet_fields')
            )
            add_samplesheet_field_button.grid(row=self.form_data[parent_key]["row_counter"],
                                                column=0,
                                                sticky="w",
                                                padx=self.item_x_padding,
                                                pady=(self.item_y_padding,3*self.item_y_padding))
            self.form_data[parent_key]["row_counter"] += 1

        # Handle the additional manifest fields
        if not additional_manifest_fields == "not found":
            self.form_data[parent_key]["items"]["additional_manifest_fields"] = {
                'counter': 0,
            }


            # Create a frame for the additional manifest fields
            additional_manifest_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
            additional_manifest_frame.grid(row=self.form_data[parent_key]["row_counter"],
                                            column=0,
                                            sticky="nsew",
                                            padx=0,
                                            pady=0,
                                            columnspan=3)
            self.form_data[parent_key]["row_counter"] += 1
            self.configure_frame_columns(additional_manifest_frame, [1, 2, 0])
            

            # Create a title label & help button
            title_label = ctk.CTkLabel(additional_manifest_frame,
                                        text="Additional Fields (Manifest)",
                                        font=(self.item_font, self.item_font_size+2))
            title_label.grid(row=0,
                                column=0,
                                sticky="w",
                                padx=self.item_x_padding,
                                pady=(20, self.item_y_padding))

            help_button = ctk.CTkButton(additional_manifest_frame,
                                        text="?",
                                        width=30,
                                        command=lambda: self.show_help(self.special_fieldnames['manifest']))
            help_button.grid(row=0,
                                column=2,
                                sticky="e",
                                pady=(20, self.item_y_padding),
                                padx=self.item_x_padding)

            # Create static fields for the items already existing in the config
            if isinstance(additional_manifest_fields, dict):
                for field, value in additional_manifest_fields.items():
                    self.create_additional_field(
                        additional_manifest_frame,
                        parent_key,
                        'additional_manifest_fields',
                        field_name=field,
                        field_value=value
                    )
                    # Counter is incremented in create_additional_field
                    # self.form_data[parent_key]["items"]["additional_manifest_fields"]['counter'] += 1
                    if isinstance(value, list):
                        item_has_lists = True
            # Create a button to allow users to add more fields
            add_manifest_field_button = ctk.CTkButton(
                new_frame,
                text="Add Manifest Field",
                width=15,
                command=self.additional_field_command(parent_key,
                                                        additional_manifest_frame,
                                                        'additional_manifest_fields')
            )
            add_manifest_field_button.grid(row=self.form_data[parent_key]["row_counter"],
                                           column=0,
                                           sticky="w",
                                           padx=self.item_x_padding,
                                           pady=(self.item_y_padding, 3*self.item_y_padding))
            self.form_data[parent_key]["row_counter"] += 1

        # Add the asterisk label
        if item_has_lists:
            self.create_asterisk_label(new_frame,
                                       self.form_data[parent_key]["row_counter"])

        return new_frame
        

    def create_list_of_nested_items(self, key, itemlist):
        """ For a list of nested items, create a frame for each item
        """
        counter = 0
        # Create a numbered frame with entry fields for each item
        for item in itemlist:
            counter += 1
            numbered_key = f"{key} #{counter}"
            self.form_data[numbered_key] = {"type": "nested_numbered",
                                            "frame": None,
                                            "row_counter": 0,
                                            "items": {}}
            title = f"{YAML_PRETTYNAMES[key]} #{counter}"
            new_frame = self.make_form_fields(title=title,
                                              data=item,
                                              parent_key=numbered_key)
            self.form_data[numbered_key]["frame"] = new_frame


    def create_string_entry(self, frame, row_count, parent_key, key, value, is_additonal=False):
        """ Create a label and a string entry field.
            Put in the default value.
            Add the entry to form_data.
        """
        # Create the left label
        text = YAML_PRETTYNAMES.get(key, key)
        if isinstance(value, list):
            text += "*"
        outline_frame = ctk.CTkFrame(frame)
        outline_frame.grid(row=row_count,
                           column=0,
                           sticky="nsew",
                           padx=self.item_x_padding,
                           pady=(self.item_y_padding, 0))
        label = ctk.CTkLabel(outline_frame,
                             font=(self.item_font, self.item_font_size),
                             anchor=ctk.W,
                             text=text)
        label.grid(row=0,
                   column=0,
                   sticky="ew",
                   padx=self.item_x_padding,
                   pady=(self.item_y_padding, 0))

        
        # Create the entry field
        entry = ctk.CTkEntry(frame)
        entry.grid(row=row_count,
                   column=1,
                   sticky="ew",
                   pady=(self.item_y_padding, 0),
                   padx=self.item_x_padding)
        
        if not is_additonal:
            # Put default values into the field and write to form_data
            if isinstance(value, list):
                value = [str(x) for x in value]
                value = ", ".join(value)
                entry.insert(0, value)
                if parent_key == 'Core':
                    self.form_data[key] = {"type": "list", "widget": entry}
                else:
                    self.form_data[parent_key]["items"][key] = {"type": "list",
                                                                "widget": entry}
            else:
                if value is not None:
                    entry.insert(0, str(value))
                if parent_key == 'Core':
                    self.form_data[key] = {"type": "string", "widget": entry}
                else:
                    self.form_data[parent_key]["items"][key] = {"type": "string",
                                                                "widget": entry}

        # Add a help button
        help_button = ctk.CTkButton(frame,
                                    text="?",
                                    width=30,
                                    command=lambda: self.show_help(key))
        help_button.grid(row=row_count,
                         column=2,
                         sticky="e",
                         pady=0, 
                         padx=self.item_x_padding)

    def create_single_filepicker(self, frame, row_count, parent_key, key, value):
        """ Create a single-item filepicker with a label, a button and a
            picked-file-label.
            Read in the list of filepaths from value and write them to form_data
        """
        # Crteate the left label
        text = YAML_PRETTYNAMES[key]
        outline_frame = ctk.CTkFrame(frame)
        outline_frame.grid(row=row_count,
                           column=0,
                           sticky="nsew",
                           padx=self.item_x_padding,
                           pady=(self.item_y_padding, 0))
        label = ctk.CTkLabel(outline_frame,
                             font=(self.item_font, self.item_font_size),
                             anchor=ctk.W,
                             text=text)
        label.grid(row=0,
                   column=0,
                   sticky="ew",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)
        
        # Create a frame for the pick button and the picked-file-label
        miniframe = ctk.CTkFrame(frame, fg_color="transparent")
        miniframe.grid(row=row_count,
                       column=1,
                       sticky="nsew",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)
        self.configure_frame_columns(miniframe, [0, 10])
        miniframe.grid_rowconfigure(0, weight=1)

        # Create the picked-file-label
        pathlabel = ctk.CTkLabel(miniframe,
                                 font=("Courier", 12),
                                 text="no file selected",
                                 wraplength=250)	
        pathlabel.grid(row=0,
                       column=1,
                       sticky="ew",
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
                    padx=(0,self.item_x_padding))

        # Add help button
        help_button = ctk.CTkButton(frame,
                                    text="?",
                                    width=30,
                                    command=lambda: self.show_help(key))
        help_button.grid(row=row_count,
                         column=2,
                         sticky="e",
                         pady=0,
                         padx=self.item_x_padding)

        # Set form_data
        self.form_data[parent_key]["items"][key] = {"type": "singlefile",
                                                    "widget": None}

        # Read in the path from value
        if value is not None:
            #if not parent_key in self.picked_files:
            #    self.picked_files[parent_key] = {}
            #self.picked_files[parent_key][key] = value
            self.form_data[parent_key]["items"][key] = {"type": "singlefile",
                                                        "widget": None,
                                                        "path": value}
            truncated_path = self.controller.truncate_display_path(value, max_display_len=14)
            pathlabel.configure(text=truncated_path)

    def create_multi_filepicker(self, frame, row_count, parent_key, key, value):
        """ Create a multi-item filepicker with a label, a button and a
            number-of-picked-files-label
        """
        # Create the left label
        text = YAML_PRETTYNAMES[key]
        outline_frame = ctk.CTkFrame(frame)
        outline_frame.grid(row=row_count,
                           column=0,
                           sticky="nsew",
                           padx=self.item_x_padding,
                           pady=(self.item_y_padding, 0))
        label = ctk.CTkLabel(outline_frame,
                             font=(self.item_font, self.item_font_size),
                             anchor=ctk.W,
                             text=text)
        label.grid(row=0,
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
        self.configure_frame_columns(miniframe, [1, 2, 1])
        miniframe.grid_rowconfigure(0, weight=0)
        
        # Create the number-of-picked-files label
        pathlabel = ctk.CTkLabel(miniframe,
                                 font=("Courier", 12),
                                 text="picked: 0",
                                 wraplength=200)
        pathlabel.grid(row=0,
                       column=1,
                       sticky="ew",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)

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
                    pady=0,
                    padx=(0,self.item_x_padding))

        # Create clear button
        clear_button = ctk.CTkButton(miniframe,
                                     text="Clear files",
                                     fg_color=self.controller.colors['red'],
                                     width=50,
                                     command=lambda: self.clear_files(parent_key,
                                                                      key,
                                                                      pathlabel))
        clear_button.grid(row=0,
                          column=2,
                          sticky="e",
                          pady=0,
                          padx=0)
        
        # Add help button
        help_button = ctk.CTkButton(frame,
                                    text="?",
                                    width=30,
                                    command=lambda: self.show_help(key))
        help_button.grid(row=row_count,
                         column=2,
                         sticky="e",
                         pady=0,
                         padx=self.item_x_padding)

        # Set form data
        if parent_key == 'Core':
            self.form_data[key] = {"type": "multifile",
                                   "widget": None,
                                    "pathlist": []}
        else:
            self.form_data[parent_key]["items"][key] = {"type": "multifile",
                                                        "widget": None,
                                                        "pathlist": []}

        # Read in the paths from value
        if value is not None:
            if not isinstance(value, list):
                value = [value]

            #if not parent_key in self.picked_filelists:
            #    self.picked_filelists[parent_key] = {}
            #self.picked_files[parent_key][key] = value
            if parent_key == 'Core':
                self.form_data[key] = {"type": "multifile",
                                        "widget": None,
                                        "pathlist": value}
            else:
                self.form_data[parent_key]["items"][key] = {"type": "multifile",
                                                        "widget": None,
                                                        "pathlist": value}
            pathlabel.configure(text=f"picked: {len(value)}")
                
    def create_directory_picker(self, frame, row_count, parent_key, key, value):
        """ Create a directory picker with a label, a button and a
            picked-directory-label.
            Read in the path from value and write it to form_data.
        """
        # Create the left label
        text = YAML_PRETTYNAMES[key]
        outline_frame = ctk.CTkFrame(frame)
        outline_frame.grid(row=row_count,
                           column=0,
                           sticky="nsew",
                           padx=self.item_x_padding,
                           pady=(self.item_y_padding, 0))
        label = ctk.CTkLabel(outline_frame,
                             font=(self.item_font, self.item_font_size),
                             anchor=ctk.W,
                             text=text)
        label.grid(row=0,
                   column=0,
                   sticky="ew",
                   padx=self.item_x_padding,
                   pady=self.item_y_padding)
        
        # Create a frame for the pick button and the picked-directory-label
        miniframe = ctk.CTkFrame(frame, fg_color="transparent")
        miniframe.grid(row=row_count,
                       column=1,
                       sticky="nsew",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)
        self.configure_frame_columns(miniframe, [0, 10])
        miniframe.grid_rowconfigure(0, weight=1)

        # Create the picked-directory-label
        pathlabel = ctk.CTkLabel(miniframe,
                                 font=("Courier", 12),
                                 text="no directory selected",
                                 wraplength=250)
        pathlabel.grid(row=0,
                       column=1,
                       sticky="ew",
                       pady=self.item_y_padding,
                       padx=0)
        
        # Create a directory picker button
        button = ctk.CTkButton(miniframe,
                               text="Pick directory",
                               width=50,
                               command=lambda: self.pick_directory(parent_key,
                                                                   key,
                                                                   pathlabel))
        button.grid(row=0,
                    column=0,
                    sticky="w",
                    pady=0,
                    padx=(0,self.item_x_padding))
        
        # Add help button
        help_button = ctk.CTkButton(frame,
                                    text="?",
                                    width=30,
                                    command=lambda: self.show_help(key))
        
        help_button.grid(row=row_count,
                         column=2,
                         sticky="e",
                         pady=0,
                         padx=self.item_x_padding)
        
        # Set form_data
        self.form_data[parent_key]["items"][key] = {"type": "directory",
                                                    "widget": None}
        
        # Read in the path from value
        if value is not None:
            self.form_data[parent_key]["items"][key] = {"type": "directory",
                                                        "widget": None,
                                                        "path": value}
            truncated_path = self.controller.truncate_display_path(value, max_display_len=14)
            pathlabel.configure(text=truncated_path)

    def create_core_item(self, key, value):
        """ Create a core item in the core_frame
        """
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

    def create_nested_item(self,
                           parent_key,
                           key,
                           value,
                           frame):
        """ Create a nested item in the specified frame.
        """
        if key in YAML_SINGLE_FILEKEYS:
            filepicker = 'single'
        elif key in YAML_MULTI_FILEKEYS:
            filepicker = 'multi'
        elif key in YAML_DIRKEYS:
            filepicker = 'directory'
        else:
            filepicker = None

        #frame = self.form_data[parent_key]["frame"]
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
        elif filepicker == 'directory':
            self.create_directory_picker(frame, row_counter, parent_key, key, value)
                
        self.form_data[parent_key]["row_counter"] += 1

    def remove_additional_field(self,
                                parent_key,
                                key_entry,
                                value_entry,
                                button,
                                manifest_or_samplesheet,
                                rowindex):
        """ Remove an additional field """
        # Destroy widgets
        key_entry.destroy()
        value_entry.destroy()
        button.destroy()
        # Remove the items from the form_data
        self.form_data[parent_key]["items"][manifest_or_samplesheet].pop(rowindex)


    def create_additional_field(self,
                                frame,
                                parent_key,
                                manifest_or_samplesheet,
                                field_name=None,
                                field_value=None):
        """ Creates an empty item to allow a user to add a key-value pair.
            For mandatory fields, creates a label instead of an entry for the
            key and a help button.
        """
        self.form_data[parent_key]["items"][manifest_or_samplesheet]["counter"] += 1
        row = self.form_data[parent_key]["items"][manifest_or_samplesheet]["counter"]
        

        # Check if the field is mandatory
        is_static_field = field_name in GUI_STATIC_ADDITIONAL_FIELDS

        # Create the key widget
        if is_static_field:
            outline_frame = ctk.CTkFrame(frame, fg_color="#CFCFCF")
            outline_frame.grid(row=row,
                               column=0,
                               sticky="nsew",
                               padx=self.item_x_padding,
                               pady=self.item_y_padding)
            key_widget = ctk.CTkLabel(outline_frame,
                                      text=field_name,
                                      anchor=ctk.W,
                                      font=(self.item_font, self.item_font_size))
        else:
            key_widget = ctk.CTkEntry(frame)
            key_widget.insert(0, field_name or "your keyword")

        key_widget.grid(row=row,
                        column=0,
                        sticky="ew",
                        pady=self.item_y_padding,
                        padx=self.item_x_padding)

        # Create the value entry
        value_entry = ctk.CTkEntry(frame)
        if field_value is not None:
            if isinstance(field_value, list):
                field_value = ', '.join(str(item) for item in field_value)
            value_entry.insert(0, field_value)
        value_entry.grid(row=row,
                        column=1,
                        sticky="nsew",
                        pady=self.item_y_padding,
                        padx=self.item_x_padding)

        # Create the appropriate button
        if is_static_field:
            # Help button
            button = ctk.CTkButton(frame,
                                text="?",
                                width=30,
                                command=lambda: self.show_help(field_name))
        else:
            # Remove button
            button = ctk.CTkButton(frame,
                                text="x",
                                width=30,
                                fg_color=self.controller.colors['red'],
                                command=lambda: self.remove_additional_field(parent_key,
                                                                                key_widget,
                                                                                value_entry,
                                                                                button,
                                                                                manifest_or_samplesheet,
                                                                                row))
        button.grid(row=row,
                    column=2,
                    sticky="w",
                    pady=self.item_y_padding,
                    padx=self.item_x_padding)

        # Update form_data
        self.form_data[parent_key]['items'][manifest_or_samplesheet][row] = {
            'type': 'additional_static' if is_static_field else 'additional',
            'key': key_widget,
            'value': value_entry
        }

 


    def pick_multifile(self, parent_key, key, pathlabel):
        """ Pick a single field and add it to the list of picked files in a
            multifile field.
        """
        file_paths = filedialog.askopenfilenames()

        if file_paths:
            if parent_key == 'Core':
                new_files = [fp for fp in file_paths if fp not in self.form_data[key]["pathlist"]]
                if not new_files:
                    showerror("Error", "All selected files were already picked")
                else:
                    self.form_data[key]["pathlist"].extend(new_files)
                    pathlabel.configure(text=f"picked: {len(self.form_data[key]['pathlist'])}")
            else:
                new_files = [fp for fp in file_paths if fp not in self.form_data[parent_key]["items"][key]["pathlist"]]
                if not new_files:
                    showerror("Error", "All selected files were already picked")
                else:
                    self.form_data[parent_key]["items"][key]["pathlist"].extend(new_files)
                    pathlabel.configure(text=f"picked: {len(self.form_data[parent_key]['items'][key]['pathlist'])}")


    def pick_file(self, parent_key, key, pathlabel):
        """ Pick a file and add it to the form_data
        """
        file_path = filedialog.askopenfilename()

        if file_path:
            self.form_data[parent_key]["items"][key]["path"] = file_path
            truncated_path = self.controller.truncate_display_path(file_path, max_display_len=14)
            pathlabel.configure(text=truncated_path)
        else:
            pathlabel.configure(text="no file selected")

    def pick_directory(self, parent_key, key, pathlabel):
        directory = filedialog.askdirectory()

        if directory:
            self.form_data[parent_key]["items"][key]["path"] = directory
            truncated_path = self.controller.truncate_display_path(directory, max_display_len=14)
            pathlabel.configure(text=truncated_path)
        else:
            pathlabel.configure(text="no directory selected")

    def get_comment(self, key):
        """ Try to get a comment for the key from GUICOMMENTS. Use YAMLCOMMENTS
            as a fallback. If no comment is found, return a default message.
        """
        default = "No help available for this item"
        return GUICOMMENTS.get(key, YAMLCOMMENTS.get(key, default))

    def clear_files(self, parent_key, key, pathlabel):
        """ Clear the list of picked files """
        if parent_key == 'Core':
            self.form_data[key]["pathlist"] = []
        else:
            self.form_data[parent_key]["items"][key]["pathlist"] = []
        pathlabel.configure(text="picked: 0")

    def extract_data(self, input_dict):
        """
        Recursively extract data from the nested dictionary of widgets in
        self.form_data. The extracted data is stored in a dictionary which
        can be used to write a YAML config file.
        """
        output = {}
        nested_numbered_groups = {}
        other_keys = {}

        # First pass: group 'nested_numbered' items
        for key, value in input_dict.items():
            field_type = value.get('type')
            if field_type == 'nested_numbered':
                # Extract base name by removing the ' #number' suffix
                if ' #' in key:
                    base_name = key.split(' #')[0]
                else:
                    base_name = key
                if base_name not in nested_numbered_groups:
                    nested_numbered_groups[base_name] = []
                nested_numbered_groups[base_name].append(value)
            else:
                other_keys[key] = value

        # Process 'nested_numbered' groups
        for base_name, group in nested_numbered_groups.items():
            output_list = []
            for item in group:
                items = item.get('items', {})
                extracted_item = {}
                for item_key, item_value in items.items():
                    if item_key in ['additional_samplesheet_fields', 'additional_manifest_fields']:
                        # Handle additional fields
                        additional_fields = {}
                        for sub_key, field in item_value.items():
                            if sub_key == 'counter':
                                continue  # skip the counter
                            if field.get('type') not in ['additional', 'additional_static']:
                                continue  # include both 'additional' and 'additional_static'
                            
                            key_entry = field.get('key')
                            value_entry = field.get('value')
                            if key_entry and value_entry:
                                if field.get('type') == 'additional_static':
                                    # For static fields, the key is in a Label widget
                                    field_key = key_entry.cget('text')
                                else:
                                    # For dynamic fields, the key is in an Entry widget
                                    field_key = key_entry.get()
                                
                                field_value = value_entry.get()
                                if ',' in field_value:
                                    # Treat as list
                                    items_list = [itm.strip() for itm in field_value.split(',') if itm.strip()]
                                    additional_fields[field_key] = items_list or None
                                else:
                                    additional_fields[field_key] = field_value or None
                        # Convert key to uppercase with underscores
                        if item_key == 'additional_samplesheet_fields':
                            output_key = 'ADDITIONAL_SAMPLESHEET_FIELDS'
                        elif item_key == 'additional_manifest_fields':
                            output_key = 'ADDITIONAL_MANIFEST_FIELDS'
                        else:
                            output_key = item_key.upper()
                        
                        # Only add to extracted_item if additional_fields is not empty
                        if additional_fields:
                            extracted_item[output_key] = additional_fields
                    else:
                        # Process other items recursively
                        extracted = self.extract_data({item_key: item_value})
                        if extracted:
                            extracted_item.update(extracted)
                # Append the extracted_item to the output_list
                output_list.append(extracted_item or None)
            # Assign the list to the base_name key if not empty
            if output_list:
                output[base_name] = output_list
            else:
                output[base_name] = None

        # Now process other keys as usual
        for key, value in other_keys.items():
            field_type = value.get('type')

            # Skip entries without a 'type' key
            if not field_type:
                if isinstance(value, dict):
                    # Process nested dictionaries recursively
                    nested_data = self.extract_data(value)
                    if nested_data:
                        output[key] = nested_data or None
                continue

            if field_type == 'string':
                widget = value.get('widget')
                if widget:
                    try:
                        # Retrieve string value from the widget
                        output[key] = widget.get() or None
                    except AttributeError:
                        print(f"Warning: Widget for '{key}' does not have a 'get()' method.")
                        output[key] = value.get('default', None)
                else:
                    # Fallback to default value if widget is None
                    output[key] = value.get('default', None)

            elif field_type == 'list':
                widget = value.get('widget')
                if widget:
                    try:
                        # Retrieve comma-separated string from the widget
                        list_str = widget.get()
                        # Split by comma and strip whitespace from each item
                        items = [itm.strip() for itm in list_str.split(',') if itm.strip()]
                        output[key] = items if items else None
                    except AttributeError:
                        print(f"Warning: Widget for '{key}' does not have a 'get()' method.")
                        output[key] = value.get('default', None)
                else:
                    # Fallback to default list if widget is None
                    output[key] = value.get('default', None)

            elif field_type == 'singlefile':
                # Retrieve the file path directly from the 'path' key
                output[key] = value.get('path', None) or None

            elif field_type == 'multifile':
                # Retrieve the list of file paths directly from the 'pathlist' key
                multifile_paths = value.get('pathlist', [])
                if isinstance(multifile_paths, list):
                    output[key] = multifile_paths if multifile_paths else None
                else:
                    print(f"Warning: 'pathlist' for '{key}' should be a list. Converting to list.")
                    output[key] = [multifile_paths] if multifile_paths else None

            elif field_type == 'directory':
                # Retrieve the directory path directly from the 'path' key
                output[key] = value.get('path', None) or None

            elif field_type == 'nested':
                items = value.get('items', {})
                nested_data = {}
                for item_key, item_value in items.items():
                    if item_key in ['additional_samplesheet_fields', 'additional_manifest_fields']:
                        # Handle additional fields
                        additional_fields = {}
                        for row_key, field in item_value.items():
                            if row_key == 'counter':
                                continue  # skip the counter
                            if field.get('type') not in ['additional', 'additional_static']:
                                continue  # include both 'additional' and 'additional_static'
                            
                            key_entry = field.get('key')
                            value_entry = field.get('value')
                            if key_entry and value_entry:
                                if field.get('type') == 'additional_static':
                                    # For static fields, the key is in a Label widget
                                    field_key = key_entry.cget('text')
                                else:
                                    # For dynamic fields, the key is in an Entry widget
                                    field_key = key_entry.get()
                                
                                field_value = value_entry.get()
                                if ',' in field_value:
                                    # Treat as list
                                    items_list = [itm.strip() for itm in field_value.split(',') if itm.strip()]
                                    additional_fields[field_key] = items_list or None
                                else:
                                    additional_fields[field_key] = field_value or None
                        # Convert key to uppercase with underscores
                        if item_key == 'additional_samplesheet_fields':
                            output_key = 'ADDITIONAL_SAMPLESHEET_FIELDS'
                        elif item_key == 'additional_manifest_fields':
                            output_key = 'ADDITIONAL_MANIFEST_FIELDS'
                        else:
                            output_key = item_key.upper()
                        
                        # Only add to nested_data if additional_fields is not empty
                        if additional_fields:
                            nested_data[output_key] = additional_fields
                    else:
                        # Process other items recursively
                        extracted_item = self.extract_data({item_key: item_value})
                        if extracted_item:
                            nested_data.update(extracted_item)
                if nested_data:
                    output[key] = nested_data or None

            elif field_type in ['additional', 'additional_static']:
                # Initialize additional_fields dictionary
                if 'additional_fields' not in output:
                    output['additional_fields'] = {}
                
                key_widget = value.get('key')
                value_entry = value.get('value')
                if key_widget and value_entry:
                    if field_type == 'additional_static':
                        field_key = key_widget.cget('text')
                    else:
                        field_key = key_widget.get()
                    field_value = value_entry.get()
                    if ',' in field_value:
                        # Treat as list
                        items_list = [itm.strip() for itm in field_value.split(',') if itm.strip()]
                        output['additional_fields'][field_key] = items_list or None
                    else:
                        output['additional_fields'][field_key] = field_value or None

            else:
                # Handle other types or skip
                print(f"Warning: Unhandled type '{field_type}' for key '{key}'. Skipping.")
                continue

        return output



    def pretty_print_form_data(self, data, indent=0):
        """
        Pretty print a deeply nested dictionary, replacing CustomTkinter widgets with 'widget'.
        """
        for key, value in data.items():
            # Print the key with the current indentation
            print(" " * indent + str(key) + ": ", end="")

            # Handle the value based on its type
            if isinstance(value, dict):
                # If it's a nested dictionary, call recursively with increased indentation
                print("{")
                self.pretty_print_form_data(value, indent + 4)
                print(" " * indent + "}")
            elif isinstance(value, list):
                # If it's a list, print each item with increased indentation
                print("[")
                for item in value:
                    print(" " * (indent + 4) + str(item) + ",")
                print(" " * indent + "]")
            elif isinstance(value, ctk.CTkBaseClass):
                # Replace customtkinter widget with 'widget'
                print("widget")
            else:
                # Otherwise, print the value directly
                print(repr(value))


    def save_config(self):
        """ Save the configuration to a yaml file """

        # Step 1: Display current configuration
        #self.pretty_print_form_data(self.form_data)
        output = self.extract_data(self.form_data)

        print("form data is\n")
        print(self.form_data)
        print("\npretty form data is")
        self.pretty_print_form_data(self.form_data)
        print("\n")
        print("output is")
        print(output)
        print("\n")

        output['submission_outline'] = []
        for key, value in self.controller.submission_items.items():
            if value:
                output['submission_outline'].append(key)

        #self.pretty_print_form_data(output)

        # Step 2: Open file picker dialog
        outpath = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )

        if not outpath:
            return  # If no file is selected, return without saving

        # # Step 3: Check if the output path exists and confirm overwrite
        # if os.path.exists(outpath):
        #     overwrite = askyesno(
        #         "File Exists",
        #         f"The file '{outpath}' already exists. Do you want to overwrite it?"
        #     )
        #     if not overwrite:
        #         return  # If the user decides not to overwrite, return without saving
        #     else:
        #         os.remove(outpath)     

        # Step 4: Call write_gui_yaml with the extracted data and output path
        write_gui_yaml(output, outpath)
        self.config_saved = True
        self.controller.config_items["form_path"] = outpath
        print(f"Configuration saved to: {outpath}")


    def go_to_submission(self):
        """ Go to the submission page """
        if not self.config_saved:
            msg = ("Please save the configuration before proceeding to the "
                   "submission. Click 'Home' if you want to abort the process.")
            showerror("Please Save", msg)
        else:
            self.controller.show_page("LoadConfigPage")


    def initialize(self):
        """Called whenever controller renders the page"""
        self.config_saved = False
        form_path = self.controller.config_items["form_path"]
        self.load_form(form_path)
        self.render_form()
