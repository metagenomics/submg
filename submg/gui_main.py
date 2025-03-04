import sys

try:
    import tkinter
except ImportError as e:

    print("ERROR:\ttkinter is not installed on your system.")
    print("\tsubMG requires 'tkinter' to in graphical user interface (GUI) mode.")
    if sys.platform.startswith("linux"):
        print("\nYou can install tkinter using one of the following commands:")
        print("  Ubuntu/Debian: sudo apt install python3-tk")
        print("  Fedora/CentOS: sudo dnf install python3-tkinter")
        print("  Arch Linux: sudo pacman -S tk")
    elif sys.platform == "darwin":
        print("\nPlease install tkinter to use the GUI.")
    elif sys.platform.startswith("win"):
        print("\nOn Windows, 'tkinter' is included by default with the Python installer.")
        print("Ensure you have the official Python installed from https://www.python.org/downloads/.")
    else:
        print("\nPlease refer to your operating system's documentation for installing 'tkinter'.")
    print("Error message: ", e)
    sys.exit(1)

from submg.gui import controller



def main():
    controller.main()


if __name__ == "__main__":
    main()

