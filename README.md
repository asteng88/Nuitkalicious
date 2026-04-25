# Nuitkalicious (New-it-ka-lish-us)

**Nuitkalicious** is a front end for **nuitka** to make compiling programs easier rather than using the command line.
It has the following utilities included:
## Basic Tab
- `Standalone` (Standalone folder)
- `Onefile` (Single .exe file)
- `Follow Imports` (Follows the library imports and includes them in the compilation)
- `Remove Output` (Removes all the build and onefile directories when compiled)
- `No console` (No terminal console that can run in the background - not normally needed for single .exe's)
- `LTO` - Link Time Optimization (Faster loading .exe's with smaller file sizes)
- `Tkinter` library support (Python included GUI)
- `PyQt6` library support (PyQt6 GUI's)
- Windows Defender Exclusion (Unfortunately sometimes needed when compiling)
- Use the virtual environment (`.venv`) to compile the program
- Automatically installs nuitka into the chosen .venv to compile the program
- Choice to upgrade nuitka if found and the installed version is < latest release
- Icon inclusion (`.ico` files)
- If no icon is selected, it uses the first image file in the resources list
- Addition of all resource and supporting files (Add/Remove file option)
- Create & Copy Command - Copy the bare nuitka command with all the options you have selected. Can then be pasted into a command line.
- Open Executable Folder - File Explorer opens the folder where the executable is stored
- Status box for all the system messages
- Opens and monitors a terminal window to complete all the nuitka compilation. Automatically exits when the compiling is complete.
