import tkinter as tk
from tkinter import ttk
import subprocess
import os
import threading

class Terminal(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create text widget with green text
        self.text = tk.Text(self, wrap='word', bg='black', fg='#00ff00')  # Bright green retro!
        self.text.pack(expand=True, fill='both')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        scrollbar.pack(side='right', fill='y')
        self.text.configure(yscrollcommand=scrollbar.set)
        
        # Configure terminal-like font
        self.text.configure(font=('Consolas', 10))
        
        # Store the current working directory
        self.cwd = os.getcwd()

    def write(self, text):
        self.text.insert('end', text)
        self.text.see('end')
        self.update()

    def clear(self):
        self.text.delete('1.0', 'end')

    def run_command(self, cmd):
        def execute():
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
                    shell=True,
                    cwd=self.cwd,
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
                            self.write(char)
                            self.update()
                
                # Create threads for stdout and stderr
                stdout_thread = threading.Thread(target=read_pipe, args=(process.stdout,))
                stderr_thread = threading.Thread(target=read_pipe, args=(process.stderr,))
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                
                stdout_thread.start()
                stderr_thread.start()
                
                process.wait()
                stdout_thread.join()
                stderr_thread.join()
                
            except Exception as e:
                self.write(f"Error: {str(e)}\n")
        
        thread = threading.Thread(target=execute)
        thread.daemon = True
        thread.start()
    
    def see(self, index):
        self.text.see(index)