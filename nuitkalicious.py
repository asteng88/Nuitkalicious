import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
from tkterm import Terminal

# this block (9-14) ensures that the ICON is displayed on the taskbar in Windows
try:
    from ctypes import windll
    my_appid = 'com.asteng88.nuitkalicious.nuitkalicious.1.0.0'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_appid)
except ImportError:
    pass

class Nuitkalicious:

    def __init__(self, root):
        self.root = root
        self.root.title("Nuitkalicious - Nuitka GUI")
        self.root.geometry("750x830")
        
        # Icon for the app - nuitkalicious.ico
        base_path = os.path.dirname(__file__)
        os.chdir(base_path)
        icon_path = os.path.join(base_path, 'nuitkalicious.ico')
        
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                print(f"Could not load icon: {icon_path}")

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Basic options tab
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text='Basic Options')
        
        # Output panel under Basic Options tab  
        self.setup_basic_options()
        self.setup_output_panel(self.basic_frame)
        
        self.resource_files = []  # Store resource file paths
        self.exe_folder = None  # Store the exe folder path
        self.icon_path = None  # Store icon path
        self.venv_active = False  # Track if venv is active
        
        # Advanced options tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_frame, text='Advanced Options')
        
        # Setup advanced options
        self.setup_advanced_options()

    def setup_basic_options(self):
        # File selection
        file_frame = ttk.LabelFrame(self.basic_frame, text="Python File", padding=5)
        file_frame.pack(fill='x', padx=5, pady=5)
        
        self.script_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.script_path).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='right')
        
        # Common options with two columns
        options_frame = ttk.LabelFrame(self.basic_frame, text="Options", padding=5)
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Create two columns
        left_column = ttk.Frame(options_frame)
        left_column.pack(side='left', fill='both', expand=True, padx=5)
        right_column = ttk.Frame(options_frame)
        right_column.pack(side='left', fill='both', expand=True, padx=5)
        
        # Left column - Basic options
        self.standalone_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="Standalone", variable=self.standalone_var).pack(anchor='w')
        
        self.onefile_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="One File", variable=self.onefile_var).pack(anchor='w')
        
        self.remove_output_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="Remove Output", variable=self.remove_output_var).pack(anchor='w')
        
        self.no_console_var = tk.BooleanVar()
        ttk.Checkbutton(left_column, text="No Console", variable=self.no_console_var).pack(anchor='w')
        
        # Right column - Basic options (removed duplicated options)
        self.follow_imports_var = tk.BooleanVar()
        ttk.Checkbutton(right_column, text="Follow Imports", variable=self.follow_imports_var).pack(anchor='w')
        
        # Add LTO checkbox to basic options
        self.lto_var = tk.BooleanVar()
        ttk.Checkbutton(right_column, text="LTO (Link Time Optimization)", variable=self.lto_var).pack(anchor='w')
        
        self.tkinter_var = tk.BooleanVar()
        ttk.Checkbutton(right_column, text="Enable Tkinter Support", variable=self.tkinter_var).pack(anchor='w')
        
        # Jobs selection
        jobs_frame = ttk.Frame(right_column)
        jobs_frame.pack(fill='x', pady=5)
        ttk.Label(jobs_frame, text="Jobs:").pack(side='left')
        self.jobs_var = tk.StringVar(value="1")
        ttk.Spinbox(jobs_frame, from_=1, to=16, textvariable=self.jobs_var, width=5).pack(side='left', padx=5)
        
        # Virtual environment option
        venv_frame = ttk.LabelFrame(self.basic_frame, text="Virtual Environment (venv)", padding=5)
        venv_frame.pack(fill='x', padx=5, pady=5)
        
        self.use_venv_var = tk.BooleanVar()
        ttk.Checkbutton(venv_frame, text="Use venv", variable=self.use_venv_var, command=self.toggle_venv_browse).pack(anchor='w')
        
        self.venv_path = tk.StringVar()
        self.venv_entry = ttk.Entry(venv_frame, textvariable=self.venv_path, state='disabled')
        self.venv_entry.pack(side='left', expand=True, fill='x', padx=5)
        self.venv_browse_button = ttk.Button(venv_frame, text="Browse", command=self.browse_venv, state='disabled')
        self.venv_browse_button.pack(side='right')
        
        # Add activate button after venv frame
        self.activate_venv_button = ttk.Button(self.basic_frame, text="Activate venv", 
                                             command=self.activate_venv, state='disabled')
        self.activate_venv_button.pack(pady=5)
        
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
        
        # Compile button
        self.compile_button = ttk.Button(action_frame, text="Compile", 
                                       command=self.compile, state='disabled')
        self.compile_button.pack(side='left', padx=5)
        
        # Create Command button
        ttk.Button(action_frame, text="Create & Copy Command", command=self.create_command).pack(side='left', padx=5)
        
        # Open EXE folder button (disabled by default)
        self.open_exe_button = ttk.Button(action_frame, text="Open Executable Folder", 
                                        command=self.open_exe_folder, state='disabled')
        self.open_exe_button.pack(side='left', padx=5)
        
        # Add Clear All button
        ttk.Button(action_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=5)
        
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
        self.use_venv_var.set(False)
        self.lto_var.set(False)
        
        # Reset other states
        self.venv_entry.config(state='disabled')
        self.venv_browse_button.config(state='disabled')
        self.activate_venv_button.config(state='disabled')
        self.open_exe_button.config(state='disabled')

        # Clear the terminal box
        self.terminal.clear()
        
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
        self.compile_button.config(state='disabled')

    def setup_output_panel(self, parent):
        # Replace scrolled text with terminal
        terminal_frame = ttk.LabelFrame(parent, text="Terminal Output", padding=5)
        terminal_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.terminal = Terminal(terminal_frame)
        self.terminal.pack(expand=True, fill='both')
        
        # Keep command preview for reference
        self.command_preview = scrolledtext.ScrolledText(parent, height=6)
        self.command_preview.pack(fill='x', padx=5, pady=5)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filename:
            self.script_path.set(filename)
            
    def toggle_venv_browse(self):
        if self.use_venv_var.get():
            self.venv_entry.config(state='normal')
            self.venv_browse_button.config(state='normal')
            if os.path.exists(self.venv_path.get()):
                self.activate_venv_button.config(state='normal')
            self.compile_button.config(state='disabled')  # Disable compile until venv is activated
            self.venv_active = False
        else:
            self.venv_entry.config(state='disabled')
            self.venv_browse_button.config(state='disabled')
            self.activate_venv_button.config(state='disabled')
            self.compile_button.config(state='disabled')
            self.venv_active = False
            
    def browse_venv(self):
        venv_dir = filedialog.askdirectory(title="Select Virtual Environment Directory")
        if venv_dir:
            self.venv_path.set(venv_dir)
            if os.path.exists(venv_dir):
                self.activate_venv_button.config(state='normal')
                
    def activate_venv(self):
        venv_path = self.venv_path.get()
        if not venv_path:
            self.terminal.write("Error: No virtual environment path selected\n")
            return
            
        activate_script = os.path.join(venv_path, 'Scripts', 'activate')
        if not os.path.exists(activate_script):
            self.terminal.write(f"Error: Could not find activation script at {activate_script}\n")
            return
            
        try:
            # Run activation in terminal
            self.terminal.write(f"Activating virtual environment at: {venv_path}\n")
            self.terminal.run_command(f'"{activate_script}"')
            
            # Verify activation
            self.terminal.run_command('python --version')
            self.venv_active = True
            self.compile_button.config(state='normal')
            
        except Exception as e:
            self.terminal.write(f"Error activating virtual environment: {str(e)}\n")
            self.venv_active = False
            self.compile_button.config(state='disabled')
            
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

    def build_command(self):
        cmd = []
        
        # Check if we're running as a compiled executable
        import sys
        is_frozen = getattr(sys, 'frozen', False)
        
        # When running as compiled exe, use system Python for Nuitka
        if is_frozen:
            # Get system Python path
            import subprocess
            try:
                result = subprocess.run(['where', 'python'], capture_output=True, text=True)
                system_python = result.stdout.splitlines()[0] if result.returncode == 0 else 'python'
                cmd.append(f'"{system_python}" -m nuitka')
            except Exception:
                cmd.append('python -m nuitka')
        else:
            # Normal behavior when running from source
            if self.venv_active and self.venv_path.get():
                venv_python = self.get_venv_python()
                cmd.append(f'"{venv_python}" -m nuitka')
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
        if self.standalone_var.get():
            cmd.append('--standalone')
        if self.onefile_var.get():
            cmd.append('--onefile')
        if self.remove_output_var.get():
            cmd.append('--remove-output')
        if self.no_console_var.get():
            # Updated console option for newer Nuitka versions
            cmd.append('--windows-console-mode=disable')
        if self.follow_imports_var.get():
            cmd.append('--follow-imports')
        if self.tkinter_var.get():
            cmd.append('--enable-plugin=tk-inter')
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
        # ...existing code for advanced options...

        # Add the script path as the last argument with proper quoting
        cmd.append(f'"{script_path}"')

        return cmd

    def check_nuitka_installed(self):
        try:
            cmd = self.run_in_venv('-c "import nuitka"')
            process = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
            return process.returncode == 0
        except Exception:
            return False

    def run_command(self, cmd, shell=True):
        try:
            # Use PIPE for stdout/stderr and disable buffering
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                universal_newlines=True,
                bufsize=0,  # Disable buffering
                startupinfo=startupinfo
            )
            
            def read_pipe(pipe):
                while True:
                    char = pipe.read(1)
                    if char == '' and process.poll() is not None:
                        break
                    if char:
                        self.terminal.write(char)
                        self.root.update_idletasks()
            
            stdout_thread = threading.Thread(target=read_pipe, args=(process.stdout,))
            stderr_thread = threading.Thread(target=read_pipe, args=(process.stderr,))
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            
            stdout_thread.start()
            stderr_thread.start()
            
            return_code = process.wait()
            
            stdout_thread.join()
            stderr_thread.join()
            
            return return_code == 0
            
        except Exception as e:
            self.terminal.write(f"Error executing command: {str(e)}\n")
            return False

    def install_nuitka(self):
        try:
            venv_python = self.get_venv_python()
            self.terminal.write("Upgrading pip and installing wheel...\n")
            
            # Check Python version before installing
            if not self.check_python_version_compatibility():
                self.terminal.write("Warning: Installing Nuitka with mismatched Python versions may cause issues.\n")
            
            # Upgrade pip
            pip_cmd = f'"{venv_python}" -m pip install --upgrade pip'
            if not self.run_command(pip_cmd):
                return False
                
            # Install wheel
            wheel_cmd = f'"{venv_python}" -m pip install --upgrade wheel'
            if not self.run_command(wheel_cmd):
                return False
            
            # Install Nuitka and dependencies
            self.terminal.write("Installing Nuitka...\n")
            nuitka_cmd = f'"{venv_python}" -m pip install --upgrade nuitka ordered-set'
            if not self.run_command(nuitka_cmd):
                return False
            
            # Verify installation
            verify_cmd = f'"{venv_python}" -c "import nuitka"'
            if not self.run_command(verify_cmd):
                self.terminal.write("Nuitka installation verification failed.\n")
                return False
            
            self.terminal.write("Nuitka installed and verified successfully.\n")
            return True
                
        except Exception as e:
            self.terminal.write(f"Error installing Nuitka: {str(e)}\n")
            return False

    def check_python_version_compatibility(self):
        if not self.use_venv_var.get():
            return True  # Skip check if not using venv
            
        try:
            venv_python = self.get_venv_python()
            if not os.path.exists(venv_python):
                self.terminal.write(f"Error: Python executable not found in venv: {venv_python}\n")
                return False
            
            # Only get venv Python version
            venv_cmd = f'"{venv_python}" -c "import sys; print(sys.version)"'
            process = subprocess.run(venv_cmd, shell=True, capture_output=True, text=True)
            
            if process.returncode == 0:
                version_info = process.stdout.strip()
                self.terminal.write(f"Using virtual environment Python: {version_info}\n")
                return True
            else:
                self.terminal.write(f"Error checking Python version: {process.stderr}\n")
                return False
                
        except Exception as e:
            self.terminal.write(f"Error checking Python: {str(e)}\n")
            return False

    def compile(self):
        if not self.venv_active:
            messagebox.showwarning("Virtual Environment Required", 
                "Please select and activate a virtual environment before compiling.")
            return

        if not self.script_path.get():
            self.terminal.write("Error: No script selected\n")
            return

        # Reset button state
        self.open_exe_button.config(state='disabled')
        
        # Clear terminal
        self.terminal.clear()
        
        # Store the exe folder path
        script_dir = os.path.dirname(self.script_path.get())
        self.exe_folder = script_dir

        # Verify venv is still valid
        venv_python = self.get_venv_python()
        if not os.path.exists(venv_python):
            self.terminal.write("Error: Virtual environment Python not found. Please reactivate venv.\n")
            return
            
        try:
            # Check if Nuitka is installed in the venv
            if not self.check_nuitka_installed():
                self.terminal.write("Nuitka is not installed in virtual environment. Installing now...\n")
                if not self.install_nuitka():
                    self.terminal.write("Failed to install Nuitka. Aborting compilation.\n")
                    return
                self.terminal.write("Nuitka installed successfully.\n")

            # Display which Python we're using (moved after venv_python is defined)
            self.terminal.write(f"Using Python from: {venv_python}\n\n")

            # Rest of compilation process
            cmd = self.build_command()
            command = ' '.join(cmd)
            self.command_preview.delete('1.0', 'end')
            self.command_preview.insert('end', command)
            self.terminal.write(f"Executing command:\n{command}\n\n")
            
            def compile_thread():
                try:
                    success = self.run_command(command)
                    if success:
                        self.root.after(0, lambda: [
                            self.open_exe_button.config(state='normal'),
                            messagebox.showinfo("Compilation Complete", "Compilation completed successfully!")
                        ])
                    else:
                        self.root.after(0, lambda: 
                            messagebox.showerror("Compilation Error", 
                                "Compilation completed with errors! Check the terminal output for details.")
                        )
                except Exception as e:
                    self.root.after(0, lambda: 
                        messagebox.showerror("Compilation Error", str(e))
                    )
            
            threading.Thread(target=compile_thread, daemon=True).start()
            
        except Exception as e:
            self.terminal.write(f"Compilation error: {str(e)}\n")
            messagebox.showerror("Compilation Error", str(e))

    def open_exe_folder(self):
        if self.exe_folder and os.path.exists(self.exe_folder):
            os.startfile(self.exe_folder)  # Windows
            # For other platforms use the following:
            # subprocess.run(['xdg-open', self.exe_folder])  # Linux
            # subprocess.run(['open', self.exe_folder])      # macOS

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

    def create_command(self):
        # Create and display the Nuitka command without executing it
        if not self.script_path.get():
            self.terminal.write("Error: No script selected\n")
            return
            
        cmd = self.build_command()
        command = ' '.join(cmd)
        
        # Update command preview and terminal
        self.command_preview.delete('1.0', 'end')
        self.command_preview.insert('end', command)
        self.terminal.write(f"Command created:\n{command}\n\n")
        self.terminal.see('end')
        
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(command)
        
        # Show confirmation
        messagebox.showinfo("Command Copied", "Command has been created and copied to clipboard.")

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

        # Compilation Options
        compile_frame = ttk.LabelFrame(scrollable_frame, text="Compilation Options", padding=5)
        compile_frame.pack(fill='x', padx=5, pady=5)

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

        # Module Options
        module_frame = ttk.LabelFrame(scrollable_frame, text="Module Options", padding=5)
        module_frame.pack(fill='x', padx=5, pady=5)

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

        # Performance Options
        perf_frame = ttk.LabelFrame(scrollable_frame, text="Performance Options", padding=5)
        perf_frame.pack(fill='x', padx=5, pady=5)

        self.perf_vars = {
            'disable_ccache': tk.BooleanVar(),
            'high_memory': tk.BooleanVar(),
            'linux_onefile_icon': tk.BooleanVar(),
            'macos_create_app_bundle': tk.BooleanVar()
        }  # Removed 'lto' from this dict

        for name, var in self.perf_vars.items():
            ttk.Checkbutton(perf_frame, text=name.replace('_', ' ').title(), 
                           variable=var).pack(anchor='w')

        # Debug Options
        debug_frame = ttk.LabelFrame(scrollable_frame, text="Debug Options", padding=5)
        debug_frame.pack(fill='x', padx=5, pady=5)

        self.debug_vars = {
            'debug': tk.BooleanVar(),
            'unstriped': tk.BooleanVar(),
            'trace_execution': tk.BooleanVar(),
            'disable_dll_dependency_cache': tk.BooleanVar(),
            'experimental': tk.BooleanVar(),
            'show_memory': tk.BooleanVar(),
            'show_progress': tk.BooleanVar(),
            'verbose': tk.BooleanVar(),
        }

        for name, var in self.debug_vars.items():
            ttk.Checkbutton(debug_frame, text=name.replace('_', ' '). title(), 
                           variable=var).pack(anchor='w')

        # Optimization Options
        optim_frame = ttk.LabelFrame(scrollable_frame, text="Optimization Options", padding=5)
        optim_frame.pack(fill='x', padx=5, pady=5)

        self.optimization_level = tk.StringVar(value="2")
        ttk.Label(optim_frame, text="Optimization Level:").pack(side='left')
        ttk.Spinbox(optim_frame, from_=0, to=3, width=5, 
                    textvariable=self.optimization_level).pack(side='left', padx=5)

        # Package all frames with scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

# This stays outside the class, with proper indentation
if __name__ == '__main__':
    root = tk.Tk()
    app = Nuitkalicious(root)
    root.mainloop()
