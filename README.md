# Nuitkalicious (New-it-ka-lish-us) — v1.5.0 (uv Edition)

**Nuitkalicious** is a GUI front-end for the **Nuitka** Python compiler with first-class **uv** integration, making standalone and single-file Python compilation fast and reliable without manual CLI flag wrangling.

## Quick Start with `uv`

```powershell
uv sync
uv run nuitkalicious.py
```

## Key Features

### Basic Options Tab
- **Standalone (`--standalone`)**: Compiles your script and all required dependencies into a self-contained `<script>.dist` folder.
- **One File (`--onefile`)**: Packages the standalone build into a single `.exe` executable.
- **Remove Output (`--remove-output`)**: Cleans up intermediate `.build` / `.onefile-build` folders after compilation while preserving your `.dist` folder or `.exe`.
- **No Console (`--windows-console-mode=disable`)**: Hides the terminal window for GUI applications.
- **Follow Imports (`--follow-imports`)**: Follows imported Python modules in accelerated mode.
- **LTO (`--lto=yes`)**: Enables Link Time Optimization for smaller, faster binaries.
- **Enable Tkinter Support (`--enable-plugin=tk-inter`)**: Uses Nuitka's native `tk-inter` plugin to bundle Tcl/Tk from the target Python environment.
- **Enable PyQt6 Support (`--enable-plugin=pyqt6`)**: Enables Nuitka's PyQt6 plugin.
- **First-Class `uv` & Virtual Environment Support**:
  - Automatically detects `.venv` or `venv` in your selected script's directory.
  - **Create/Sync uv venv**: One-click creation or repair of `.venv` using `uv venv` (and `uv sync` when `pyproject.toml` is present).
  - Automatically installs/repairs `nuitka`, `ordered-set`, `zstandard`, `imageio`, and `psutil` using `uv pip install` (with automatic fallback to `pip` / `ensurepip`).
  - Portable virtual environment handling that works even if `.venv` folders are moved across drives.
- **Application Icon**:
  - Automatically detects `<script_name>.ico` in the script folder if present, or uses the first `.ico` file added.
  - Sets both the Windows executable icon (`--windows-icon-from-ico`) and bundles the `.ico` as a runtime data file (`--include-data-files`).
- **Resource Files & Folders**:
  - **Add Files**: Bundles individual files via `--include-data-files`, preserving relative paths inside the project folder.
  - **Add Folder**: Bundles entire asset directories via `--include-data-dir`.
- **Create & Copy Command**: Copies the exact Nuitka command (including all Basic and Advanced flags) to your clipboard.
- **Open Executable Folder**: Opens the compiled `.dist` directory (for Standalone builds) or script output directory (for Onefile builds) in Explorer.
