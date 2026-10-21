"""
Nuitkalicious - A GUI for Nuitka Python Compiler
Author: asteng88 - Andrew Thomas
Version: 1.5.0
Description: GUI application to simplify the use of Nuitka compiler for Python with first-class uv support
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# Windows taskbar icon support
try:
    from ctypes import windll

    my_appid = "com.asteng88.nuitkalicious.nuitkalicious.1.5.0"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)
except (ImportError, AttributeError, OSError):
    pass


def is_compiled() -> bool:
    """Return True if running inside a compiled Nuitka or frozen executable."""
    return (
        "__compiled__" in globals()
        or getattr(sys, "frozen", False)
        or hasattr(sys, "_MEIPASS")
    )


def get_resource_path(relative_path: str = "") -> str:
    """Get absolute path to resource, works for dev and for compiled exe.

    Handles Nuitka (onefile and standalone), PyInstaller, and development environments.
    """
    candidates = []

    # PyInstaller onefile extraction directory
    if hasattr(sys, "_MEIPASS"):
        candidates.append(sys._MEIPASS)

    # Nuitka module directory (in onefile mode this is the extracted payload dir;
    # in standalone mode this is the .dist folder; in dev mode this is the script dir)
    try:
        candidates.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass

    # Nuitka __compiled__.containing_dir if available
    if "__compiled__" in globals():
        containing_dir = getattr(globals()["__compiled__"], "containing_dir", None)
        if containing_dir:
            candidates.append(containing_dir)

    # Executable directory
    if sys.executable:
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))

    # Current working directory as last fallback
    candidates.append(os.getcwd())

    # Deduplicate while preserving order
    unique_candidates = []
    for path in candidates:
        if path and path not in unique_candidates:
            unique_candidates.append(path)

    if relative_path:
        for base in unique_candidates:
            candidate = os.path.join(base, relative_path)
            if os.path.exists(candidate):
                return candidate
        return os.path.join(unique_candidates[0], relative_path)

    return unique_candidates[0]


class Nuitkalicious:
    """Main application class for Nuitkalicious."""

    REQUIRED_PACKAGES = ("nuitka", "ordered-set", "zstandard", "imageio", "psutil")

    def __init__(self, root: tk.Tk):
        """Initialize the application."""
        self._init_variables()
        self._setup_main_window(root)
        self._setup_ui()

    def _init_variables(self):
        """Initialize all instance variables."""
        self.uninstall_button = None
        self.repair_venv_button = None
        self.resource_files = []  # List of file/folder paths
        self.exe_folder = None
        self.icon_path = None
        self.venv_active = False
        self.compile_process = None

    def _setup_main_window(self, root: tk.Tk):
        """Setup the main application window."""
        self.root = root
        self.root.title("Nuitkalicious - Nuitka GUI (uv Edition) - Version 1.5.0")
        self.root.geometry("740x740")
        self.root.minsize(680, 680)
        self._setup_app_icon()

    def _setup_app_icon(self):
        """Setup application icon - works for both development and compiled exe."""
        icon_path = get_resource_path("nuitkalicious.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                return
            except tk.TclError as e:
                print(f"Could not load icon: {icon_path} - {e}")

        png_path = get_resource_path("nuitkalicious.png")
        if os.path.exists(png_path):
            try:
                icon_img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, icon_img)
                self._icon_img_ref = icon_img
            except tk.TclError:
                pass

    def _setup_ui(self):
        """Setup the main UI components."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)

        # Basic options tab
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="Basic Options")
        self.setup_basic_options()
        self.setup_output_panel(self.basic_frame)

        # Advanced options tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text="Advanced Options")
        self.setup_advanced_options()

    # =========================================================================
    # Group 1: UI Setup Methods
    # =========================================================================
    def setup_basic_options(self):
        # Initialize Tkinter variables once
        self.standalone_var = tk.BooleanVar(value=False)
        self.onefile_var = tk.BooleanVar(value=False)
        self.remove_output_var = tk.BooleanVar(value=False)
        self.no_console_var = tk.BooleanVar(value=False)
        self.follow_imports_var = tk.BooleanVar(value=False)
        self.lto_var = tk.BooleanVar(value=False)
        self.tkinter_var = tk.BooleanVar(value=False)
        self.pyqt6_var = tk.BooleanVar(value=False)
        self.use_venv_var = tk.BooleanVar(value=False)

        # File selection
        file_frame = ttk.LabelFrame(self.basic_frame, text="Python File", padding=5)
        file_frame.pack(fill="x", padx=5, pady=5)

        self.script_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.script_path).pack(
            side="left", expand=True, fill="x", padx=5
        )
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(
            side="right"
        )

        # Common options with three columns
        options_frame = ttk.LabelFrame(self.basic_frame, text="Options", padding=5)
        options_frame.pack(fill="x", padx=5, pady=5)

        left_column = ttk.Frame(options_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=5)
        middle_column = ttk.Frame(options_frame)
        middle_column.pack(side="left", fill="both", expand=True, padx=5)
        right_column = ttk.Frame(options_frame)
        right_column.pack(side="left", fill="both", expand=True, padx=5)

        # Left column - Basic options
        self.standalone_checkbox = ttk.Checkbutton(
            left_column,
            text="Standalone",
            variable=self.standalone_var,
            command=self.handle_standalone_change,
        )
        self.standalone_checkbox.pack(anchor="w")

        self.onefile_checkbox = ttk.Checkbutton(
            left_column,
            text="One File",
            variable=self.onefile_var,
            command=self.handle_onefile_change,
        )
        self.onefile_checkbox.pack(anchor="w")

        ttk.Checkbutton(
            left_column, text="Remove Output", variable=self.remove_output_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            left_column, text="No Console", variable=self.no_console_var
        ).pack(anchor="w")

        # Middle column - Basic options
        self.follow_imports_checkbox = ttk.Checkbutton(
            middle_column, text="Follow Imports", variable=self.follow_imports_var
        )
        self.follow_imports_checkbox.pack(anchor="w")

        ttk.Checkbutton(
            middle_column, text="LTO (Link Time Optimization)", variable=self.lto_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            middle_column, text="Enable Tkinter Support", variable=self.tkinter_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            middle_column, text="Enable PyQt6 Support", variable=self.pyqt6_var
        ).pack(anchor="w")

        # Right column - Jobs control
        jobs_frame = ttk.Frame(right_column)
        jobs_frame.pack(fill="x", pady=5)
        ttk.Label(jobs_frame, text="Jobs:").pack(side="left")
        default_jobs = str(os.cpu_count() or 4)
        self.jobs_var = tk.StringVar(value=default_jobs)
        ttk.Spinbox(
            jobs_frame, from_=1, to=32, textvariable=self.jobs_var, width=5
        ).pack(side="left", padx=5)

        # Virtual environment option
        venv_frame = ttk.LabelFrame(
            self.basic_frame, text="Virtual Environment (uv / venv)", padding=5
        )
        venv_frame.pack(fill="x", padx=5, pady=5)

        top_venv_row = ttk.Frame(venv_frame)
        top_venv_row.pack(fill="x")

        ttk.Checkbutton(
            top_venv_row,
            text="Use venv",
            variable=self.use_venv_var,
            command=self.toggle_venv_controls,
        ).pack(side="left", anchor="w")

        bottom_venv_row = ttk.Frame(venv_frame)
        bottom_venv_row.pack(fill="x", pady=(3, 0))

        self.venv_path = tk.StringVar()
        self.venv_entry = ttk.Entry(
            bottom_venv_row, textvariable=self.venv_path, state="disabled"
        )
        self.venv_entry.pack(side="left", expand=True, fill="x", padx=5)

        venv_btn_frame = ttk.Frame(bottom_venv_row)
        venv_btn_frame.pack(side="right")

        self.venv_browse_button = ttk.Button(
            venv_btn_frame,
            text="Browse",
            command=self.browse_venv,
            state="disabled",
        )
        self.venv_browse_button.pack(side="left", padx=2)

        self.repair_venv_button = ttk.Button(
            venv_btn_frame,
            text="Create/Sync uv venv",
            command=self.create_or_sync_uv_venv,
        )
        self.repair_venv_button.pack(side="left", padx=2)

        self.uninstall_button = ttk.Button(
            venv_btn_frame,
            text="Uninstall Nuitka",
            command=self.uninstall_nuitka,
            state="disabled",
        )
        self.uninstall_button.pack(side="left", padx=2)

        # Application Icon section
        icon_frame = ttk.LabelFrame(
            self.basic_frame, text="Application Icon", padding=5
        )
        icon_frame.pack(fill="x", padx=5, pady=5)

        self.icon_label = ttk.Label(icon_frame, text="No icon selected")
        self.icon_label.pack(side="left", padx=5, fill="x", expand=True)

        ttk.Button(icon_frame, text="Clear", command=self.clear_icon).pack(
            side="right", padx=5
        )
        ttk.Button(icon_frame, text="Select Icon", command=self.select_icon).pack(
            side="right"
        )

        # Resource Files & Folders section
        resource_frame = ttk.LabelFrame(
            self.basic_frame, text="Resource Files & Folders", padding=5
        )
        resource_frame.pack(fill="x", padx=5, pady=5)

        self.resource_listbox = tk.Listbox(resource_frame, height=5)
        self.resource_listbox.pack(fill="x", padx=5, expand=True)

        res_btn_frame = ttk.Frame(resource_frame)
        res_btn_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(res_btn_frame, text="Add Files", command=self.add_resources).pack(
            side="left", padx=5
        )
        ttk.Button(
            res_btn_frame, text="Add Folder", command=self.add_resource_folder
        ).pack(side="left", padx=5)
        ttk.Button(
            res_btn_frame, text="Remove Selected", command=self.remove_resource
        ).pack(side="left", padx=5)

        # Action buttons
        action_frame = ttk.Frame(self.basic_frame)
        action_frame.pack(pady=5)

        self.compile_button = ttk.Button(
            action_frame, text="Compile", command=self.compile
        )
        self.compile_button.pack(side="left", padx=5)

        ttk.Button(
            action_frame, text="Create & Copy Command", command=self.create_command
        ).pack(side="left", padx=5)

        self.open_exe_button = ttk.Button(
            action_frame,
            text="Open Executable Folder",
            command=self.open_exe_folder,
            state="disabled",
        )
        self.open_exe_button.pack(side="left", padx=5)

        ttk.Button(action_frame, text="Clear All", command=self.clear_all).pack(
            side="left", padx=5
        )

    def setup_output_panel(self, parent):
        status_frame = ttk.LabelFrame(parent, text="Status", padding=5)
        status_frame.pack(fill="x", padx=5, pady=5)

        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(fill="x", padx=5, pady=5)

        # Keep command preview for compatibility
        self.command_preview = scrolledtext.ScrolledText(parent, height=0)

    def setup_advanced_options(self):
        canvas = tk.Canvas(self.advanced_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.advanced_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        columns_frame = ttk.Frame(scrollable_frame)
        columns_frame.pack(expand=True, fill="both", padx=5, pady=5)

        left_column = ttk.Frame(columns_frame)
        left_column.pack(side="left", fill="both", expand=True, padx=4)

        middle_column = ttk.Frame(columns_frame)
        middle_column.pack(side="left", fill="both", expand=True, padx=4)

        right_column = ttk.Frame(columns_frame)
        right_column.pack(side="left", fill="both", expand=True, padx=4)

        # Column 1: Compilation and Module Options
        compile_frame = ttk.LabelFrame(
            left_column, text="Compilation Options", padding=8
        )
        compile_frame.pack(fill="x", pady=5)

        self.compilation_vars = {
            "clang": tk.BooleanVar(value=False),
            "mingw64": tk.BooleanVar(value=False),
            "full_compat": tk.BooleanVar(value=False),
            "static_libpython": tk.BooleanVar(value=False),
        }

        for name, var in self.compilation_vars.items():
            ttk.Checkbutton(
                compile_frame, text=name.replace("_", " ").title(), variable=var
            ).pack(anchor="w", pady=1)

        module_frame = ttk.LabelFrame(left_column, text="Module Options", padding=8)
        module_frame.pack(fill="x", pady=5)

        self.module_vars = {
            "follow_stdlib": tk.BooleanVar(value=False),
            "prefer_source": tk.BooleanVar(value=False),
            "python_flag_nosite": tk.BooleanVar(value=False),
            "python_flag_no_warnings": tk.BooleanVar(value=False),
        }

        for name, var in self.module_vars.items():
            ttk.Checkbutton(
                module_frame, text=name.replace("_", " ").title(), variable=var
            ).pack(anchor="w", pady=1)

        # Column 2: Performance and Optimization Options
        perf_frame = ttk.LabelFrame(
            middle_column, text="Performance Options", padding=8
        )
        perf_frame.pack(fill="x", pady=5)

        self.perf_vars = {
            "disable_cache": tk.BooleanVar(value=False),
            "clean_cache": tk.BooleanVar(value=False),
            "low_memory": tk.BooleanVar(value=False),
            "macos_create_app_bundle": tk.BooleanVar(value=False),
        }

        for name, var in self.perf_vars.items():
            ttk.Checkbutton(
                perf_frame, text=name.replace("_", " ").title(), variable=var
            ).pack(anchor="w", pady=1)

        optim_frame = ttk.LabelFrame(
            middle_column, text="Optimization Options", padding=8
        )
        optim_frame.pack(fill="x", pady=5)

        self.optimization_level = tk.StringVar(value="2")
        ttk.Label(optim_frame, text="Optimization Level:").pack(side="left")
        ttk.Spinbox(
            optim_frame,
            from_=0,
            to=2,
            width=5,
            textvariable=self.optimization_level,
        ).pack(side="left", padx=5)

        # Column 3: Debug Options
        debug_frame = ttk.LabelFrame(right_column, text="Debug Options", padding=8)
        debug_frame.pack(fill="x", pady=5)

        self.debug_vars = {
            "debug": tk.BooleanVar(value=False),
            "unstripped": tk.BooleanVar(value=False),
            "trace_execution": tk.BooleanVar(value=False),
            "force_dll_dependency_cache_update": tk.BooleanVar(value=False),
            "show_memory": tk.BooleanVar(value=False),
            "show_progress": tk.BooleanVar(value=False),
            "verbose": tk.BooleanVar(value=False),
            "report_xml": tk.BooleanVar(value=False),
        }

        for name, var in self.debug_vars.items():
            ttk.Checkbutton(
                debug_frame, text=name.replace("_", " ").title(), variable=var
            ).pack(anchor="w", pady=1)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    # =========================================================================
    # Group 2: Event Handlers
    # =========================================================================
    def clear_all(self):
        """Reset all fields and checkboxes to their default states."""
        self.script_path.set("")
        self.venv_path.set("")
        self.jobs_var.set(str(os.cpu_count() or 4))
        self.command_preview.delete("1.0", "end")

        # Reset basic checkboxes
        self.standalone_var.set(False)
        self.onefile_var.set(False)
        self.remove_output_var.set(False)
        self.no_console_var.set(False)
        self.follow_imports_var.set(False)
        self.tkinter_var.set(False)
        self.pyqt6_var.set(False)
        self.use_venv_var.set(False)
        self.lto_var.set(False)

        # Re-enable checkboxes that may have been disabled by Onefile mode
        self.standalone_checkbox.config(state="normal")
        self.onefile_checkbox.config(state="normal")
        self.follow_imports_checkbox.config(state="normal")
        self.compile_button.config(state="normal")

        # Reset venv controls
        self.venv_entry.config(state="disabled")
        self.venv_browse_button.config(state="disabled")
        self.open_exe_button.config(state="disabled")
        self.uninstall_button.config(state="disabled")

        self.status_label.config(text="Ready")

        # Clear icon
        self.icon_path = None
        self.icon_label.config(text="No icon selected")

        # Clear resource files
        self.resource_files.clear()
        self.resource_listbox.delete(0, "end")

        # Reset exe folder
        self.exe_folder = None

        # Reset all advanced option dictionaries
        if hasattr(self, "optimization_level"):
            self.optimization_level.set("2")
        for var_dict_name in (
            "compilation_vars",
            "module_vars",
            "perf_vars",
            "debug_vars",
        ):
            var_dict = getattr(self, var_dict_name, {})
            for var in var_dict.values():
                var.set(False)

        self.venv_active = False

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=(("Python files", "*.py"), ("All files", "*.*")),
        )
        if not filename:
            return

        filename = os.path.normpath(filename)
        self.script_path.set(filename)
        script_dir = os.path.dirname(filename)
        script_stem = os.path.splitext(os.path.basename(filename))[0]

        # Auto-detect matching .ico file if no icon is selected yet
        if not self.icon_path:
            candidate_ico = os.path.join(script_dir, f"{script_stem}.ico")
            if os.path.exists(candidate_ico):
                self.icon_path = candidate_ico
                self.icon_label.config(text=os.path.basename(candidate_ico))

        # Auto-detect project virtual environment (.venv or venv) if not already set
        if not self.venv_path.get():
            for venv_name in (".venv", "venv"):
                candidate_venv = os.path.join(script_dir, venv_name)
                if os.path.isdir(candidate_venv):
                    self.use_venv_var.set(True)
                    self.venv_path.set(candidate_venv)
                    self.venv_entry.config(state="normal")
                    self.venv_browse_button.config(state="normal")
                    venv_python = self.get_venv_python()
                    is_ok, _ = self.validate_python_executable(venv_python)
                    if is_ok:
                        self.check_nuitka_installed(venv_python)
                    else:
                        self.status_label.config(
                            text=f"Detected broken {venv_name} - click 'Create/Sync uv venv' to repair"
                        )
                    break

    def toggle_venv_controls(self):
        if self.use_venv_var.get():
            self.venv_entry.config(state="normal")
            self.venv_browse_button.config(state="normal")
            if self.venv_path.get() and os.path.exists(self.venv_path.get()):
                self.check_nuitka_installed(self.get_venv_python())
            else:
                self.uninstall_button.config(state="disabled")
        else:
            self.venv_entry.config(state="disabled")
            self.venv_browse_button.config(state="disabled")
            self.uninstall_button.config(state="disabled")

    def browse_venv(self):
        venv_dir = filedialog.askdirectory(
            title="Select Virtual Environment Directory"
        )
        if not venv_dir:
            return

        venv_dir = os.path.normpath(venv_dir)
        # If the user selected a project folder containing .venv, resolve to .venv
        if not os.path.exists(
            os.path.join(venv_dir, "Scripts", "python.exe")
        ) and os.path.exists(
            os.path.join(venv_dir, ".venv", "Scripts", "python.exe")
        ):
            venv_dir = os.path.join(venv_dir, ".venv")

        self.venv_path.set(venv_dir)
        if os.path.exists(venv_dir):
            venv_python = self.get_venv_python()
            is_valid, err_msg = self.validate_python_executable(venv_python)
            if not is_valid:
                repair = messagebox.askyesno(
                    "Broken Virtual Environment",
                    f"The selected virtual environment appears to be broken or points to an uninstalled Python version:\n\n{err_msg}\n\n"
                    "Would you like to repair/recreate it now using uv?",
                )
                if repair:
                    self.create_or_sync_uv_venv(target_venv_dir=venv_dir)
                else:
                    self.compile_button.config(state="disabled")
                return

            self.compile_button.config(state="normal")
            self.check_nuitka_installed(venv_python)

    def create_or_sync_uv_venv(self, target_venv_dir: str = None):
        """Create or repair a virtual environment using uv (or python -m venv fallback)."""
        uv_path = self.find_uv()

        if not target_venv_dir:
            if self.venv_path.get():
                target_venv_dir = os.path.normpath(self.venv_path.get())
            elif self.script_path.get():
                script_dir = os.path.dirname(os.path.normpath(self.script_path.get()))
                target_venv_dir = os.path.join(script_dir, ".venv")
            else:
                chosen = filedialog.askdirectory(
                    title="Select Project Directory for New .venv"
                )
                if not chosen:
                    return
                target_venv_dir = os.path.join(os.path.normpath(chosen), ".venv")

        project_dir = (
            os.path.dirname(target_venv_dir)
            if os.path.basename(target_venv_dir) in (".venv", "venv")
            else target_venv_dir
        )

        self.status_label.config(text=f"Creating virtual environment at {target_venv_dir}...")
        self.root.update_idletasks()

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            if uv_path:
                # Create/clear the venv with uv
                res = subprocess.run(
                    [uv_path, "venv", "--clear", target_venv_dir],
                    cwd=project_dir if os.path.isdir(project_dir) else None,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                if res.returncode != 0:
                    messagebox.showerror(
                        "uv venv Error",
                        f"Failed to create virtual environment with uv:\n{res.stderr or res.stdout}",
                    )
                    self.status_label.config(text="Failed to create venv")
                    return

                # If pyproject.toml exists in project_dir and target is .venv, sync dependencies
                pyproject_file = os.path.join(project_dir, "pyproject.toml")
                if (
                    os.path.exists(pyproject_file)
                    and os.path.basename(target_venv_dir) == ".venv"
                ):
                    self.status_label.config(
                        text="Syncing project dependencies with uv sync..."
                    )
                    self.root.update_idletasks()
                    subprocess.run(
                        [uv_path, "sync"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        stdin=subprocess.DEVNULL,
                        creationflags=creationflags,
                    )
            else:
                sys_python = self.find_system_python()
                if not sys_python:
                    messagebox.showerror(
                        "Error",
                        "Neither 'uv' nor a working system Python was found to create the virtual environment.",
                    )
                    return
                res = subprocess.run(
                    [sys_python, "-m", "venv", "--clear", target_venv_dir],
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                if res.returncode != 0:
                    messagebox.showerror(
                        "venv Error",
                        f"Failed to create virtual environment:\n{res.stderr or res.stdout}",
                    )
                    return

            # Fix activate.bat inside the newly created venv so it is portable across drive letters
            self._make_activate_bat_portable(target_venv_dir)

            self.use_venv_var.set(True)
            self.venv_path.set(target_venv_dir)
            self.venv_entry.config(state="normal")
            self.venv_browse_button.config(state="normal")
            self.compile_button.config(state="normal")

            venv_python = self.get_venv_python()
            if not self.check_nuitka_installed(venv_python):
                if messagebox.askyesno(
                    "Install Nuitka",
                    "Virtual environment is ready! Would you like to install Nuitka and its dependencies into it now?",
                ):
                    self.install_nuitka(venv_python)
            else:
                self.status_label.config(text="Virtual environment ready with Nuitka!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create virtual environment: {e}")
            self.status_label.config(text="Error creating virtual environment")

    def _make_activate_bat_portable(self, venv_dir: str):
        """Ensure .venv/Scripts/activate.bat uses relative path resolution instead of hardcoded drive letters."""
        activate_bat = os.path.join(venv_dir, "Scripts", "activate.bat")
        if not os.path.exists(activate_bat):
            return
        try:
            with open(activate_bat, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("@for %%i in (") and 'set "VIRTUAL_ENV=%%~fi"' in line:
                    lines[i] = '@for %%i in ("%~dp0..") do @set "VIRTUAL_ENV=%%~fi"\n'
                    updated = True
            if updated:
                with open(activate_bat, "w", encoding="utf-8") as f:
                    f.writelines(lines)
        except OSError:
            pass

    def add_resources(self):
        files = filedialog.askopenfilenames(
            title="Select Resource Files",
            filetypes=(
                ("All files", "*.*"),
                (
                    "Image files",
                    "*.ico *.png *.jpg *.jpeg *.gif *.tiff *.bmp *.webp *.svg *.eps",
                ),
            ),
        )
        for file in files:
            norm_file = os.path.normpath(file)
            if norm_file.lower().endswith(".ico") and not self.icon_path:
                self.icon_path = norm_file
                self.icon_label.config(text=os.path.basename(norm_file))
                continue
            if norm_file not in self.resource_files:
                self.resource_files.append(norm_file)
                self.resource_listbox.insert("end", f"[File] {os.path.basename(norm_file)}")

    def add_resource_folder(self):
        folder = filedialog.askdirectory(title="Select Resource Folder to Include")
        if folder:
            norm_folder = os.path.normpath(folder)
            if norm_folder not in self.resource_files:
                self.resource_files.append(norm_folder)
                self.resource_listbox.insert(
                    "end", f"[Folder] {os.path.basename(norm_folder)}/"
                )

    def remove_resource(self):
        selection = self.resource_listbox.curselection()
        if selection:
            idx = selection[0]
            self.resource_files.pop(idx)
            self.resource_listbox.delete(idx)

    def select_icon(self):
        icon_file = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=(("Icon files", "*.ico"), ("All files", "*.*")),
        )
        if icon_file:
            self.icon_path = os.path.normpath(icon_file)
            self.icon_label.config(text=os.path.basename(self.icon_path))

    def clear_icon(self):
        self.icon_path = None
        self.icon_label.config(text="No icon selected")

    def handle_standalone_change(self):
        if not self.standalone_var.get() and self.onefile_var.get():
            self.standalone_var.set(True)
            messagebox.showinfo(
                "Info", "Standalone mode is required for onefile builds"
            )
        elif not self.standalone_var.get():
            self.onefile_checkbox.config(state="normal")

    def handle_onefile_change(self):
        if self.onefile_var.get():
            self.follow_imports_var.set(False)
            self.follow_imports_checkbox.config(state="disabled")
            self.standalone_var.set(True)
            self.standalone_checkbox.config(state="disabled")
        else:
            self.follow_imports_checkbox.config(state="normal")
            self.standalone_checkbox.config(state="normal")

    # =========================================================================
    # Group 3: Nuitka & uv Operations
    # =========================================================================
    def find_uv(self) -> str | None:
        """Locate the uv executable, even when running from a compiled standalone exe."""
        uv_bin = shutil.which("uv")
        if uv_bin and os.path.exists(uv_bin):
            return uv_bin

        candidates = [
            os.path.expanduser(r"~\.local\bin\uv.exe"),
            os.path.expanduser(r"~\.cargo\bin\uv.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"),
            os.path.expandvars(r"%APPDATA%\Python\Scripts\uv.exe"),
            os.path.expanduser("~/.local/bin/uv"),
            os.path.expanduser("~/.cargo/bin/uv"),
        ]
        # Also check any Python Scripts directories in LocalAppData
        candidates.extend(
            glob.glob(
                os.path.expandvars(
                    r"%LOCALAPPDATA%\Programs\Python\Python*\Scripts\uv.exe"
                )
            )
        )

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return candidate
        return None

    def validate_python_executable(self, python_path: str) -> tuple[bool, str]:
        """Verify that python_path exists, is not a Windows Store stub, and executes properly."""
        if not python_path:
            return False, "No Python executable path specified."

        if "WindowsApps" in python_path:
            try:
                if os.path.getsize(python_path) == 0:
                    return (
                        False,
                        f"'{python_path}' is a Windows Store alias stub, not a real Python installation.",
                    )
            except OSError:
                return False, f"Cannot access '{python_path}'."

        if not os.path.isfile(python_path):
            return False, f"Python executable not found at: {python_path}"

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            result = subprocess.run(
                [python_path, "-c", "import sys; print(sys.version.split()[0])"],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
                creationflags=creationflags,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout).strip()
                return False, err or f"Python exited with code {result.returncode}"
            return True, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def find_system_python(self) -> str | None:
        """Find a valid system or uv-managed Python interpreter."""
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        # 1. Ask uv to find a valid Python installation (works great with uv-managed Pythons!)
        uv_path = self.find_uv()
        if uv_path:
            for args in (
                [uv_path, "python", "find", "--system"],
                [uv_path, "python", "find"],
            ):
                try:
                    res = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        stdin=subprocess.DEVNULL,
                        timeout=10,
                        creationflags=creationflags,
                    )
                    if res.returncode == 0:
                        found = res.stdout.strip()
                        is_ok, _ = self.validate_python_executable(found)
                        if is_ok:
                            return found
                except Exception:
                    pass

        # 2. If running from source (not compiled), sys.executable is a known working Python
        if not is_compiled() and sys.executable:
            is_ok, _ = self.validate_python_executable(sys.executable)
            if is_ok:
                return sys.executable

        # 3. Check PATH for python / python3 (filtering out Windows Store stubs)
        for name in ("python", "python3"):
            found = shutil.which(name)
            if found:
                is_ok, _ = self.validate_python_executable(found)
                if is_ok:
                    return found

        # 4. Search uv managed python directories and standard Windows Python locations
        search_patterns = [
            os.path.expandvars(r"%APPDATA%\uv\python\cpython-*\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python*\python.exe"),
            r"C:\Python*\python.exe",
        ]
        for pattern in search_patterns:
            matches = sorted(glob.glob(pattern), reverse=True)
            for match in matches:
                is_ok, _ = self.validate_python_executable(match)
                if is_ok:
                    return match

        return None

    def get_venv_python(self) -> str:
        """Get the full path to python.exe for the selected venv or system Python."""
        if self.use_venv_var.get() and self.venv_path.get():
            venv_root = os.path.normpath(self.venv_path.get())
            candidates = [
                os.path.join(venv_root, "Scripts", "python.exe"),
                os.path.join(venv_root, ".venv", "Scripts", "python.exe"),
                os.path.join(venv_root, "venv", "Scripts", "python.exe"),
                os.path.join(venv_root, "python.exe"),
                os.path.join(venv_root, "bin", "python"),
                os.path.join(venv_root, "bin", "python3"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    return candidate
            return candidates[0]

        # If Use venv is not checked, check if the selected script's directory has a .venv
        if self.script_path.get():
            script_dir = os.path.dirname(os.path.normpath(self.script_path.get()))
            for venv_name in (".venv", "venv"):
                local_venv_py = os.path.join(
                    script_dir, venv_name, "Scripts", "python.exe"
                )
                is_ok, _ = self.validate_python_executable(local_venv_py)
                if is_ok:
                    return local_venv_py

        found_sys = self.find_system_python()
        if found_sys:
            return found_sys

        return "python"

    def check_nuitka_installed(self, python_path: str) -> bool:
        """Check if Nuitka is installed and working for the given Python interpreter."""
        is_valid, msg = self.validate_python_executable(python_path)
        if not is_valid:
            self.status_label.config(text=f"Invalid Python: {msg[:60]}")
            if self.uninstall_button:
                self.uninstall_button.config(state="disabled")
            return False

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        try:
            self.status_label.config(text="Checking if Nuitka is installed...")
            self.root.update_idletasks()

            result = subprocess.run(
                [python_path, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=15,
                creationflags=creationflags,
            )

            if result.returncode == 0:
                first_line = (
                    result.stdout.strip().splitlines()[0]
                    if result.stdout.strip()
                    else "installed"
                )
                self.status_label.config(text=f"Found Nuitka {first_line}")
                if self.use_venv_var.get() and self.uninstall_button:
                    self.uninstall_button.config(state="normal")
                return True

            self.status_label.config(text="Nuitka not found in environment")
            if self.uninstall_button:
                self.uninstall_button.config(state="disabled")
            return False

        except Exception as e:
            self.status_label.config(text=f"Error checking Nuitka: {str(e)}")
            if self.uninstall_button:
                self.uninstall_button.config(state="disabled")
            return False

    def get_installer_commands(
        self, python_path: str, action: str = "install", packages: tuple | list = ()
    ) -> list[list[str]]:
        """Build list-based package manager commands preferring uv first, then pip, then ensurepip."""
        if isinstance(packages, str):
            pkg_list = packages.split()
        else:
            pkg_list = list(packages)

        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        uv_path = self.find_uv()

        if uv_path:
            if action == "install":
                return [[uv_path, "pip", "install", "--python", python_path, *pkg_list]]
            else:
                return [
                    [uv_path, "pip", "uninstall", "--python", python_path, *pkg_list]
                ]

        has_pip = (
            subprocess.run(
                [python_path, "-m", "pip", "--version"],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
            ).returncode
            == 0
        )

        cmds = []
        if not has_pip:
            cmds.append([python_path, "-m", "ensurepip", "--upgrade"])

        if action == "install":
            cmds.append([python_path, "-m", "pip", "install", "--upgrade", "pip"])
            cmds.append([python_path, "-m", "pip", "install", "--upgrade", *pkg_list])
        else:
            cmds.append([python_path, "-m", "pip", "uninstall", "-y", *pkg_list])

        return cmds

    def install_nuitka(self, python_path: str) -> bool:
        """Install Nuitka and required support packages using uv (preferred) or pip."""
        try:
            self.status_label.config(
                text="Installing Nuitka and dependencies via uv/pip..."
            )
            self.root.update_idletasks()

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            cmds = self.get_installer_commands(
                python_path, "install", self.REQUIRED_PACKAGES
            )
            process = None

            for cmd in cmds:
                tool_name = os.path.basename(cmd[0])
                self.status_label.config(text=f"Running {tool_name} {' '.join(cmd[1:4])}...")
                self.root.update_idletasks()
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                if process.returncode != 0 and "ensurepip" not in cmd:
                    break

            if process and process.returncode == 0:
                # If target is a venv, ensure activate.bat is portable
                if self.use_venv_var.get() and self.venv_path.get():
                    self._make_activate_bat_portable(self.venv_path.get())
                self.status_label.config(text="Nuitka installed successfully!")
                if (
                    hasattr(self, "uninstall_button")
                    and self.uninstall_button
                    and self.use_venv_var.get()
                ):
                    self.uninstall_button.config(state="normal")
                messagebox.showinfo(
                    "Success", "Nuitka and its dependencies have been installed!"
                )
                return True
            else:
                stderr_out = (
                    (process.stderr or process.stdout) if process else "Unknown error"
                )
                error_msg = f"Failed to install Nuitka:\n{stderr_out}"
                self.status_label.config(text="Failed to install Nuitka")
                messagebox.showerror("Installation Error", error_msg)
                return False

        except Exception as e:
            error_msg = f"Error installing Nuitka: {str(e)}"
            self.status_label.config(text="Failed to install Nuitka")
            messagebox.showerror("Installation Error", error_msg)
            return False

    def uninstall_nuitka(self):
        """Uninstall Nuitka from the selected virtual environment."""
        if not self.venv_path.get():
            return

        if not messagebox.askyesno(
            "Confirm Uninstall",
            "Are you sure you want to uninstall Nuitka from this virtual environment?",
        ):
            return

        try:
            python_path = self.get_venv_python()
            self.status_label.config(text="Uninstalling Nuitka...")
            self.root.update_idletasks()

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            cmds = self.get_installer_commands(
                python_path, "uninstall", ("nuitka", "ordered-set", "zstandard")
            )
            process = None

            for cmd in cmds:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    text=True,
                    creationflags=creationflags,
                )

                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        self.status_label.config(
                            text=f"Uninstalling: {output.strip()[:60]}"
                        )
                        self.root.update_idletasks()

                if process.returncode != 0 and "ensurepip" not in cmd:
                    break

            if process and process.returncode == 0:
                self.status_label.config(text="Nuitka has been uninstalled")
                self.uninstall_button.config(state="disabled")
                messagebox.showinfo(
                    "Success", "Nuitka has been successfully uninstalled!"
                )
            else:
                self.status_label.config(text="Failed to uninstall Nuitka")
                messagebox.showerror("Error", "Failed to uninstall Nuitka")

        except Exception as e:
            self.status_label.config(text=f"Error uninstalling Nuitka: {str(e)}")
            messagebox.showerror("Error", f"Error uninstalling Nuitka: {str(e)}")

    # =========================================================================
    # Group 4: Command Building and Execution
    # =========================================================================
    def build_command(self) -> list[str]:
        """Build the complete Nuitka CLI command tokens."""
        cmd = []

        python_path = self.get_venv_python()
        try:
            opt_level = int(self.optimization_level.get())
        except ValueError:
            opt_level = 2

        if opt_level >= 2:
            cmd.append(f'"{python_path}" -OO -m nuitka')
        elif opt_level == 1:
            cmd.append(f'"{python_path}" -O -m nuitka')
        else:
            cmd.append(f'"{python_path}" -m nuitka')

        # Automatically accept tool downloads (e.g., Zig / MinGW64 / Dependency Walker)
        cmd.append("--assume-yes-for-downloads")

        script_path = (
            os.path.normpath(self.script_path.get()) if self.script_path.get() else ""
        )
        script_dir = os.path.dirname(script_path) if script_path else ""
        if script_dir:
            cmd.append(f'--output-dir="{script_dir}"')

        is_standalone_or_onefile = (
            self.standalone_var.get()
            or self.onefile_var.get()
            or bool(self.resource_files)
        )

        if self.onefile_var.get():
            cmd.append("--standalone")
            cmd.append("--onefile")
        elif self.standalone_var.get() or bool(self.resource_files):
            cmd.append("--standalone")

        if self.remove_output_var.get():
            cmd.append("--remove-output")
        if self.no_console_var.get():
            cmd.append("--windows-console-mode=disable")
        if self.follow_imports_var.get() and not is_standalone_or_onefile:
            cmd.append("--follow-imports")

        if self.tkinter_var.get():
            cmd.append("--enable-plugin=tk-inter")
            cmd.append("--nofollow-import-to=tkinter.test")
        if self.pyqt6_var.get():
            cmd.append("--enable-plugin=pyqt6")

        if self.lto_var.get():
            cmd.append("--lto=yes")
        if self.jobs_var.get():
            cmd.append(f"--jobs={self.jobs_var.get()}")

        # Application Icon
        if self.icon_path:
            icon_norm = os.path.normpath(self.icon_path)
            icon_basename = os.path.basename(icon_norm)
            cmd.append(f'--windows-icon-from-ico="{icon_norm}"')
            if is_standalone_or_onefile:
                cmd.append(f'--include-data-files="{icon_norm}={icon_basename}"')

        # Resource files and folders
        for res_path in self.resource_files:
            norm_res = os.path.normpath(res_path)
            # Determine relative destination inside the bundle
            target_rel = os.path.basename(norm_res)
            if script_dir:
                try:
                    rel_candidate = os.path.relpath(norm_res, script_dir)
                    if not rel_candidate.startswith("..") and rel_candidate != ".":
                        target_rel = rel_candidate
                except ValueError:
                    pass

            if os.path.isdir(norm_res):
                cmd.append(f'--include-data-dir="{norm_res}={target_rel}"')
            elif not norm_res.lower().endswith(".ico") or norm_res != self.icon_path:
                cmd.append(f'--include-data-files="{norm_res}={target_rel}"')

        # Advanced Options - Compilation
        if self.compilation_vars["clang"].get():
            cmd.append("--clang")
        if self.compilation_vars["mingw64"].get():
            cmd.append("--mingw64")
        if self.compilation_vars["full_compat"].get():
            cmd.append("--full-compat")
        if self.compilation_vars["static_libpython"].get():
            cmd.append("--static-libpython=yes")

        # Advanced Options - Modules
        if self.module_vars["follow_stdlib"].get():
            cmd.append("--follow-stdlib")
        if self.module_vars["prefer_source"].get():
            cmd.append("--prefer-source-code")
        if self.module_vars["python_flag_nosite"].get():
            cmd.append("--python-flag=no_site")
        if self.module_vars["python_flag_no_warnings"].get():
            cmd.append("--python-flag=no_warnings")

        # Advanced Options - Performance
        if self.perf_vars["disable_cache"].get():
            cmd.append("--disable-cache=all")
        if self.perf_vars["clean_cache"].get():
            cmd.append("--clean-cache=all")
        if self.perf_vars["low_memory"].get():
            cmd.append("--low-memory")
        if self.perf_vars["macos_create_app_bundle"].get():
            cmd.append("--macos-create-app-bundle")

        # Advanced Options - Debug
        if self.debug_vars["debug"].get():
            cmd.append("--debug")
        if self.debug_vars["unstripped"].get():
            cmd.append("--unstripped")
        if self.debug_vars["trace_execution"].get():
            cmd.append("--trace-execution")
        if self.debug_vars["force_dll_dependency_cache_update"].get():
            cmd.append("--force-dll-dependency-cache-update")
        if self.debug_vars["show_memory"].get():
            cmd.append("--show-memory")
        if self.debug_vars["show_progress"].get():
            cmd.append("--show-progress")
        if self.debug_vars["verbose"].get():
            cmd.append("--verbose")
        if self.debug_vars["report_xml"].get():
            cmd.append("--report=compilation-report.xml")

        # Never compile Nuitka itself into the target application
        cmd.append("--nofollow-import-to=nuitka")

        if script_path:
            cmd.append(f'"{script_path}"')

        return cmd

    def compile(self):
        """Validate environment, ensure Nuitka is installed via uv/pip, and run compilation."""
        if not self.script_path.get():
            messagebox.showwarning(
                "Script Required", "Please select a Python script to compile."
            )
            return

        script_path = os.path.normpath(self.script_path.get())
        if not os.path.isfile(script_path):
            messagebox.showerror(
                "File Not Found", f"Selected script does not exist:\n{script_path}"
            )
            return

        if self.use_venv_var.get():
            if not self.venv_path.get() or not os.path.exists(self.venv_path.get()):
                messagebox.showwarning(
                    "Virtual Environment Required",
                    "Please select a valid virtual environment directory or click 'Create/Sync uv venv'.",
                )
                return

        python_path = self.get_venv_python()
        is_valid_py, err_msg = self.validate_python_executable(python_path)
        if not is_valid_py:
            if self.use_venv_var.get():
                repair = messagebox.askyesno(
                    "Broken Virtual Environment",
                    f"The selected virtual environment appears to be broken:\n\n{err_msg}\n\n"
                    "Would you like to recreate/repair it now using uv?",
                )
                if repair:
                    self.create_or_sync_uv_venv(target_venv_dir=self.venv_path.get())
                    python_path = self.get_venv_python()
                    is_valid_py, err_msg = self.validate_python_executable(python_path)
                if not is_valid_py:
                    return
            else:
                messagebox.showerror(
                    "Python Not Found",
                    f"Could not find a working Python interpreter:\n{err_msg}\n\n"
                    "Tip: Click 'Create/Sync uv venv' to create a uv virtual environment for your script.",
                )
                return

        # Ensure Nuitka is installed in the target Python environment
        if not self.check_nuitka_installed(python_path):
            if self.use_venv_var.get():
                if not messagebox.askyesno(
                    "Nuitka Not Found",
                    "Nuitka is not installed in the selected virtual environment.\n\n"
                    "Would you like to install Nuitka and its dependencies now using uv?",
                ):
                    self.status_label.config(
                        text="Compilation cancelled - Nuitka not installed"
                    )
                    return
                if not self.install_nuitka(python_path):
                    return
            else:
                result = messagebox.askyesnocancel(
                    "Nuitka Not Found",
                    "Nuitka is not installed in the target Python environment.\n\n"
                    "• Yes - Create a uv virtual environment (.venv) and install Nuitka (Recommended)\n"
                    "• No - Install Nuitka directly into the current Python environment\n"
                    "• Cancel - Abort compilation",
                )
                if result is None:
                    self.status_label.config(text="Compilation cancelled")
                    return
                elif result:
                    script_dir = os.path.dirname(script_path)
                    target_venv = os.path.join(script_dir, ".venv")
                    self.create_or_sync_uv_venv(target_venv_dir=target_venv)
                    python_path = self.get_venv_python()
                    if not self.check_nuitka_installed(python_path):
                        if not self.install_nuitka(python_path):
                            return
                else:
                    if not self.install_nuitka(python_path):
                        return

        # Reset button state
        self.open_exe_button.config(state="disabled")
        self.status_label.config(text="Starting compilation...")
        self.root.update_idletasks()

        script_dir = os.path.dirname(script_path)
        script_stem = os.path.splitext(os.path.basename(script_path))[0]
        self.exe_folder = script_dir

        temp_dir = tempfile.gettempdir()
        status_file = os.path.join(temp_dir, "nuitka_status.txt")
        if os.path.exists(status_file):
            try:
                os.remove(status_file)
            except OSError:
                pass

        cmd = self.build_command()
        command = " ".join(cmd)
        uv_path = self.find_uv()

        try:
            if os.name == "nt":
                batch_file = os.path.join(temp_dir, "nuitka_compile.bat")
                with open(batch_file, "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("setlocal EnableDelayedExpansion\n")
                    f.write("echo Nuitkalicious Compiler (uv Edition)\n")
                    f.write("echo ===================================\n\n")

                    # Ensure uv directory is on PATH if uv was found
                    if uv_path:
                        uv_dir = os.path.dirname(uv_path)
                        f.write(f'set "PATH={uv_dir};%PATH%"\n')

                    # Configure virtual environment variables directly without relying on stale activate.bat paths
                    if self.use_venv_var.get() and self.venv_path.get():
                        venv_root = os.path.normpath(self.venv_path.get())
                        self._make_activate_bat_portable(venv_root)
                        f.write(f'set "VIRTUAL_ENV={venv_root}"\n')
                        f.write(f'set "PATH={venv_root}\\Scripts;%PATH%"\n')
                        f.write('set "PYTHONHOME="\n')

                    f.write(f'echo Using Python: "{python_path}"\n')
                    f.write(
                        f'"{python_path}" -c "import sys; print(\'Python \' + sys.version.split()[0] + \' ready\')"\n'
                    )
                    f.write("if !ERRORLEVEL! NEQ 0 (\n")
                    f.write("    echo Python execution check failed!\n")
                    f.write(f'    echo FAILED > "{status_file}"\n')
                    f.write("    pause\n")
                    f.write("    exit /b 1\n")
                    f.write(")\n\n")

                    # Verify Nuitka and essential packages are importable
                    f.write("echo Verifying Nuitka installation...\n")
                    f.write(f'"{python_path}" -m nuitka --version >nul 2>&1\n')
                    f.write("if !ERRORLEVEL! NEQ 0 (\n")
                    f.write(
                        "    echo Nuitka missing or needs repair. Installing with uv/pip...\n"
                    )
                    if uv_path:
                        f.write(
                            f'    "{uv_path}" pip install --python "{python_path}" {" ".join(self.REQUIRED_PACKAGES)}\n'
                        )
                    else:
                        f.write(f'    "{python_path}" -m ensurepip --upgrade >nul 2>&1\n')
                        f.write(
                            f'    "{python_path}" -m pip install --upgrade {" ".join(self.REQUIRED_PACKAGES)}\n'
                        )
                    f.write("    if !ERRORLEVEL! NEQ 0 (\n")
                    f.write("        echo Failed to install Nuitka!\n")
                    f.write(f'        echo FAILED > "{status_file}"\n')
                    f.write("        pause\n")
                    f.write("        exit /b 1\n")
                    f.write("    )\n")
                    f.write(")\n\n")

                    f.write("echo.\n")
                    f.write("echo Running Nuitka compilation...\n")
                    f.write(f'cd /d "{script_dir}"\n')
                    f.write(f"{command}\n")
                    f.write('set "NUITKA_EXIT=!ERRORLEVEL!"\n\n')

                    # Only clean intermediate build folders if Remove Output is checked
                    if self.remove_output_var.get():
                        f.write("echo Cleaning intermediate build folders...\n")
                        f.write(
                            'for /d %%d in ("*.build") do if exist "%%d" rmdir /s /q "%%d"\n'
                        )
                        f.write(
                            'for /d %%d in ("*.onefile-build") do if exist "%%d" rmdir /s /q "%%d"\n'
                        )

                    f.write("if !NUITKA_EXIT! EQU 0 (\n")
                    f.write("    echo.\n")
                    f.write("    echo Compilation successful!\n")
                    f.write(f'    echo SUCCESS > "{status_file}"\n')
                    f.write("    timeout /t 2 >nul\n")
                    f.write("    exit /b 0\n")
                    f.write(") else (\n")
                    f.write("    echo.\n")
                    f.write(
                        "    echo Compilation failed with exit code !NUITKA_EXIT!!\n"
                    )
                    f.write(f'    echo FAILED > "{status_file}"\n')
                    f.write("    pause\n")
                    f.write("    exit /b !NUITKA_EXIT!\n")
                    f.write(")\n")

                # Spawn a dedicated console window for the compilation batch script
                self.compile_process = subprocess.Popen(
                    ["cmd.exe", "/c", batch_file],
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )

                self.monitor_compilation(status_file, script_dir, script_stem)

            else:
                # Unix-like systems
                full_command = f'cd "{script_dir}" && {command}'
                terminal_cmd = (
                    f"{full_command}; "
                    f'if [ $? -eq 0 ]; then echo SUCCESS > "{status_file}"; echo "Compilation successful!"; sleep 2; '
                    f'else echo FAILED > "{status_file}"; echo "Compilation failed!"; read -p "Press Enter to continue..."; fi'
                )
                self.compile_process = subprocess.Popen(
                    ["gnome-terminal", "--", "bash", "-c", terminal_cmd]
                )
                self.monitor_compilation(status_file, script_dir, script_stem)

        except Exception as e:
            messagebox.showerror(
                "Compilation Error", f"Error starting compilation: {str(e)}"
            )
            self.status_label.config(text="Compilation failed to start")

    def cleanup_build_artifacts(self):
        """Clean up intermediate build folders if Remove Output was requested."""
        if not self.exe_folder or not self.remove_output_var.get():
            return True
        try:
            for pattern in ("*.build", "*.onefile-build", "__pycache__"):
                target_pattern = os.path.join(self.exe_folder, pattern)
                for path in glob.glob(target_pattern):
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception:
            return False

    # =========================================================================
    # Group 5: Utility Methods
    # =========================================================================
    def run_in_venv(self, command: str) -> str:
        """Run a command in the context of the selected venv or system Python."""
        python_path = self.get_venv_python()
        return f'"{python_path}" {command}'

    def create_command(self):
        """Create and copy the Nuitka command to clipboard."""
        if not self.script_path.get():
            messagebox.showwarning(
                "Script Required", "Please select a Python script first."
            )
            return

        try:
            cmd = self.build_command()
            command = " ".join(cmd)

            self.root.clipboard_clear()
            self.root.clipboard_append(command)

            preview = f"Command copied to clipboard:\n\n{command}"
            messagebox.showinfo("Command Created", preview)
            self.status_label.config(text="Command created and copied to clipboard")

        except Exception as e:
            error_msg = f"Error creating command: {str(e)}"
            self.status_label.config(text="Failed to create command")
            messagebox.showerror("Error", error_msg)

    def open_exe_folder(self):
        """Open the folder containing the compiled executable."""
        if not self.exe_folder or not os.path.exists(self.exe_folder):
            messagebox.showwarning("Error", "Executable folder not found.")
            return

        target_folder = self.exe_folder
        # If compiled as Standalone (and not Onefile), open the .dist directory if it exists
        if (
            self.standalone_var.get()
            and not self.onefile_var.get()
            and self.script_path.get()
        ):
            script_stem = os.path.splitext(
                os.path.basename(self.script_path.get())
            )[0]
            dist_candidate = os.path.join(self.exe_folder, f"{script_stem}.dist")
            if os.path.isdir(dist_candidate):
                target_folder = dist_candidate

        try:
            if os.name == "nt":
                os.startfile(target_folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", target_folder])
            else:
                subprocess.run(["xdg-open", target_folder])

            self.status_label.config(text=f"Opened: {target_folder}")

        except Exception as e:
            error_msg = f"Error opening folder: {str(e)}"
            self.status_label.config(text="Failed to open folder")
            messagebox.showerror("Error", error_msg)

    def monitor_compilation(
        self, status_file: str, script_dir: str, script_stem: str
    ):
        """Monitor the compilation status file and subprocess state."""

        def check_status():
            if os.path.exists(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        status = f.read().strip()

                    if status == "SUCCESS":
                        try:
                            os.remove(status_file)
                        except OSError:
                            pass
                        self.cleanup_build_artifacts()
                        dist_dir = os.path.join(script_dir, f"{script_stem}.dist")
                        if (
                            self.standalone_var.get()
                            and not self.onefile_var.get()
                            and os.path.isdir(dist_dir)
                        ):
                            self.status_label.config(
                                text=f"Compilation successful! Output in {script_stem}.dist"
                            )
                        else:
                            self.status_label.config(text="Compilation successful!")
                        self.open_exe_button.config(state="normal")
                        return

                    elif status == "FAILED":
                        try:
                            os.remove(status_file)
                        except OSError:
                            pass
                        self.status_label.config(text="Compilation failed!")
                        self.open_exe_button.config(state="disabled")
                        return

                except Exception as e:
                    self.status_label.config(
                        text=f"Error monitoring compilation: {str(e)}"
                    )
                    return

            # Check if the console process exited without writing status (e.g. user closed the window)
            if self.compile_process is not None and self.compile_process.poll() is not None:
                if not os.path.exists(status_file):
                    self.status_label.config(
                        text="Compilation window closed before completion"
                    )
                    return

            self.root.after(1000, check_status)

        self.root.after(1000, check_status)


def main():
    root = tk.Tk()
    Nuitkalicious(root)
    root.mainloop()


if __name__ == "__main__":
    main()
