import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import font
import csv
import time
import threading


def approximate_char_width(font, string, approx_char='0'):
    # Pixel width of string in the provided font
    string_px_width = font.measure(string)
    # Using '0' to approximate 1 char in font
    approx_char_px_width = font.measure(approx_char)
    # Get approximate char width in font with 
    return int(string_px_width / approx_char_px_width)

class Step:
    def __init__(self, parent, label, delete_cb=None):
        self.frame = tk.Frame(parent)
        self.frame.grid_columnconfigure(1, weight=1)
        self.label = label
        self.delete_cb = delete_cb

        self.time = 0
        self.running = False
        self.start_time = None

        self.setup_widgets()

    def setup_widgets(self):
        self.delete_button = tk.Button(self.frame, text='Delete', command=self.delete_step)
        self.delete_button.grid(row=0, column=0, padx=2, pady=2, sticky='w')

        self.name_entry = tk.Entry(self.frame)
        self.name_entry.insert(0, self.label)
        self.name_entry.grid(row=0, column=1, padx=2, pady=2, sticky='ew')

        self.time_display = tk.Label(self.frame, text=self.format_time(self.time))
        self.time_display.grid(row=0, column=2, padx=2, pady=2)

        self.pause_resume_button = tk.Button(self.frame, text='Resume', command=self.toggle_timer)
        # Configure width of pause/resume button based on "Resume" char width so that it doesn't shrink
        btn_font = font.nametofont(self.pause_resume_button.cget('font'))
        self.pause_resume_button.config(width=approximate_char_width(btn_font, 'Resume'))
        self.pause_resume_button.grid(row=0, column=3, padx=2, pady=2, sticky='e')

        self.reset_button = tk.Button(self.frame, text='Reset', command=self.reset_timer)
        self.reset_button.grid(row=0, column=4, padx=2, pady=2, sticky='e')

    def format_time(self, milliseconds):
        """Format milliseconds into HH:MM:SS.ssss."""
        hours = milliseconds // 3600000
        minutes = (milliseconds % 3600000) // 60000
        seconds = (milliseconds % 60000) // 1000
        millis = milliseconds % 1000
        return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


    def update_time(self):
        if self.running:
            elapsed = int((time.time() - self.start_time) * 1000)
            self.time += elapsed
            self.start_time = time.time()
            self.time_display.config(text=self.format_time(self.time))
        if self.running:
            self.frame.after(100, self.update_time)

    def start_timer(self):
        self.running = True
        self.start_time = time.time()
        self.update_time()
        self.pause_resume_button.config(text='  Pause  ')

    def pause_timer(self):
        self.running = False
        self.pause_resume_button.config(text='Resume')

    def toggle_timer(self):
        if self.running:
            self.pause_timer()
        else:
            self.start_timer()

    def reset_timer(self):
        self.time = 0
        self.time_display.config(text=self.format_time(self.time))

    def delete_step(self):
        self.delete_cb(self)
        self.frame.destroy()

class TimeStudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Time Study")
        
        #self.set_icon('resources/app_icon.png')

        # Initialize window dimensions relative to screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = int(screen_width * .4)
        initial_height = int(screen_height * .4)
        self.root.geometry(f'{initial_width}x{initial_height}')
        
        # Set minimum size of window to something reasonable
        self.root.minsize(200, 100)

        self.steps_frame = tk.Frame(self.root)
        self.steps_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure the grid columns in the steps frame
        self.steps_frame.grid_columnconfigure(1, weight=1)

        self.step_widgets = []
        self.current_step = None
        
        self.autosave_enabled = True
        self.current_file = None

        self.create_menu()
        self.create_control_panel()

        self.autosave_interval = 5000  # 5 seconds
        self.autosave_thread = threading.Thread(target=self.autosave_loop, daemon=True)
        self.autosave_thread.start()

        self.root.bind("<Tab>", self.tab_step)
        # Binding for adding a new step
        self.root.bind("<Alt-n>", self.add_step)
        # Bindings for selecting previous step
        self.root.bind("<Up>", self.previous_step)
        # Binding for selecting previous step, but pause current step before moving
        self.root.bind("<Control-Up>", self.pause_then_previous_step)
        # Bindings for selecting next step
        self.root.bind("<Down>", self.next_step)
        # Binding for selecting next step, but pause current step before moving
        self.root.bind("<Control-Down>", self.pause_then_next_step)
        # Bind for selecting first step
        self.root.bind("<Control-Home>", self.select_first_step)
        # Bind for selecting last step
        self.root.bind("<Control-End>", self.select_last_step)
        # Bindings for pausing/resuming current step's timer
        self.root.bind("<Return>", self.toggle_current_timer)
        self.root.bind("<Control-Return>", self.toggle_current_timer)
        # Bindings for resetting current timer
        self.root.bind("<Control-r>", self.reset_current_timer)
        # Bindings for toggling autosave feature
        self.root.bind("<Control-q>", self.toggle_autosave)
        # Bindings for resetting interface (i.e. starting a new time study)
        self.root.bind("<Control-n>", self.reset_interface)
        # Bindings for File Menu
        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-Shift-s>", self.save_as_file)

    def set_icon(self, icon_file):
        """Set the window icon using a PNG image"""
        icon = tk.PhotoImage(file=icon_file)
        self.root.iconphoto(False, icon)

    def create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        # File menu
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As", accelerator="Ctrl+Shift+S", command=self.save_as_file)
        
        # Help menu
        help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Show Shortcuts", command=self.show_shortcuts)
        

    def create_control_panel(self):
        control_panel = tk.Frame(self.root)
        control_panel.pack(fill=tk.X)

        self.autosave_check = tk.Checkbutton(control_panel, text="Autosave", variable=tk.BooleanVar(value=self.autosave_enabled))
        self.autosave_check.config(command=self.toggle_autosave)
        self.autosave_check.pack(side=tk.LEFT)

        self.add_button = tk.Button(control_panel, text="Add Step", command=self.add_step)
        self.add_button.pack(side=tk.LEFT)

    def show_shortcuts(self, event=None):
        shortcuts = (
            "NAVIGATION\n"
            "Previous step: Up Arrow key\n"
            "Previous step (pause current step, then move): Ctrl + Up Arrow key\n"
            "Next step: Down Arrow key\n"
            "Next step (pause current step, then move): Ctrl + Down Arrow key\n"
            "Next step (add new step if last, pause current before moving): Tab\n"
            "First step: Ctrl+Home\n"
            "Last step: Ctrl+End\n"
            "\n"
            "CURRENT (HIGHLIGHTED) TIMER\n"
            "Pause/Resume current timer: Return or Ctrl+Return\n"
            "Reset current timer: Ctrl+R\n"
            "\n"
            "MAIN INTERFACE\n"
            "New time study / reset interface: Ctrl+N\n"
            "Add step: Alt+N or Tab (adds new step if no next step)\n"
            "Toggle autosave: Ctrl+Q\n"
            "\n"
            "FILE MENU\n"
            "Open file: Ctrl+O\n"
            "Save file: Ctrl+S\n"
            "Save file As: Ctrl+Shift+S\n"
        )
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def tab_step(self, event=None):
        if not self.current_step:
            self.add_step()
            return
        
        # Regardless of next/new, current step should always be paused first
        self.current_step.pause_timer()
        
        index = self.step_widgets.index(self.current_step)
        if index < len(self.step_widgets) - 1:
            self.select_step(self.step_widgets[index + 1])
        else:
            self.add_step()
            return        

    def add_step(self, event=None):
        step = Step(self.steps_frame, label="", delete_cb=self.remove_step)
        step.frame.pack(fill=tk.X, padx=5, pady=2)
        # Step is selected when name entry gains focus
        step.name_entry.bind("<FocusIn>", lambda e, s=step: self.select_step(s))
        # Step is selected when pause/resume button pressed
        step.pause_resume_button.bind('<Button-1>', lambda e, s=step: self.select_step(s))
        # Step is selected when reset button pressed
        step.reset_button.bind('<Button-1>', lambda e, s=step: self.select_step(s))
        self.step_widgets.append(step)
        # Always select a step if it was just added
        self.select_step(step)
        # And set the focus to the name entry of that new step
        step.name_entry.focus_set()
        # Delay setting focus to ensure the widget is fully displayed first
        self.root.after(100, step.name_entry.focus_set)
        
    def remove_step(self, step):
        self.step_widgets.remove(step)

    def select_step(self, step):
        if self.current_step and self.current_step.frame.winfo_exists():
            self.current_step.frame.config(bg=self.root.cget("bg"))
        self.current_step = step
        self.current_step.frame.config(bg="lightblue")
        self.current_step.name_entry.focus_set()

    def previous_step(self, event=None):
        if self.current_step:
            index = self.step_widgets.index(self.current_step)
            if index > 0:
                self.select_step(self.step_widgets[index - 1])

    def next_step(self, event=None):
        if self.current_step:
            index = self.step_widgets.index(self.current_step)
            if index < len(self.step_widgets) - 1:
                self.select_step(self.step_widgets[index + 1])

    def pause_then_previous_step(self, event=None):
        if self.current_step:
            self.current_step.pause_timer()
            self.previous_step()

    def pause_then_next_step(self, event=None):
        if self.current_step:
            self.current_step.pause_timer()
            self.next_step()
    
    def select_first_step(self, event=None):
        if self.step_widgets:
            self.select_step(self.step_widgets[0])
    
    def select_last_step(self, event=None):
        if self.step_widgets:
            self.select_step(self.step_widgets[-1])

    def toggle_current_timer(self, event=None):
        if self.current_step:
            if self.current_step.running:
                self.current_step.pause_timer()
            else:
                self.current_step.start_timer()

    def reset_current_timer(self, event=None):
        if self.current_step:
            response = messagebox.askyesno("Reset Timer", f"Do you want to reset the timer for '{self.current_step.name_entry.get()}'?")
            if response:
                self.current_step.reset_timer()
                
    def reset_interface(self, event=None):
        response = messagebox.askyesno("Reset Interface", "Do you want to reset the entire time study interface? All steps will be removed.")
        if response:
            for step in self.step_widgets:
                step.frame.destroy()
            self.step_widgets = []
            self.current_step = None

    def toggle_autosave(self, event=None):
        self.autosave_enabled = not self.autosave_enabled
        if self.autosave_enabled:
            self.autosave_check.select()
        else:
            self.autosave_check.deselect()

    def autosave_loop(self):
        while True:
            time.sleep(self.autosave_interval / 1000.0)
            if self.autosave_enabled and self.current_file:
                try:
                    self.save_to_file(self.current_file)
                except PermissionError as ex:
                    print('Permission denied to save file. Please ensure the file is closed in other programs.')
                    print(ex)

    def save_file(self, event=None):
        print('save_file')
        if not hasattr(self, 'current_file'):
            self.save_as_file()
        else:
            self.save_to_file(self.current_file)

    def save_as_file(self, event=None):
        print('save_as_file')
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file:
            self.current_file = file
            self.save_to_file(file)

    def save_to_file(self, file):
        with open(file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for step in self.step_widgets:
                writer.writerow([step.name_entry.get(), step.time])

    def open_file(self, event=None):
        file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file:
            self.load_from_file(file)

    def load_from_file(self, file):
        response = messagebox.askyesno("Load File", "Loading a new file will remove existing steps. Do you want to continue?")
        if response:
            for step in self.step_widgets:
                step.frame.destroy()
            self.step_widgets = []
            with open(file, 'r') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    step = Step(self.steps_frame, label=row[0])
                    step.time = int(row[1])
                    step.time_display.config(text=step.format_time(step.time))
                    step.frame.pack(fill=tk.X)
                    step.name_entry.bind("<FocusIn>", lambda e, s=step: self.select_step(s))
                    self.step_widgets.append(step)
            self.current_file = file

if __name__ == "__main__":
    root = tk.Tk()
    app = TimeStudyApp(root)
    root.mainloop()
