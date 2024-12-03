import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
import os
import sys

# this block ensures that the ICON is displayed on the taskbar in Windows
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
        self.root.geometry("700x820")
        
        # Icon
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
        
        # Right column - Advanced options
        self.follow_imports_var = tk.BooleanVar()
        ttk.Checkbutton(right_column, text="Follow Imports", variable=self.follow_imports_var).pack(anchor='w')
        
        self.lto_var = tk.BooleanVar()
        ttk.Checkbutton(right_column, text="Enable LTO", variable=self.lto_var).pack(anchor='w')
        
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
        
        ttk.Button(icon_frame, text="Select Icon", command=self.select_icon).pack(side='right')
        ttk.Button(icon_frame, text="Clear", command=self.clear_icon).pack(side='right', padx=5)
        
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
        ttk.Button(action_frame, text="Compile", command=self.compile).pack(side='left', padx=5)
        
        # Create Command button
        ttk.Button(action_frame, text="Create Command", command=self.create_command).pack(side='left', padx=5)
        
        # Open EXE folder button (disabled by default)
        self.open_exe_button = ttk.Button(action_frame, text="Open Executable Folder", 
                                        command=self.open_exe_folder, state='disabled')
        self.open_exe_button.pack(side='left', padx=5)
        
    def setup_output_panel(self, parent):
        self.output_text = scrolledtext.ScrolledText(parent, height=8)
        self.output_text.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.command_preview = scrolledtext.ScrolledText(parent, height=5)
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
        else:
            self.venv_entry.config(state='disabled')
            self.venv_browse_button.config(state='disabled')
            self.activate_venv_button.config(state='disabled')
            
    def browse_venv(self):
        venv_dir = filedialog.askdirectory(title="Select Virtual Environment Directory")
        if venv_dir:
            self.venv_path.set(venv_dir)
            if os.path.exists(venv_dir):
                self.activate_venv_button.config(state='normal')
                
    def activate_venv(self):
        venv_path = self.venv_path.get()
        if not venv_path:
            self.output_text.insert('end', "Error: No virtual environment path selected\n")
            return
            
        activate_script = os.path.join(venv_path, 'Scripts', 'activate')
        if not os.path.exists(activate_script):
            self.output_text.insert('end', f"Error: Could not find activation script at {activate_script}\n")
            return
            
        try:
            command = f'cmd /c ""{activate_script}" && python --version"'
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=True
            )
            
            self.output_text.insert('end', f"Activating virtual environment at: {venv_path}\n")
            
            output, _ = process.communicate()
            if output:
                if "not recognized" not in output and "Error" not in output:
                    self.output_text.insert('end', f"Virtual environment activated successfully!\n")
                    self.output_text.insert('end', f"Using: {output}\n")
                else:
                    self.output_text.insert('end', f"Error activating venv: {output}\n")
            
            self.output_text.see('end')
            
        except Exception as e:
            self.output_text.insert('end', f"Error activating virtual environment: {str(e)}\n")
            
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
        """Get the python executable path for the selected venv"""
        if self.use_venv_var.get() and self.venv_path.get():
            return os.path.join(self.venv_path.get(), 'Scripts', 'python.exe')
        return 'python'

    def run_in_venv(self, command):
        """Run a command in the context of the selected venv"""
        if self.use_venv_var.get() and self.venv_path.get():
            venv_python = self.get_venv_python()
            if not os.path.exists(venv_python):
                raise FileNotFoundError(f"Python executable not found in venv: {venv_python}")
            # Use the venv's Python directly instead of activation
            return f'"{venv_python}" {command}'
        return f'python {command}'

    def build_command(self):
        cmd = []
        
        # Use venv python directly instead of activation
        if self.use_venv_var.get() and self.venv_path.get():
            venv_python = self.get_venv_python()
            cmd.append(f'"{venv_python}" -m nuitka')
        else:
            cmd.append('python -m nuitka')

        # Add automatic yes for downloads
        cmd.append('--assume-yes-for-downloads')

        # Get the directory of the selected Python script
        if self.script_path.get():
            script_dir = os.path.dirname(self.script_path.get())
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
            cmd.append('--windows-disable-console')
        if self.follow_imports_var.get():
            cmd.append('--follow-imports')
        if self.lto_var.get():
            cmd.append('--lto=yes')
        if self.tkinter_var.get():
            cmd.append('--enable-plugin=tk-inter')
        if self.jobs_var.get():
            cmd.append(f'--jobs={self.jobs_var.get()}')
            
        # Add icon if selected
        if self.icon_path:
            cmd.append(f'--windows-icon-from-ico="{self.icon_path}"')
            
        # Add resource files to command with proper quoting
        for res_file in self.resource_files:
            # Use basename of the file as the target path
            target_path = os.path.basename(res_file)
            if not res_file.lower().endswith('.ico'):  # Skip .ico files from general resources
                cmd.append(f'--include-data-file="{res_file}"="{target_path}"')
            
        # Add the script path as the last argument with proper quoting
        cmd.append(f'"{self.script_path.get()}"')
        
        return cmd

    def check_nuitka_installed(self):
        try:
            cmd = self.run_in_venv('-c "import nuitka"')
            process = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
            return process.returncode == 0
        except Exception:
            return False

    def run_command(self, cmd, shell=True):
        """Run a command and capture its output in real-time"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=shell
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_text.insert('end', output)
                    self.output_text.see('end')
                    self.root.update_idletasks()
            
            success = process.returncode == 0
            if success:
                self.open_exe_button.config(state='normal')
            return success
            
        except Exception as e:
            self.output_text.insert('end', f"Error executing command: {str(e)}\n")
            return False

    def install_nuitka(self):
        try:
            venv_python = self.get_venv_python()
            self.output_text.insert('end', "Upgrading pip and installing wheel...\n")
            
            # Upgrade pip
            pip_cmd = f'"{venv_python}" -m pip install --upgrade pip'
            if not self.run_command(pip_cmd):
                return False
                
            # Install wheel
            wheel_cmd = f'"{venv_python}" -m pip install --upgrade wheel'
            if not self.run_command(wheel_cmd):
                return False
            
            # Install Nuitka and dependencies
            self.output_text.insert('end', "Installing Nuitka...\n")
            nuitka_cmd = f'"{venv_python}" -m pip install --upgrade nuitka ordered-set'
            if not self.run_command(nuitka_cmd):
                return False
            
            # Verify installation
            verify_cmd = f'"{venv_python}" -c "import nuitka"'
            if not self.run_command(verify_cmd):
                self.output_text.insert('end', "Nuitka installation verification failed.\n")
                return False
            
            self.output_text.insert('end', "Nuitka installed and verified successfully.\n")
            return True
                
        except Exception as e:
            self.output_text.insert('end', f"Error installing Nuitka: {str(e)}\n")
            return False

    def compile(self):
        if not self.script_path.get():
            self.output_text.insert('end', "Error: No script selected\n")
            return

        # Reset button state
        self.open_exe_button.config(state='disabled')
        
        # Store the exe folder path
        script_dir = os.path.dirname(self.script_path.get())
        self.exe_folder = script_dir

        self.output_text.delete('1.0', 'end')
        
        if not self.check_nuitka_installed():
            self.output_text.insert('end', "Nuitka is not installed. Installing now...\n")
            if not self.install_nuitka():
                self.output_text.insert('end', "Failed to install Nuitka. Aborting compilation.\n")
                return
            self.output_text.insert('end', "Nuitka installed successfully.\n")

        cmd = self.build_command()
        command = ' '.join(cmd)
        self.command_preview.delete('1.0', 'end')
        self.command_preview.insert('end', command)
        self.output_text.insert('end', f"Executing command:\n{command}\n\n")        
        threading.Thread(target=lambda: self.run_command(command), daemon=True).start()

    def open_exe_folder(self):
        if self.exe_folder and os.path.exists(self.exe_folder):
            os.startfile(self.exe_folder)  # Windows
            # For other platforms you might use:
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
        """Create and display the Nuitka command without executing it"""
        if not self.script_path.get():
            self.output_text.insert('end', "Error: No script selected\n")
            return
            
        cmd = self.build_command()
        command = ' '.join(cmd)
        self.command_preview.delete('1.0', 'end')
        self.command_preview.insert('end', command)
        self.output_text.insert('end', f"Command created:\n{command}\n\n")
        self.output_text.see('end')

# Move this outside the class, with proper indentation
if __name__ == '__main__':
    root = tk.Tk()
    app = Nuitkalicious(root)
    root.mainloop()