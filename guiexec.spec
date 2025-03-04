# -*- mode: python ; coding: utf-8 -*-+

# Resources to include in the build
resources = [
    ('submg/resources/gui_flow.png', 'submg/resources'),
    ('submg/resources/gui_logo.png', 'submg/resources'),
    ('submg/resources/logo_dark.png', 'submg/resources'),
    ('submg/resources/logo_light.png', 'submg/resources'),
    ('submg/resources/nfdi4microbiota_dark.png', 'submg/resources'),
    ('submg/resources/nfdi4microbiota_light.png', 'submg/resources'),
    ('submg/resources/steps_dark.png', 'submg/resources'),
    ('submg/resources/steps_light.png', 'submg/resources'),
    ('submg/resources/submission_modes_dark.png', 'submg/resources'),
    ('submg/resources/submission_modes_light.png', 'submg/resources'),
]

# Combine all collected data
all_datas = resources

# Path to the GUI main script
main_script = 'submg/gui_main.py'

# Analysis step
a = Analysis(
    [main_script],
    pathex=['.'],  # Current working directory
    binaries=[],  # No extra binaries
    datas=all_datas,  # Include resources
    hiddenimports=[
        'yaml',
        'requests',
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'yaspin',
        'tqdm',
        'tqdm.std',
        'tqdm.asyncio',
    ],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=True,  # Ensure unpacked resources
)

# Create the PyInstaller archive step
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the single-file executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Avoid standalone UPX packing
    name='submg-gui',
    debug=False,
    bootloader_ignore_signals=False,
    console=False,  # No console window
    icon=None,  # Add your .ico file here if you have one
    onefile=True,  # Generate a single executable
)
