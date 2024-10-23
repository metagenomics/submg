# pages/config_form_page.py
import customtkinter as ctk
import yaml
from tkinter import filedialog
from tkinter.messagebox import showerror
from .base import BasePage
from ..modules.statConf import YAMLCOMMENTS, GUICOMMENTS, GUIEXAMPLES, GUILINKS, YAML_PRETTYNAMES, YAML_MULTI_FILEKEYS, YAML_SINGLE_FILEKEYS
import webbrowser

class ConfigFormPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Configuration Form")

        # Static variables
        self.special_fieldnames = {
            'manifest': 'ADDITIONAL_MANIFEST_FIELDS',
            'samplesheet': 'ADDITIONAL_SAMPLESHEET_FIELDS',
        }

        # Formatting
        self.colors = {
            'red': '#a31a15'
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
        self.validate_config_button = ctk.CTkButton(
            self.button_frame,
            text="Validate",
            command=lambda: self.validate_config()
        )
        self.validate_config_button.grid(row=0,
                                         column=0,
                                         padx=0,
                                         pady=(0,5),
                                         sticky="nsew")
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
        self.picked_files = {}
        self.picked_filelists = {}
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

        print("\n\n RENDERING THE FORM \n\n")
        # Frame for core items
        self.core_frame = ctk.CTkFrame(self.form_frame)
        self.core_frame_rowcounter = 0
        self.core_frame.grid(row=0,
                              column=0,
                              sticky="nsew",
                              padx=self.frame_x_padding,
                                pady=self.frame_y_padding)
        self.configure_frame_columns(self.core_frame, [1, 3])
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
            print("\nPROCESSING KEY: ", key)
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

                # item_has_lists = False
                # new_frame = ctk.CTkFrame(self.form_frame)
                # new_frame.grid(row=self.frame_row_counter,
                #                column=0,
                #                sticky="nsew",
                #                padx=self.frame_x_padding,
                #                pady=self.frame_y_padding)
                # self.configure_frame_columns(new_frame, [1, 3, 0])

                # self.frame_row_counter += 1
                # self.form_data[key] = {"type": "nested",
                #                        "frame": new_frame,
                #                        "row_counter": 0,
                #                        "items": {}}
                # # Give the frame a title
                # title_label = ctk.CTkLabel(new_frame,
                #                            text=YAML_PRETTYNAMES[key],
                #                            font=(self.item_font, self.title_font_size))
                # title_label.grid(row=0,
                #                  column=0,
                #                  sticky="w",
                #                  padx=self.item_x_padding,
                #                  pady=self.item_y_padding)
                # self.form_data[key]["row_counter"] += 1

                # additional_manifest_fields = "not found"
                # additional_samplesheet_fields = "not found"
                # for subkey, subvalue in value.items():
                #     # Handle the regular fields, collect the additional fields
                #     if subkey == self.special_fieldnames['manifest']:
                #         additional_manifest_fields = subvalue
                #     elif subkey == self.special_fieldnames['samplesheet']:
                #         additional_samplesheet_fields = subvalue
                #     else:
                #         self.create_nested_item(key, subkey, subvalue)
                #         if isinstance(subvalue, list):
                #             item_has_lists = True
                # # Handle the additional fields
                # if not additional_samplesheet_fields == "not found":
                #     print("I AM HANDLING THE ADDITOINAL FIELDS FOR SAMPLESHEET for key ", key)
                #     self.form_data[key]["items"]["additional_samplesheet_fields"] = {
                #         'counter': 0,
                #     }
                #     # Create a title label & help button
                #     title_label = ctk.CTkLabel(new_frame,
                #                                text="Additional Fields (Samplesheet)",
                #                                font=(self.item_font, self.item_font_size+2))
                #     title_label.grid(row=self.form_data[key]["row_counter"],
                #                      column=0,
                #                      sticky="w",
                #                      padx=self.item_x_padding,
                #                      pady=(20, self.item_y_padding))

                #     help_button = ctk.CTkButton(new_frame,
                #                                 text="?",
                #                                 width=30,
                #                                 command=lambda: self.show_help(self.special_fieldnames['samplesheet']))
                #     help_button.grid(row=self.form_data[key]["row_counter"],
                #                      column=2,
                #                      sticky="w",
                #                      pady=(20, self.item_y_padding),
                #                      padx=self.item_x_padding)
                    
                #     self.form_data[key]["row_counter"] += 1

                #     # Create a frame for the additional samplesheet fields
                #     additional_samplesheet_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
                #     additional_samplesheet_frame.grid(row=self.form_data[key]["row_counter"],
                #                                         column=0,
                #                                         sticky="nsew",
                #                                         padx=0,
                #                                         pady=0,
                #                                         columnspan=3)
                #     self.configure_frame_columns(additional_samplesheet_frame, [1, 3, 0])
                #     self.form_data[key]["row_counter"] += 1

                #     # Create static fields for the items already existing in the config
                #     if isinstance(additional_samplesheet_fields, dict):
                #         for field, value in additional_samplesheet_fields.items():
                #             self.create_string_entry(additional_samplesheet_frame,
                #                                         self.form_data[key]["items"]["additional_samplesheet_fields"]['counter'],
                #                                         key,
                #                                         field,
                #                                         value,
                #                                         is_additonal=True)
                #             self.form_data[key]["items"]["additional_samplesheet_fields"]['counter'] += 1
                #             if isinstance(value, list):
                #                 item_has_lists = True
                #     # Create a button to allow users to add more fields
                #     add_samplesheet_field_button = ctk.CTkButton(
                #         additional_samplesheet_frame,
                #         text="Add Samplesheet Field",
                #         width=15,
                #         command=self.additional_field_command(key,
                #                                               additional_samplesheet_frame,
                #                                               'additional_samplesheet_fields')
                #     )
                #     print("I am adding the add samplesheet field button for key ", key)
                #     add_samplesheet_field_button.grid(row=self.form_data[key]["row_counter"],
                #                                         column=0,
                #                                         sticky="w",
                #                                         padx=self.item_x_padding,
                #                                         pady=self.item_y_padding)
                #     self.form_data[key]["row_counter"] += 1
                # if not additional_manifest_fields == "not found":
                #     print("I AM HANDLING THE ADDITOINAL FIELDS FOR MANIFEST for key ", key)
                #     self.form_data[key]["items"]["additional_manifest_fields"] = {
                #         'counter': 0,
                #     }

                #     # Create a title label & help button
                #     title_label = ctk.CTkLabel(new_frame,
                #                                text="Additional Fields (Manifest)",
                #                                font=(self.item_font, self.item_font_size+2))
                #     title_label.grid(row=self.form_data[key]["row_counter"],
                #                      column=0,
                #                      sticky="w",
                #                      padx=self.item_x_padding,
                #                      pady=(20, self.item_y_padding))

                #     help_button = ctk.CTkButton(new_frame,
                #                                 text="?",
                #                                 width=30,
                #                                 command=lambda: self.show_help(self.special_fieldnames['manifest']))
                #     help_button.grid(row=self.form_data[key]["row_counter"],
                #                      column=2,
                #                      sticky="e",
                #                      pady=(20, self.item_y_padding),
                #                      padx=self.item_x_padding)
                    
                #     self.form_data[key]["row_counter"] += 1

                #     # Create a frame for the additional manifest fields
                #     additional_manifest_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
                #     additional_manifest_frame.grid(row=self.form_data[key]["row_counter"],
                #                                     column=0,
                #                                     sticky="nsew",
                #                                     padx=0,
                #                                     pady=0,
                #                                     columnspan=3)
                #     self.form_data[key]["row_counter"] += 1
                #     self.configure_frame_columns(additional_manifest_frame, [1, 3, 0])
                #     # Create static fields for the items already existing in the config
                #     if isinstance(additional_manifest_fields, dict):
                #         for field, value in additional_manifest_fields.items():
                #             self.create_string_entry(additional_manifest_frame,
                #                                         self.form_data[key]["items"]["additional_manifest_fields"]['counter'],
                #                                         key,
                #                                         field,
                #                                         value,
                #                                         is_additonal=True)
                #             self.form_data[key]["items"]["additional_manifest_fields"]['counter'] += 1
                #             if isinstance(value, list):
                #                 item_has_lists = True
                #     # Create a button to allow users to add more fields
                #     print("I am creating the button for key ", key)
                #     add_manifest_field_button = ctk.CTkButton(
                #         additional_manifest_frame,
                #         text="Add Manifest Field",
                #         width=15,
                #         command=self.additional_field_command(key,
                #                                               additional_manifest_frame,
                #                                               'additional_manifest_fields')
                #     )
                #     add_manifest_field_button.grid(row=self.form_data[key]["row_counter"],
                #                                    column=0,
                #                                    sticky="w",
                #                                    padx=self.item_x_padding,
                #                                    pady=self.item_y_padding)
                #     self.form_data[key]["row_counter"] += 1

                # if item_has_lists:
                #     self.create_asterisk_label(new_frame, self.form_data[key]["row_counter"])
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
        # Auslagern: Adding frame to form_data
        # Increasing the row counter for numbered keys
        
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
            print("I AM HANDLING THE ADDITOINAL FIELDS FOR SAMPLESHEET for key ", parent_key)
            self.form_data[parent_key]["items"]["additional_samplesheet_fields"] = {
                'counter': 0,
            }
            # Create a title label & help button
            title_label = ctk.CTkLabel(new_frame,
                                        text="Additional Fields (Samplesheet)",
                                        font=(self.item_font, self.item_font_size+2))
            title_label.grid(row=self.form_data[parent_key]["row_counter"],
                                column=0,
                                sticky="w",
                                padx=self.item_x_padding,
                                pady=(20, self.item_y_padding))

            help_button = ctk.CTkButton(new_frame,
                                        text="?",
                                        width=30,
                                        command=lambda: self.show_help(self.special_fieldnames['samplesheet']))
            help_button.grid(row=self.form_data[parent_key]["row_counter"],
                                column=2,
                                sticky="w",
                                pady=(20, self.item_y_padding),
                                padx=self.item_x_padding)
            
            self.form_data[parent_key]["row_counter"] += 1

            # Create a frame for the additional samplesheet fields
            additional_samplesheet_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
            additional_samplesheet_frame.grid(row=self.form_data[parent_key]["row_counter"],
                                                column=0,
                                                sticky="nsew",
                                                padx=0,
                                                pady=0,
                                                columnspan=3)
            self.configure_frame_columns(additional_samplesheet_frame, [1, 3, 0])
            self.form_data[parent_key]["row_counter"] += 1

            # Create static fields for the items already existing in the config
            if isinstance(additional_samplesheet_fields, dict):
                for field, value in additional_samplesheet_fields.items():
                    self.create_string_entry(additional_samplesheet_frame,
                                             self.form_data[parent_key]["items"]["additional_samplesheet_fields"]['counter'],
                                             parent_key,
                                             field,
                                             value,
                                             is_additonal=True)
                    self.form_data[parent_key]["items"]["additional_samplesheet_fields"]['counter'] += 1
                    if isinstance(value, list):
                        item_has_lists = True
            # Create a button to allow users to add more fields
            add_samplesheet_field_button = ctk.CTkButton(
                additional_samplesheet_frame,
                text="Add Samplesheet Field",
                width=15,
                command=self.additional_field_command(parent_key,
                                                      additional_samplesheet_frame,
                                                      'additional_samplesheet_fields')
            )
            print("I am adding the add samplesheet field button for key ", parent_key)
            add_samplesheet_field_button.grid(row=self.form_data[parent_key]["row_counter"],
                                                column=0,
                                                sticky="w",
                                                padx=self.item_x_padding,
                                                pady=(self.item_y_padding,3*self.item_y_padding))
            self.form_data[parent_key]["row_counter"] += 1

        # Handle the additional manifest fields
        if not additional_manifest_fields == "not found":
            print("I AM HANDLING THE ADDITOINAL FIELDS FOR MANIFEST for key ", parent_key)
            self.form_data[parent_key]["items"]["additional_manifest_fields"] = {
                'counter': 0,
            }

            # Create a title label & help button
            title_label = ctk.CTkLabel(new_frame,
                                        text="Additional Fields (Manifest)",
                                        font=(self.item_font, self.item_font_size+2))
            title_label.grid(row=self.form_data[parent_key]["row_counter"],
                                column=0,
                                sticky="w",
                                padx=self.item_x_padding,
                                pady=(20, self.item_y_padding))

            help_button = ctk.CTkButton(new_frame,
                                        text="?",
                                        width=30,
                                        command=lambda: self.show_help(self.special_fieldnames['manifest']))
            help_button.grid(row=self.form_data[parent_key]["row_counter"],
                                column=2,
                                sticky="e",
                                pady=(20, self.item_y_padding),
                                padx=self.item_x_padding)
            
            self.form_data[parent_key]["row_counter"] += 1

            # Create a frame for the additional manifest fields
            additional_manifest_frame = ctk.CTkFrame(new_frame, fg_color="transparent")
            additional_manifest_frame.grid(row=self.form_data[parent_key]["row_counter"],
                                            column=0,
                                            sticky="nsew",
                                            padx=0,
                                            pady=0,
                                            columnspan=3)
            self.form_data[parent_key]["row_counter"] += 1
            self.configure_frame_columns(additional_manifest_frame, [1, 3, 0])
            # Create static fields for the items already existing in the config
            if isinstance(additional_manifest_fields, dict):
                for field, value in additional_manifest_fields.items():
                    self.create_string_entry(additional_manifest_frame,
                                                self.form_data[parent_key]["items"]["additional_manifest_fields"]['counter'],
                                                parent_key,
                                                field,
                                                value,
                                                is_additonal=True)
                    self.form_data[parent_key]["items"]["additional_manifest_fields"]['counter'] += 1
                    if isinstance(value, list):
                        item_has_lists = True
            # Create a button to allow users to add more fields
            print("I am creating the button for key ", parent_key)
            add_manifest_field_button = ctk.CTkButton(
                additional_manifest_frame,
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
            # has_lists = False # are any of the subvalues lists?
            # counter += 1
            # numbered_key = f"{key} #{counter}"
            # new_frame = ctk.CTkFrame(self.form_frame)
            # new_frame.grid(row=self.frame_row_counter,
            #                column=0,
            #                sticky="nsew",
            #                 padx=self.frame_x_padding,
            #                 pady=self.frame_y_padding)
            # self.configure_frame_columns(new_frame, [1,3])
            # self.frame_row_counter += 1
            # self.form_data[numbered_key] = {"type": "nested_numbered",
            #                                  "frame": new_frame,
            #                                  "row_counter": 0,
            #                                  "items": {}}
            # # Give the frame a title
            # title = f"{YAML_PRETTYNAMES[key]} #{counter}"
            # title_label = ctk.CTkLabel(new_frame,
            #                            text=title,
            #                            font=(self.title_font, self.title_font_size))
            # title_label.grid(row=0,
            #                  column=0,
            #                  sticky="w",
            #                  padx=self.item_x_padding,
            #                  pady=self.item_y_padding)
            # self.form_data[numbered_key]["row_counter"] += 1

            # for subkey, subvalue in item.items():
            #     self.create_nested_item(numbered_key, subkey, subvalue, new_frame)
            #     if isinstance(subvalue, list):
            #         has_lists = True
            # if has_lists:
            #     self.create_asterisk_label(new_frame, self.form_data[numbered_key]["row_counter"])

    def create_string_entry(self, frame, row_count, parent_key, key, value, is_additonal=False):
        """ Create a label and a string entry field.
            Put in the default value.
            Add the entry to form_data.
        """
        # Create the left label
        text = YAML_PRETTYNAMES[key]
        if isinstance(value, list):
            text += "*"
        label = ctk.CTkLabel(frame,
                             font=(self.item_font, self.item_font_size),
                             text=text)
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
        label = ctk.CTkLabel(frame,
                             font=(self.item_font, self.item_font_size),
                             text=text)
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
            if not parent_key in self.picked_files:
                self.picked_files[parent_key] = {}
            self.picked_files[parent_key][key] = value
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
        label = ctk.CTkLabel(frame,
                             font=(self.item_font, self.item_font_size),
                             text=text)
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
                                     fg_color=self.colors['red'],
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
                    pathlabel.configure(text=f"picked: {len(self.picked_filelists[parent_key][key])}")

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

    def create_nested_item(self,
                           parent_key,
                           key,
                           value,
                           frame):
        if key in YAML_SINGLE_FILEKEYS:
            filepicker = 'single'
        elif key in YAML_MULTI_FILEKEYS:
            filepicker = 'multi'
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
                                manifest_or_samplesheet):
        """ Creates an empty item to allow a user to add a key value pair.
            Also creates a button to remove the item.
        """
        print("Calling create_additional_field for ", parent_key, manifest_or_samplesheet)
        row = self.form_data[parent_key]["items"][manifest_or_samplesheet]["counter"]
        self.form_data[parent_key]["items"][manifest_or_samplesheet]["counter"] += 1
        # Create the left entry field (for the key)
        key_entry = ctk.CTkEntry(frame)
        key_entry.grid(row=row,
                       column=0,
                       sticky="w",
                       pady=self.item_y_padding,
                       padx=self.item_x_padding)
        key_entry.insert(0, "your keyword")
        # Create the right entry (for the value)
        value_entry = ctk.CTkEntry(frame)
        value_entry.grid(row=row,
                         column=1,
                         sticky="nsew",
                         pady=self.item_y_padding,
                         padx=self.item_x_padding)
        value_entry.insert(0, "your value")
        # Create the remove button
        remove_button = ctk.CTkButton(frame,
                                      text="x",
                                      width=30,
                                      fg_color=self.colors['red'],
                                      command=lambda: self.remove_additional_field(parent_key,
                                                                                   key_entry,
                                                                                   value_entry,
                                                                                   remove_button,
                                                                                   manifest_or_samplesheet,
                                                                                   row))
        remove_button.grid(row=row,
                           column=2,
                           sticky="w",
                           pady=self.item_y_padding,
                           padx=self.item_x_padding)
        # Add the new items to the form_data, using the counter as the key
        self.form_data[parent_key]['items'][manifest_or_samplesheet][row] = {
            'key': key_entry,
            'value': value_entry
        }
 



    def pick_multifile(self, parent_key, key, pathlabel):
        file_path = filedialog.askopenfilenames()

        if file_path:
            if not parent_key in self.picked_filelists:
                self.picked_filelists[parent_key] = {}
            if not key in self.picked_filelists[parent_key]:
                self.picked_filelists[parent_key][key] = []
            if file_path not in self.picked_filelists[parent_key][key]:
                self.picked_filelists[parent_key][key].append(file_path)
                pathlabel.configure(text=f"picked: {len(self.picked_filelists[parent_key][key])}")
            else:
                showerror("Error", "This file was already picked")

    def pick_file(self, parent_key, key, pathlabel):
        file_path = filedialog.askopenfilename()

        if file_path:
            if not parent_key in self.picked_files:
                self.picked_files[parent_key] = {}
            self.picked_files[parent_key][key] = file_path
            self.form_data[parent_key]["items"][key]["path"] = file_path
            truncated_path = self.controller.truncate_display_path(file_path, max_display_len=14)
            pathlabel.configure(text=truncated_path)
        else:
            pathlabel.configure(text="no file selected")

    def get_comment(self, key):
        """ Try to get a comment for the key from GUICOMMENTS. Use YAMLCOMMENTS
            as a fallback. If no comment is found, return a default message.
        """
        default = "No help available for this item"
        return GUICOMMENTS.get(key, YAMLCOMMENTS.get(key, default))

    def clear_files(self, parent_key, key, pathlabel):
        if parent_key in self.picked_filelists:
            if key in self.picked_filelists[parent_key]:
                self.picked_filelists[parent_key].pop(key)
                pathlabel.configure(text="picked: 0")

    def validate_config(self):
        """ Validate the configuration """
        print("\n\tvalidate_config placeholder\n")

    def save_config(self):
        """ Save the configuration to a yaml file """
        print("\n\tsave_config placeholder\n")

    def go_to_submission(self):
        """ Go to the submission page """
        print("\n\tgo_to_submission placeholder\n")

    def initialize(self):
        """Called whenever controller renders the page"""
        form_path = self.controller.config_items["form_path"]
        self.load_form(form_path)
        self.render_form()
        
        print("\n\n LE FORM DATA")
        for a,b in self.form_data.items():
            if isinstance(b, dict):
                for c,d in b.items():
                    if isinstance(d, dict):
                        for e,f in d.items():
                            if isinstance(f, dict):
                                for g,h in f.items():
                                    if isinstance(h, dict):
                                        for i,j in h.items():
                                            print(a,c,e,g,i,j)
                                    else:
                                        print(a,c,e,g,h)
                            else:
                                print(a,c,e,f)
                    else:
                        print(a,c,d)
            else:
                print(a,b)
        print("\n\n")
                

