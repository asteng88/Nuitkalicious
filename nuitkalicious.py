"""
Nuitkalicious - A GUI for Nuitka Python Compiler
Author: asteng88 - Andrew Thomas
Version: 1.4.2
Description: GUI application to simplify the use of Nuitka compiler for Python
"""

import tkinter as tk

from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import os

# Windows taskbar icon support
try:
    from ctypes import windll
    my_appid = 'com.asteng88.nuitkalicious.nuitkalicious.1.4.2'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)
except ImportError:
    pass

class Nuitkalicious:
    # Main application class for Nuitkalicious

    def __init__(self, root):
        """Initialize the application"""
        # Initialize instance variables
        self._init_variables()
        
        # Setup main window
        self._setup_main_window(root)
        
        # Setup UI components
        self._setup_ui()

    def _init_variables(self):
        """Initialize all instance variables"""
        self.uninstall_button = None
        self.resource_files = []
        self.exe_folder = None
        self.icon_path = None
        self.venv_active = True

    def _setup_main_window(self, root):
        """Setup the main application window"""
        self.root = root
        self.root.title("Nuitkalicious - Nuitka GUI - Version 1.4.2")
        self.root.geometry("700x700")
        self._setup_app_icon()

    def _setup_app_icon(self):
        """Setup application icon"""
        base_path = os.path.dirname(__file__)
        os.chdir(base_path)
        icon_path = os.path.join(base_path, 'nuitkalicious.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                print(f"Could not load icon: {icon_path}")

    def _setup_ui(self):
        """Setup the main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Setup basic options tab
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text='Basic Options')
        self.setup_basic_options()
        self.setup_output_panel(self.basic_frame)
        
        # Setup advanced options tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text='Advanced Options')
        self.setup_advanced_options()

    # Group 1: UI Setup Methods
    def setup_basic_options(self):
        # Initialize BooleanVar variables first
        self.standalone_var = tk.BooleanVar()
        self.onefile_var = tk.BooleanVar()
        self.remove_output_var = tk.BooleanVar()
        self.no_console_var = tk.BooleanVar()
        self.follow_imports_var = tk.BooleanVar()
        self.lto_var = tk.BooleanVar()
        self.tkinter_var = tk.BooleanVar()
        self.use_venv_var = tk.BooleanVar()

        # File selection
        file_frame = ttk.LabelFrame(self.basic_frame, text="Python File", padding=5)
        file_frame.pack(fill='x', padx=5, pady=5)
        
        self.script_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.script_path).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='right')
        
        # Common options with two columns
        options_frame = ttk.LabelFrame(self.basic_frame, text="Options", padding=5)
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Create three columns
        left_column = ttk.Frame(options_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=5)
        middle_column = ttk.Frame(options_frame)
        middle_column.pack(side='left', fill='both', expand=True, padx=5)
        right_column = ttk.Frame(options_frame)
        right_column.pack(side='left', fill='both', expand=True, padx=5)
        
        # Left column - Basic options
        self.standalone_checkbox = ttk.Checkbutton(left_column, text="Standalone", 
                                                 variable=self.standalone_var, 
                                                 command=self.handle_standalone_change)
        self.standalone_checkbox.pack(anchor='w')
        
        self.onefile_checkbox = ttk.Checkbutton(left_column, text="One File", 
                                               variable=self.onefile_var, 
                                               command=self.handle_onefile_change)
        self.onefile_checkbox.pack(anchor='w')
        
        self.remove_output_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="Remove Output", variable=self.remove_output_var).pack(anchor='w')
        
        self.no_console_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="No Console", variable=self.no_console_var).pack(anchor='w')
        
        # Middle column - Basic options
        self.follow_imports_var = tk.BooleanVar()
        self.follow_imports_checkbox = ttk.Checkbutton(middle_column, text="Follow Imports", 
                                                     variable=self.follow_imports_var)
        self.follow_imports_checkbox.pack(anchor='w')
        
        self.lto_var = tk.BooleanVar()
        ttk.Checkbutton(middle_column, text="LTO (Link Time Optimization)", variable=self.lto_var).pack(anchor='w')
        
        self.tkinter_var = tk.BooleanVar()
        ttk.Checkbutton(middle_column, text="Enable Tkinter Support", variable=self.tkinter_var).pack(anchor='w')
        
        self.pyqt6_var = tk.BooleanVar()
        ttk.Checkbutton(middle_column, text="Enable PyQt6 Support", variable=self.pyqt6_var).pack(anchor='w')
        
        # Right column - Just jobs control (removed Windows Defender checkbox)
        jobs_frame = ttk.Frame(right_column)
        jobs_frame.pack(fill='x', pady=5)
        ttk.Label(jobs_frame, text="Jobs:").pack(side='left')
        self.jobs_var = tk.StringVar(value="1")
        ttk.Spinbox(jobs_frame, from_=1, to=16, textvariable=self.jobs_var, width=5).pack(side='left', padx=5)
        
        # Virtual environment option
        venv_frame = ttk.LabelFrame(self.basic_frame, text="Virtual Environment (venv)", padding=5)
        venv_frame.pack(fill='x', padx=5, pady=5)
        
        self.use_venv_var = tk.BooleanVar()
        ttk.Checkbutton(venv_frame, text="Use venv", variable=self.use_venv_var, 
                        command=self.toggle_venv_controls).pack(anchor='w')
        
        self.venv_path = tk.StringVar()
        self.venv_entry = ttk.Entry(venv_frame, textvariable=self.venv_path, state='disabled')
        self.venv_entry.pack(side='left', expand=True, fill='x', padx=5)
        
        button_frame = ttk.Frame(venv_frame)
        button_frame.pack(side='right')
        
        self.venv_browse_button = ttk.Button(button_frame, text="Browse", 
                                       command=self.browse_venv, state='disabled')
        self.venv_browse_button.pack(side='left', padx=2)
        
        self.uninstall_button = ttk.Button(button_frame, text="Uninstall Nuitka", 
                                      command=self.uninstall_nuitka, state='disabled')
        self.uninstall_button.pack(side='left', padx=2)

        # Add Icon section before resource files section
        icon_frame = ttk.LabelFrame(self.basic_frame, text="Application Icon", padding=5)
        icon_frame.pack(fill='x', padx=5, pady=5)
        
        self.icon_label = ttk.Label(icon_frame, text="No icon selected")
        self.icon_label.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(icon_frame, text="Clear", command=self.clear_icon).pack(side='right', padx=5)
        ttk.Button(icon_frame, text="Select Icon", command=self.select_icon).pack(side='right')
        
        # Add Resource Files section before the compile button
        resource_frame = ttk.LabelFrame(self.basic_frame, text="Resource Files", padding=5)
        resource_frame.pack(fill='x', padx=5, pady=5)
        
        # Listbox to show selected resources
        self.resource_listbox = tk.Listbox(resource_frame, height=5)
        self.resource_listbox.pack(fill='x', padx=5, expand=True)
        
        button_frame = ttk.Frame(resource_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Files", command=self.add_resources).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_resource).pack(side='left')
        
        # Create a frame for the action buttons
        action_frame = ttk.Frame(self.basic_frame)
        action_frame.pack(pady=5)
        
        # Compile button - remove state='disabled'
        self.compile_button = ttk.Button(action_frame, text="Compile", 
                                       command=self.compile)
        self.compile_button.pack(side='left', padx=5)
        
        # Create Command button
        ttk.Button(action_frame, text="Create & Copy Command", command=self.create_command).pack(side='left', padx=5)
        
        # Open EXE folder button (disabled by default)
        self.open_exe_button = ttk.Button(action_frame, text="Open Executable Folder", 
                                        command=self.open_exe_folder, state='disabled')
        self.open_exe_button.pack(side='left', padx=5)
        
        # Add Clear All button
        ttk.Button(action_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=5)
        
    def setup_output_panel(self, parent):
        status_frame = ttk.LabelFrame(parent, text="Status", padding=5)
        status_frame.pack(fill='x', padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(fill='x', padx=5, pady=5)
        
        # Keep command preview for compatibility
        self.command_preview = scrolledtext.ScrolledText(parent, height=0)  # Hidden but keeps references working

    def setup_advanced_options(self):
        # Setup the advanced options tab
        # Create scrollable frame for advanced options
        canvas = tk.Canvas(self.advanced_frame)
        scrollbar = ttk.Scrollbar(self.advanced_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create container frame for columns
        columns_frame = ttk.Frame(scrollable_frame)
        columns_frame.pack(expand=True, fill='both')

        # Create three columns
        left_column = ttk.Frame(columns_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=2)
        
        middle_column = ttk.Frame(columns_frame)
        middle_column.pack(side='left', fill='both', expand=True, padx=2)
        
        right_column = ttk.Frame(columns_frame)
        right_column.pack(side='left', fill='both', expand=True, padx=2)

        # Create a list to store all frames for later resizing
        option_frames = []

        # Column 1: Compilation and Module Options
        compile_frame = ttk.LabelFrame(left_column, text="Compilation Options", padding=5)
        compile_frame.pack(fill='x', pady=5)
        option_frames.append(compile_frame)

        self.compilation_vars = {
            'clang': tk.BooleanVar(),
            'mingw64': tk.BooleanVar(),
            'disable_console_ctrl_handler': tk.BooleanVar(),
            'full_compat': tk.BooleanVar(),
            'static_libpython': tk.BooleanVar()
        }

        for name, var in self.compilation_vars.items():
            ttk.Checkbutton(compile_frame, text=name.replace('_', ' ').title(), 
                           variable=var).pack(anchor='w')

        module_frame = ttk.LabelFrame(left_column, text="Module Options", padding=5)
        module_frame.pack(fill='x', pady=5)
        option_frames.append(module_frame)

        self.module_vars = {
            'follow_stdlib': tk.BooleanVar(),
            'prefer_source': tk.BooleanVar(),
            'include_package_data': tk.BooleanVar(),
            'python_flag_nosite': tk.BooleanVar(),
            'remove_embedded': tk.BooleanVar()
        }

        for name, var in self.module_vars.items():
            ttk.Checkbutton(module_frame, text=name.replace('_', ' ').title(), 
                           variable=var).pack(anchor='w')

        # Column 2: Performance and Optimization Options
        perf_frame = ttk.LabelFrame(middle_column, text="Performance Options", padding=5)
        perf_frame.pack(fill='x', pady=5)
        option_frames.append(perf_frame)

        self.perf_vars = {
            'disable_ccache': tk.BooleanVar(),
            'high_memory': tk.BooleanVar(),
            'linux_onefile_icon': tk.BooleanVar(),
            'macos_create_app_bundle': tk.BooleanVar()
        }

        for name, var in self.perf_vars.items():
            ttk.Checkbutton(perf_frame, text=name.replace('_', ' '). title(), 
                           variable=var).pack(anchor='w')

        optim_frame = ttk.LabelFrame(middle_column, text="Optimization Options", padding=5)
        optim_frame.pack(fill='x', pady=5)
        option_frames.append(optim_frame)

        self.optimization_level = tk.StringVar(value="2")
        ttk.Label(optim_frame, text="Optimization Level:").pack(side='left')
        ttk.Spinbox(optim_frame, from_=0, to=3, width=5, 
                    textvariable=self.optimization_level).pack(side='left', padx=5)

        # Column 3: Debug Options
        debug_frame = ttk.LabelFrame(right_column, text="Debug Options", padding=5)
        debug_frame.pack(fill='x', pady=5)
        option_frames.append(debug_frame)

        self.debug_vars = {
            'debug': tk.BooleanVar(),
            'unstriped': tk.BooleanVar(),
            'trace_execution': tk.BooleanVar(),
            'disable_dll_depsubprocess_cache': tk.BooleanVar(),  # This was mismatched
            'experimental': tk.BooleanVar(),
            'show_memory': tk.BooleanVar(),
            'show_progress': tk.BooleanVar(),
            'verbose': tk.BooleanVar(),
        }

        for name, var in self.debug_vars.items():
            ttk.Checkbutton(debug_frame, text=name.replace('_', ' '). title(), 
                           variable=var).pack(anchor='w')

        # Wait for all frames to be drawn
        self.root.update_idletasks()

        # Find the maximum width and height among all frames
        max_width = max(frame.winfo_reqwidth() for frame in option_frames)
        max_height = max(frame.winfo_reqheight() for frame in option_frames)

        # Set all frames to the maximum size
        for frame in option_frames:
            frame.configure(width=max_width, height=max_height)
            # Prevent the frame from shrinking
            frame.pack_propagate(False)

        # Package all frames with scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    # Group 2: Event Handlers
    def clear_all(self):
        # Reset all fields and checkboxes to their default states
        # Clear text fields
        self.script_path.set("")
        self.venv_path.set("")
        self.jobs_var.set("1")
        self.command_preview.delete('1.0', 'end')
        
        # Reset checkboxes
        self.standalone_var.set(False)
        self.onefile_var.set(False)
        self.remove_output_var.set(False)
        self.no_console_var.set(False)
        self.follow_imports_var.set(False)
        self.tkinter_var.set(False)
        self.pyqt6_var.set(False)
        self.use_venv_var.set(False)
        self.lto_var.set(False)
        
        # Reset other states
        self.venv_entry.config(state='disabled')
        self.venv_browse_button.config(state='disabled')
        self.open_exe_button.config(state='disabled')
        self.uninstall_button.config(state='disabled')

        # Update to use status label instead of terminal
        self.status_label.config(text="Ready")
        
        # Clear icon
        self.icon_path = None
        self.icon_label.config(text="No icon selected")
        
        # Clear resource files
        self.resource_files.clear()
        self.resource_listbox.delete(0, 'end')
        
        # Reset exe folder
        self.exe_folder = None

        # Reset advanced options
        if hasattr(self, 'optimization_level'):
            self.optimization_level.set("2")
        if hasattr(self, 'debug_var'):
            self.debug_var.set(False)
        if hasattr(self, 'unstriped_var'):
            self.unstriped_var.set(False)
        if hasattr(self, 'debugger_var'):
            self.debugger_var.set(False)
        if hasattr(self, 'doc_var'):
            self.doc_var.set(False)
        if hasattr(self, 'follow_stdlib_var'):
            self.follow_stdlib_var.set(False)
        if hasattr(self, 'prefer_source_var'):
            self.prefer_source_var.set(False)
        
        self.venv_active = False

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filename:
            self.script_path.set(filename)
            
    def toggle_venv_controls(self):
        # Handle all venv-related control states in one place
        if self.use_venv_var.get():
            self.venv_entry.config(state='normal')
            self.venv_browse_button.config(state='normal')
            if self.venv_path.get() and os.path.exists(self.venv_path.get()):
                self.check_nuitka_installed(self.get_venv_python())
            else:
                self.uninstall_button.config(state='disabled')
        else:
            self.venv_entry.config(state='disabled')
            self.venv_browse_button.config(state='disabled')
            self.uninstall_button.config(state='disabled')
            
    def browse_venv(self):
        venv_dir = filedialog.askdirectory(title="Select Virtual Environment Directory")
        if venv_dir:
            self.venv_path.set(venv_dir)
            if os.path.exists(venv_dir):
                self.compile_button.config(state='normal')
                # Immediately check for Nuitka when selecting venv
                self.check_nuitka_installed(self.get_venv_python())
                
    def add_resources(self):
        files = filedialog.askopenfilenames(
            title="Select Resource Files",
            filetypes=(
                ("All files", "*.*"),
                ("Image files", "*.ico *.png *.jpg *.jpeg *.gif *.tiff *.bmp *.webp *.svg *.eps"),
            )
        )
        for file in files:
            if file.lower().endswith('.ico'):
                if not self.icon_path:  # If no icon is set, use the first .ico file
                    self.icon_path = file
                    self.icon_label.config(text=os.path.basename(file))
                    continue
            if file not in self.resource_files:
                self.resource_files.append(file)
                self.resource_listbox.insert('end', os.path.basename(file))
                
    def remove_resource(self):
        selection = self.resource_listbox.curselection()
        if selection:
            idx = selection[0]
            self.resource_files.pop(idx)
            self.resource_listbox.delete(idx)
            
    def select_icon(self):
        icon_file = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=(("Icon files", "*.ico"), ("All files", "*.*"))
        )
        if icon_file:
            self.icon_path = icon_file
            self.icon_label.config(text=os.path.basename(icon_file))
            
    def clear_icon(self):
        self.icon_path = None
        self.icon_label.config(text="No icon selected")

    def handle_standalone_change(self):
        # Handle standalone checkbox changes
        if not self.standalone_var.get() and self.onefile_var.get():
            # Prevent standalone from being unchecked if onefile is selected
            self.standalone_var.set(True)
            messagebox.showinfo("Info", "Standalone mode is required for onefile builds")
        elif not self.standalone_var.get():
            self.onefile_checkbox.config(state='normal')

    def handle_onefile_change(self):
        # Handle onefile checkbox changes - make mutually exclusive with standalone and manage dependencies
        if self.onefile_var.get():
            self.follow_imports_var.set(False)
            self.follow_imports_checkbox.config(state='disabled')
            # Enable standalone automatically for onefile (required)
            self.standalone_var.set(True)
            self.standalone_checkbox.config(state='disabled')
        else:
            self.follow_imports_checkbox.config(state='normal')
            self.standalone_checkbox.config(state='normal')
            # Don't automatically unset standalone when disabling onefile
            # as user might want standalone without onefile

    # Group 3: Nuitka Operations
    def check_nuitka_installed(self, python_path):
        # Check if Nuitka is installed in the virtual environment
        try:
            # First try pip list approach
            cmd = f'"{python_path}" -m pip list'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if 'nuitka' in result.stdout.lower():
                # Extract version from pip list output
                for line in result.stdout.split('\n'):
                    if 'nuitka' in line.lower():
                        version = line.split()[1]
                        self.status_label.config(text=f"Found Nuitka {version}")
                        self.uninstall_button.config(state='normal')
                        return True
            
            # Fallback to direct module import check
            result = subprocess.run(
                [python_path, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.status_label.config(text=f"Found Nuitka {version}")
                self.uninstall_button.config(state='normal')
                return True
            
            self.status_label.config(text="Nuitka not found in environment")
            self.uninstall_button.config(state='disabled')
            return False
            
        except Exception as e:
            self.status_label.config(text=f"Error checking Nuitka: {str(e)}")
            self.uninstall_button.config(state='disabled')
            return False

    def install_nuitka(self, python_path):
        # Install Nuitka in the virtual environment
        try:
            # Update status and force GUI refresh
            self.status_label.config(text="Installing Nuitka... Please wait while it is being installed.")
            self.root.update_idletasks()  # Force GUI update
            
            cmd = f'"{python_path}" -m pip install nuitka'
            process = subprocess.run(
                cmd, 
                shell=True,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                self.status_label.config(text="Nuitka installed successfully!")
                if hasattr(self, 'uninstall_button') and self.uninstall_button:
                    self.uninstall_button.config(state='normal')
                messagebox.showinfo("Success", "Nuitka has been successfully installed!")
                return True
            else:
                error_msg = f"Failed to install Nuitka:\n{process.stderr}"
                self.status_label.config(text="Failed to install Nuitka")
                messagebox.showerror("Installation Error", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error installing Nuitka: {str(e)}"
            self.status_label.config(text="Failed to install Nuitka")
            messagebox.showerror("Installation Error", error_msg)
            return False

    def uninstall_nuitka(self):
        # Uninstall Nuitka from the virtual environment
        if not self.venv_path.get():
            return
            
        if not messagebox.askyesno("Confirm Uninstall", 
                                  "Are you sure you want to uninstall Nuitka from this virtual environment?"):
            return
            
        try:
            python_path = self.get_venv_python()
            self.status_label.config(text="Uninstalling Nuitka...")
            
            cmd = f'"{python_path}" -m pip uninstall nuitka -y'
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Monitor the uninstallation progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.status_label.config(text=f"Uninstalling...\n{output.strip()}")
                    self.root.update()
            
            if process.returncode == 0:
                self.status_label.config(text="Nuitka has been uninstalled")
                self.uninstall_button.config(state='disabled')
                messagebox.showinfo("Success", "Nuitka has been successfully uninstalled!")
            else:
                self.status_label.config(text="Failed to uninstall Nuitka")
                messagebox.showerror("Error", "Failed to uninstall Nuitka")
                
        except Exception as e:
            self.status_label.config(text=f"Error uninstalling Nuitka: {str(e)}")
            messagebox.showerror("Error", f"Error uninstalling Nuitka: {str(e)}")

    # Group 4: Command Building and Execution

    def get_tcl_tk_paths(self):
        """Get correct Tcl/Tk paths and version info"""
        
        tcl_lib = os.path.join(os.path.dirname(os.path.dirname(tk.__file__)), 'tcl')
        tk_lib = os.path.join(os.path.dirname(os.path.dirname(tk.__file__)), 'tk')
        
        # Find exact Tcl version
        tcl_version = tk.Tcl().eval('info patchlevel')
        return tcl_lib, tk_lib, tcl_version

    def build_command(self):
        cmd = []
        
        # Use venv Python if selected, otherwise system Python
        if self.use_venv_var.get() and self.venv_path.get():
            venv_python = self.get_venv_python()
            # Add optimization level directly to python command
            opt_level = int(self.optimization_level.get())
            if opt_level >= 2:
                cmd.append(f'"{venv_python}" -OO -m nuitka')
            elif opt_level == 1:
                cmd.append(f'"{venv_python}" -O -m nuitka')
            else:
                cmd.append(f'"{venv_python}" -m nuitka')
        else:
            # Use system Python when no venv is selected
            opt_level = int(self.optimization_level.get())
            if opt_level >= 2:
                cmd.append('python -OO -m nuitka')
            elif opt_level == 1:
                cmd.append('python -O -m nuitka')
            else:
                cmd.append('python -m nuitka')

        # Add automatic yes for downloads
        cmd.append('--assume-yes-for-downloads')

        # Get the directory of the selected Python script
        script_path = self.script_path.get()
        if script_path:
            script_dir = os.path.dirname(script_path)
            # Set output directory and working directory
            cmd.append(f'--output-dir="{script_dir}"')

        # Add all the options
        if self.onefile_var.get():
            # For onefile, we need both flags
            cmd.append('--standalone')
            cmd.append('--onefile')
        elif self.standalone_var.get():
            cmd.append('--standalone')
        if self.remove_output_var.get():
            cmd.append('--remove-output')
        if self.no_console_var.get():
            # Updated console option for newer Nuitka versions
            cmd.append('--windows-console-mode=disable')
        if self.follow_imports_var.get():
            cmd.append('--follow-imports')
        if self.tkinter_var.get():
            cmd.append('--enable-plugin=tk-inter')
        if self.pyqt6_var.get():
            cmd.append('--enable-plugin=pyqt6')
        if self.lto_var.get():  # Updated LTO option to include value
            cmd.append('--lto=yes')
        if self.jobs_var.get():
            cmd.append(f'--jobs={self.jobs_var.get()}')
            
        # Add icon both as Windows icon and as a data file
        if self.icon_path:
            icon_basename = os.path.basename(self.icon_path)
            cmd.append(f'--windows-icon-from-ico="{self.icon_path}"')
            cmd.append(f'--include-data-files="{self.icon_path}"="{icon_basename}"')
            
        # Add resource files to command with proper quoting
        for res_file in self.resource_files:
            target_path = os.path.basename(res_file)
            if not res_file.lower().endswith('.ico'):  # Skip .ico files as they're handled above
                cmd.append(f'--include-data-file="{res_file}"="{target_path}"')

        # Add advanced options
        # Compilation options
        if self.compilation_vars['clang'].get():
            cmd.append('--clang')
        if self.compilation_vars['mingw64'].get():
            cmd.append('--mingw64')
        if self.compilation_vars['disable_console_ctrl_handler'].get():
            cmd.append('--disable-console-ctrl-handler')
        if self.compilation_vars['full_compat'].get():
            cmd.append('--full-compat')
        if self.compilation_vars['static_libpython'].get():
            cmd.append('--static-libpython=yes')

        # Module options
        if self.module_vars['follow_stdlib'].get():
            cmd.append('--follow-stdlib')
        if self.module_vars['prefer_source'].get():
            cmd.append('--prefer-source-code')
        if self.module_vars['include_package_data'].get():
            cmd.append('--include-package-data')
        if self.module_vars['python_flag_nosite'].get():
            cmd.append('--python-flag=nosite')
        if self.module_vars['remove_embedded'].get():
            cmd.append('--remove-embedded')

        # Performance options
        if self.perf_vars['disable_ccache'].get():
            cmd.append('--disable-ccache')
        if self.perf_vars['high_memory'].get():
            cmd.append('--jobs=maximum')
        if self.perf_vars['linux_onefile_icon'].get():
            cmd.append('--linux-onefile-icon')
        if self.perf_vars['macos_create_app_bundle'].get():
            cmd.append('--macos-create-app-bundle')

        # Debug options
        if self.debug_vars['debug'].get():
            cmd.append('--debug')
        if self.debug_vars['unstriped'].get():
            cmd.append('--unstriped')
        if self.debug_vars['trace_execution'].get():
            cmd.append('--trace-execution')
        if self.debug_vars['disable_dll_depsubprocess_cache'].get():  # Updated to match the key name
            cmd.append('--disable-dll-dependency-cache')
        if self.debug_vars['experimental'].get():
            cmd.append('--experimental')
        if self.debug_vars['show_memory'].get():
            cmd.append('--show-memory')
        if self.debug_vars['show_progress'].get():
            cmd.append('--show-progress')
        if self.debug_vars['verbose'].get():
            cmd.append('--verbose')

        # Add Nuitka exclusion patterns to prevent it from being included in the build
        cmd.append('--nofollow-import-to=nuitka')
        cmd.append('--nofollow-import-to=ordered_set')
        cmd.append('--nofollow-import-to=wheel')
        cmd.append('--nofollow-import-to=pip')
        cmd.append('--nofollow-import-to=setuptools')
        cmd.append('--nofollow-import-to=distutils')
        cmd.append('--nofollow-import-to=pkg_resources')
        cmd.append('--nofollow-import-to=zstandard')
        
        # Add cleanup flags
        cmd.append('--remove-output')
        cmd.append('--clean-cache=all')

        # Include Tcl/Tk files only if Tkinter support is enabled
        if self.tkinter_var.get():
            tcl_lib, tk_lib, tcl_version = self.get_tcl_tk_paths()
            
            if os.path.exists(tcl_lib):
                cmd.append(f'--include-package=tkinter')
                cmd.append(f'--include-package=_tkinter')
                cmd.append(f'--include-data-dir={tcl_lib}=tcl')
                cmd.append(f'--include-data-dir={tk_lib}=tk')
                
                # Include specific version folders
                tcl_version_dir = os.path.join(tcl_lib, f'tcl{tcl_version.rsplit(".", 1)[0]}')
                tk_version_dir = os.path.join(tk_lib, f'tk{tcl_version.rsplit(".", 1)[0]}')
                
                if os.path.exists(tcl_version_dir):
                    cmd.append(f'--include-data-dir={tcl_version_dir}=tcl{tcl_version.rsplit(".", 1)[0]}')
                if os.path.exists(tk_version_dir):
                    cmd.append(f'--include-data-dir={tk_version_dir}=tk{tcl_version.rsplit(".", 1)[0]}')

            # Add plugin options for tkinter
            cmd.append('--enable-plugin=tk-inter')

            # Exclude unnecessary test modules
            cmd.append('--nofollow-import-to=tkinter.test')
            cmd.append('--nofollow-import-to=tkinter.test.support')
            cmd.append('--nofollow-import-to=tkinter.test.widget_tests')

        # Add the script path as the last argument with proper quoting
        cmd.append(f'"{script_path}"')

        return cmd

    def compile(self):
        if self.use_venv_var.get() and not os.path.exists(self.venv_path.get()):
            messagebox.showwarning("Virtual Environment Required", 
                "Please select a valid virtual environment directory.")
            return

        if not self.script_path.get():
            messagebox.showwarning("Script Required", "Please select a Python script to compile.")
            return

        # Reset button state
        self.open_exe_button.config(state='disabled')
        
        # Check Nuitka installation
        python_path = self.get_venv_python()
        if not self.check_nuitka_installed(python_path):
            if self.use_venv_var.get():
                # For venv, offer to install
                if not messagebox.askyesno("Nuitka Not Found", 
                    "Nuitka is not installed in the selected virtual environment. Would you like to install it?"):
                    self.status_label.config(text="Compilation cancelled - Nuitka not installed")
                    return
                if not self.install_nuitka(python_path):
                    return
            else:
                # For system Python, just show error
                messagebox.showerror("Nuitka Not Found", 
                    "Nuitka is not installed in your system Python installation.\n\n" +
                    "Please either:\n" +
                    "1. Install Nuitka in your system Python using 'pip install nuitka'\n" +
                    "2. Use a virtual environment (recommended)")
                self.status_label.config(text="Compilation cancelled - Nuitka not installed")
                return

        # Update status
        self.status_label.config(text="Starting compilation...")
        
        # Store the exe folder path
        script_dir = os.path.dirname(self.script_path.get())
        self.exe_folder = script_dir

        # Build the command with additional flags to reduce false positives
        cmd = self.build_command()
        cmd.extend([
            '--disable-ccache',    # Disable ccache to prevent some detection issues
            '--remove-output',     # Clean up build artifacts
            '--clean-cache=all'    # Clean Nuitka cache
        ])
        
        command = ' '.join(cmd)

        # Create activation command based on OS
        if os.name == 'nt':  # Windows
            activate_cmd = f"cd /d {self.venv_path.get()}\\Scripts && activate && "
        else:  # Unix-like
            activate_cmd = f"source {self.venv_path.get()}/bin/activate && "

        # Combine activation with the Nuitka command
        full_command = f"{activate_cmd}{command}"

        try:
            if os.name == 'nt':  # Windows
                # Create status flag file
                status_file = os.path.join(os.environ['TEMP'], 'nuitka_status.txt')
                if os.path.exists(status_file):
                    os.remove(status_file)
                    
                batch_file = os.path.join(os.environ['TEMP'], 'nuitka_compile.bat')
                with open(batch_file, 'w') as f:
                    f.write('@echo off\n')
                    
                    # Only include venv activation if using venv
                    if self.use_venv_var.get() and self.venv_path.get():
                        f.write('echo Activating virtual environment...\n')
                        f.write(f'cd /d "{self.venv_path.get()}\\Scripts"\n')
                        f.write('call activate\n')
                        
                        # Add cleanup of Nuitka cache before compilation
                        f.write('echo Cleaning Nuitka cache...\n')
                        f.write('python -m nuitka --clean-cache=all\n')
                        
                        f.write('python -c "import sys; print(f\'(venv) Python version {sys.version.split()[0]} confirmed\')" \n')
                        f.write('echo.\n')
                    
                    f.write('echo Running Nuitka compilation...\n')
                    f.write(f'cd /d "{script_dir}"\n')
                    f.write(f'{command}\n')
                    
                    # Add post-compilation cleanup
                    f.write('echo Cleaning up build artifacts...\n')
                    f.write('if exist build rmdir /s /q build\n')
                    f.write('if exist *.build rmdir /s /q *.build\n')
                    f.write('if exist __pycache__ rmdir /s /q __pycache__\n')
                    
                    f.write('if %ERRORLEVEL% EQU 0 (\n')
                    f.write('    echo Compilation successful!\n')
                    f.write(f'    echo SUCCESS > "{status_file}"\n')
                    f.write('    timeout /t 2 >nul\n')
                    f.write('    exit\n')
                    f.write(') else (\n')
                    f.write('    echo Compilation failed!\n')
                    f.write(f'    echo FAILED > "{status_file}"\n')
                    f.write('    pause\n')
                    f.write(')\n')

                # Run the batch file in a new terminal
                subprocess.Popen(['start', 'cmd', '/c', batch_file], shell=True)

                # Start monitoring the status file
                self.monitor_compilation(status_file)

            else:  # Unix-like systems
                terminal_cmd = f'''
                    gnome-terminal -- bash -c '{full_command}; 
                    if [ $? -eq 0 ]; then 
                        echo "Compilation successful!"; 
                        sleep 2; 
                    else 
                        echo "Compilation failed!"; 
                        read -p "Press Enter to continue..."; 
                    fi'
                '''
                subprocess.Popen(['bash', '-c', terminal_cmd])

            # Enable the open exe button after compilation
            self.open_exe_button.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Compilation Error", f"Error starting compilation: {str(e)}")
            self.status_label.config(text="Compilation failed to start")

    def cleanup_build_artifacts(self):
        """Clean up build artifacts after compilation"""
        if self.exe_folder:
            try:
                # Clean up common build artifacts
                artifacts = ['build', '*.build', '__pycache__']
                for artifact in artifacts:
                    artifact_path = os.path.join(self.exe_folder, artifact)
                    if '*' in artifact:
                        # Handle wildcard patterns
                        import glob
                        for path in glob.glob(artifact_path):
                            if os.path.isdir(path):
                                import shutil
                                shutil.rmtree(path)
                    else:
                        if os.path.exists(artifact_path):
                            import shutil
                            shutil.rmtree(artifact_path)
                
                # Clean Nuitka cache
                python_path = self.get_venv_python()
                subprocess.run([python_path, '-m', 'nuitka', '--clean-cache=all'], 
                             capture_output=True, text=True)
                
                self.status_label.config(text="Build artifacts cleaned up")
                return True
                
            except Exception as e:
                self.status_label.config(text=f"Error cleaning up: {str(e)}")
                return False
        return False

    # Group 5: Utility Methods
    def get_venv_python(self):
        # Get the python executable path for the selected venv
        if self.use_venv_var.get() and self.venv_path.get():
            return os.path.join(self.venv_path.get(), 'Scripts', 'python.exe')
        return 'python'

    def run_in_venv(self, command):
        # Run a command in the context of the selected venv
        if self.use_venv_var.get() and self.venv_path.get():
            venv_python = self.get_venv_python()
            if not os.path.exists(venv_python):
                raise FileNotFoundError(f"Python executable not found in venv: {venv_python}")
            # Use the venv's Python directly instead of activation
            return f'"{venv_python}" {command}'
        return f'python {command}'

    def create_command(self):
        """Create and copy the Nuitka command to clipboard"""
        if not self.script_path.get():
            messagebox.showwarning("Script Required", "Please select a Python script first.")
            return
            
        try:
            # Build the command
            cmd = self.build_command()
            command = ' '.join(cmd)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(command)
            
            # Show confirmation with command preview
            preview = f"Command copied to clipboard:\n\n{command}"
            messagebox.showinfo("Command Created", preview)
            
            # Update status
            self.status_label.config(text="Command created and copied to clipboard")
            
        except Exception as e:
            error_msg = f"Error creating command: {str(e)}"
            self.status_label.config(text="Failed to create command")
            messagebox.showerror("Error", error_msg)

    def open_exe_folder(self):
        """Open the folder containing the compiled executable"""
        if not self.exe_folder or not os.path.exists(self.exe_folder):
            messagebox.showwarning("Error", "Executable folder not found.")
            return
            
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.exe_folder)
            elif os.name == 'darwin':  # macOS
                subprocess.run(['open', self.exe_folder])
            else:  # Linux
                subprocess.run(['xdg-open', self.exe_folder])
                
            self.status_label.config(text="Opened executable folder")
            
        except Exception as e:
            error_msg = f"Error opening folder: {str(e)}"
            self.status_label.config(text="Failed to open folder")
            messagebox.showerror("Error", error_msg)

    def monitor_compilation(self, status_file):
        """Monitor the compilation status file and update UI accordingly"""
        def check_status():
            if not os.path.exists(status_file):
                # Keep checking if file doesn't exist yet
                self.root.after(1000, check_status)
                return
            
            try:
                with open(status_file, 'r') as f:
                    status = f.read().strip()
                
                if status == "SUCCESS":
                    self.status_label.config(text="Compilation successful!")
                    self.open_exe_button.config(state='normal')
                    # Clean up the status file
                    os.remove(status_file)
                    # Clean up build artifacts
                    self.cleanup_build_artifacts()
                elif status == "FAILED":
                    self.status_label.config(text="Compilation failed!")
                    self.open_exe_button.config(state='disabled')
                    # Clean up the status file
                    os.remove(status_file)
                    # Clean up build artifacts
                    self.cleanup_build_artifacts()
                else:
                    # Keep checking if status is not final
                    self.root.after(1000, check_status)
            except Exception as e:
                self.status_label.config(text=f"Error monitoring compilation: {str(e)}")
                if os.path.exists(status_file):
                    os.remove(status_file)
        
        # Start the monitoring loop
        self.root.after(1000, check_status)

# This stays outside the class
if __name__ == '__main__':
    root = tk.Tk()
    app = Nuitkalicious(root)
    root.mainloop()
