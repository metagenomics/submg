# Creating GUI executables

subMG uses PyInstaller and `guiexec.spec` to create a single-file GUI executable. PyInstaller is not a cross-compiler, so the Linux executable must be built on Linux and the Windows executable on Windows.

The build scripts create a clean, private virtual environment under `.build-gui`, install subMG and the build dependency, run PyInstaller, and place a versioned executable plus its SHA-256 checksum in `dist`.

## Before building

1. Make sure these three version strings are identical:

   - `setup.py`: `version`
   - `submg/__init__.py`: `__version__`
   - `submg/modules/statConf.py`: `submg_version`

2. Build from the commit that will receive the release tag. Commit or consciously review all tracked changes first.
3. Test the normal source installation and the behavior changed by the release.

The build aborts if the three version strings differ.

## Ubuntu executable

Install the system prerequisites once:

```bash
sudo apt install python3 python3-tk python3-venv
```

Then, from anywhere, run:

```bash
./scripts/build_gui_ubuntu.sh
```

For broad Linux compatibility, build on the oldest Ubuntu version that the release intends to support. Linux binaries built on a newer distribution can depend on a newer glibc and fail on older distributions.

For example, version 1.1.0 produces:

```text
dist/submg-gui-linux-v1.1.0
dist/submg-gui-linux-v1.1.0.sha256
```

## Windows executable

Install 64-bit Python 3.10 or newer from python.org. The standard installer includes tkinter; enable the Python launcher (`py`) during installation.

Open Command Prompt in the repository and run:

```bat
scripts\build_gui_windows.bat
```

For example, version 1.1.0 produces:

```text
dist\submg-gui-windows-v1.1.0.exe
dist\submg-gui-windows-v1.1.0.exe.sha256
```

## Test and publish

Test each executable on its own operating system before publishing it. At minimum:

1. Start the executable and check that the home screen and images load.
2. Open or create a configuration.
3. Check Java/Webin-CLI detection and download.
4. Exercise the workflows changed in this release.
5. Optionally verify the checksum:

   - Ubuntu: `cd dist && sha256sum -c submg-gui-linux-vX.Y.Z.sha256`
   - Windows PowerShell: `Get-FileHash dist\submg-gui-windows-vX.Y.Z.exe -Algorithm SHA256`

Upload the two executables to the GitHub release for the matching `vX.Y.Z` tag. The checksum files are small and should be uploaded too.
