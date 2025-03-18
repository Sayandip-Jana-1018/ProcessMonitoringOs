import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import time
import os
import csv
import math  # Add this import for isnan function
from datetime import datetime
import matplotlib as mpl
import platform
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

from config import THEMES, DEFAULT_ALERT_THRESHOLDS, CUSTOM_STYLES
from ui.sections import TopSection, MiddleSection, BottomSection
from utils.process_utils import get_process_details, kill_process, change_process_priority
from utils.ai_utils import ResourcePredictor, AnomalyDetector
from ui.footer import Footer

# Set default font to avoid EUDC.TTE error
mpl.rcParams['font.family'] = 'DejaVu Sans'  # Use a single, reliable font
mpl.rcParams['axes.unicode_minus'] = False    # Fix minus sign display

class ProcessMonitorApp:
    def __init__(self, root):
        """Initialize the Process Monitor App"""
        self.root = root
        self.root.title("Advanced Process Monitoring Dashboard")
        self.root.geometry("1280x720")
        
        # Default theme
        self.current_theme = "dark"
        self.theme = THEMES[self.current_theme]
        
        # Configure ttk styles based on theme
        self.style = ttk.Style()
        self.configure_styles()
        
        # Set window background
        self.root.configure(bg=self.theme["bg"])
        
        # Create main frame to hold all content
        self.main_frame = ttk.Frame(self.root, style="TFrame")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize alert history and thresholds
        self.alert_history = []
        self.alert_thresholds = DEFAULT_ALERT_THRESHOLDS.copy()
        self.alert_active = False
        
        # Create refresh rate variable
        self.refresh_rate = tk.StringVar()
        self.refresh_rate.set("1")  # Default to 1 second
        
        # Create the UI components
        self.create_ui()
        
        # Initialize background tasks
        self.start_background_tasks()
        
        # Set up closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Data storage
        self.cpu_usage_history = []
        self.mem_usage_history = []
        self.disk_usage_history = []
        self.timestamps = []
        self.process_history = {}
        self.alerts = []  # Store alert history
        
        # Initialize AI components
        self.resource_predictor = ResourcePredictor()
        self.anomaly_detector = AnomalyDetector()
        self.recent_anomalies = []
        
        # Fix font issues
        mpl.rcParams['font.family'] = 'DejaVu Sans'
        mpl.rcParams['axes.unicode_minus'] = False
        
    def create_ui(self):
        """Create the main UI with improved layout that fits on screen"""
        # Create top section with horizontal gauges and side-by-side panels
        self.top_section = TopSection(self.main_frame, self)
        
        # Create a frame to hold the bottom two rows (process list and charts)
        content_container = ttk.Frame(self.main_frame, style="TFrame")
        content_container.pack(fill="both", expand=True, pady=(0, 0))
        
        # Split the space between process list and charts more efficiently
        content_container.columnconfigure(0, weight=1)  # Column for process list
        content_container.columnconfigure(1, weight=1)  # Column for performance graphs
        content_container.rowconfigure(0, weight=1)  # Row for both elements
        
        # Left side: Running Processes (first column)
        self.process_frame = ttk.Frame(content_container, style="Card.TFrame")
        self.process_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        
        # Process list header
        header_frame = ttk.Frame(self.process_frame, style="Card.TFrame")
        header_frame.pack(fill="x", padx=10, pady=5)  # Reduced padding
        
        # Title and process count
        title_frame = ttk.Frame(header_frame, style="Card.TFrame")
        title_frame.pack(side="left")
        
        title_label = ttk.Label(title_frame, 
                               text="RUNNING PROCESSES", 
                               style="Title.TLabel",
                               font=("Segoe UI", 12, "bold"))
        title_label.pack(side="left")
        
        self.process_count = ttk.Label(title_frame, 
                                     text="0 processes", 
                                     style="Info.TLabel")
        self.process_count.pack(side="left", padx=(15, 0))
        
        # Search box with icon
        search_frame = ttk.Frame(header_frame, style="Search.TFrame")
        search_frame.pack(side="right")
        
        search_icon = ttk.Label(search_frame, text="🔍", style="TLabel")
        search_icon.pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, 
                                    textvariable=self.filter_var,
                                    width=30)
        self.search_entry.pack(side="left", padx=(0, 5))
        
        # Process list container
        list_container = ttk.Frame(self.process_frame, style="Card.TFrame")
        list_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))  # Reduced padding
        
        # Process treeview
        columns = ("PID", "Name", "CPU%", "Memory", "Status")
        self.process_tree = ttk.Treeview(list_container, 
                                       columns=columns, 
                                       show="headings",
                                       style="Custom.Treeview")
        
        # Configure columns
        self.process_tree.heading("PID", text="PID")
        self.process_tree.heading("Name", text="Process Name")
        self.process_tree.heading("CPU%", text="CPU %")
        self.process_tree.heading("Memory", text="Memory (MB)")
        self.process_tree.heading("Status", text="Status")
        
        self.process_tree.column("PID", width=70, anchor="center")
        self.process_tree.column("Name", width=200)
        self.process_tree.column("CPU%", width=70, anchor="center")
        self.process_tree.column("Memory", width=100, anchor="center")
        self.process_tree.column("Status", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        self.process_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create the process controls at the bottom of the process list
        self.create_process_controls_panel(self.process_frame)
        
        # Right side container: Performance charts (second column)
        right_container = ttk.Frame(content_container, style="Card.TFrame")
        right_container.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        
        # Right side is split into upper and lower parts, give more space to Virtual Assistant
        right_container.rowconfigure(0, weight=2)  # Virtual Assistant (larger - 2/5 of height)
        right_container.rowconfigure(1, weight=3)  # System Performance (smaller - 3/5 of height)
        right_container.columnconfigure(0, weight=1)  # Both take full width
        
        # Upper right: Virtual Assistant (takes more height now)
        self.assistant_frame = ttk.Frame(right_container, style="Card.TFrame")
        self.assistant_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        self.create_virtual_assistant(self.assistant_frame)
        
        # Lower right: System Performance
        self.performance_frame = ttk.Frame(right_container, style="Card.TFrame")
        self.performance_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        self.create_performance_graphs(self.performance_frame)
        
        # Initialize data storage for history
        self.timestamps = []
        self.cpu_usage_history = []
        self.mem_usage_history = []
        self.disk_usage_history = []
        
        # Explicitly connect the filter_var to the update_process_list method
        self.filter_var.trace_add("write", self.on_filter_change)
        
        # Add a binding for process selection
        self.process_tree.bind("<ButtonRelease-1>", self.on_process_select)
        
        # Create a context menu for the process tree
        self.create_context_menu()
        
        # Initial update of the process list to populate it
        self.update_process_list()

    def configure_styles(self):
        """Configure ttk styles for modern look with custom button styles and transparency"""
        self.style.theme_use("default")
        
        # Apply custom styles from the config
        for style_name, style_config in CUSTOM_STYLES.items():
            # Process the style configuration to replace placeholders with theme values
            if "configure" in style_config:
                configure_args = {}
                for key, value in style_config["configure"].items():
                    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                        # Replace placeholder with theme value
                        theme_key = value[1:-1]  # Remove the { and }
                        if theme_key in self.theme:
                            configure_args[key] = self.theme[theme_key]
                    else:
                        configure_args[key] = value
                
                # Configure the style
                self.style.configure(style_name, **configure_args)
            
            # Process the style map configuration
            if "map" in style_config:
                map_args = {}
                for key, value_list in style_config["map"].items():
                    processed_list = []
                    for state, val in value_list:
                        if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
                            # Replace placeholder with theme value
                            theme_key = val[1:-1]  # Remove the { and }
                            if theme_key in self.theme:
                                processed_list.append((state, self.theme[theme_key]))
                        else:
                            processed_list.append((state, val))
                
                    map_args[key] = processed_list
                
                # Map the style
                self.style.map(style_name, **map_args)
        
        # Frame styles
        self.style.configure("TFrame", background=self.theme["bg"])
        self.style.configure("Card.TFrame", background=self.theme["card_bg"])
        
        # New transparent style for gauge area
        self.style.configure("TransparentCard.TFrame", background=self.theme["bg"])
        
        self.style.configure("Accent.TFrame", background=self.theme["accent"])
        
        # Button styles
        self.style.configure("TButton", 
                             background=self.theme["accent"],
                             foreground=self.theme["text"],
                             borderwidth=0)
        
        self.style.configure("Accent.TButton", 
                             background=self.theme["accent"],
                             foreground=self.theme["text"])
        
        self.style.configure("Danger.TButton", 
                             background=self.theme["danger"],
                             foreground=self.theme["text"])
        
        self.style.configure("Success.TButton", 
                             background=self.theme["success"],
                             foreground=self.theme["text"])
        
        # For the selected theme button
        self.style.configure("RoundedButtonSelected.TButton",
                             background=self.theme["accent"],
                             foreground=self.theme["bg"],
                             borderwidth=0,
                             focusthickness=0,
                             padding=(10, 5),
                             font=("Segoe UI", 9, "bold"))
        
        # Label styles
        self.style.configure("TLabel", 
                             background=self.theme["card_bg"],
                             foreground=self.theme["text"])
        
        self.style.configure("Title.TLabel", 
                             font=("Segoe UI", 14, "bold"),
                             background=self.theme["card_bg"],
                             foreground=self.theme["accent"])
        
        self.style.configure("InfoTitle.TLabel",
                             background=self.theme["card_bg"],
                             foreground=self.theme["accent"],
                             font=("Segoe UI", 10, "bold"))
        
        self.style.configure("Info.TLabel",
                             background=self.theme["card_bg"],
                             foreground=self.theme["text"],
                             font=("Segoe UI", 10))
        
        # Treeview styles with rounded corners
        self.style.configure("Treeview", 
                             background=self.theme["card_bg"],
                             foreground=self.theme["text"],
                             fieldbackground=self.theme["card_bg"])
        
        self.style.configure("Treeview.Heading", 
                             background=self.theme["accent"],
                             foreground=self.theme["text"],
                             font=("Segoe UI", 10, "bold"))
        
        # Remove borders from treeview
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        # Entry style
        self.style.configure("TEntry", 
                             fieldbackground=self.theme["bg"],
                             foreground=self.theme["text"])

    def toggle_theme(self):
        """Cycle through all available themes instead of just toggling"""
        # Get list of all theme keys
        theme_keys = list(THEMES.keys())
        
        # Find the index of the current theme
        current_index = theme_keys.index(self.current_theme)
        
        # Calculate next theme index (cycle through all themes)
        next_index = (current_index + 1) % len(theme_keys)
        
        # Set the new theme
        self.current_theme = theme_keys[next_index]
        self.theme = THEMES[self.current_theme]
        
        # Reconfigure the UI
        self.configure_styles()
        
        # Update theme icon on the button if it exists
        if hasattr(self.top_section, 'theme_btn'):
            self.top_section.theme_btn.config(text=THEMES[self.current_theme]["icon"])
        
        # Update plot colors
        self.top_section.update_gauge_colors(self.theme)
        
        # Update performance graph colors
        self.update_performance_graph_colors()
        
        # Update text widgets
        if hasattr(self.top_section, 'recommendations_content'):
            self.top_section.recommendations_content.config(bg=self.theme["card_bg"], fg=self.theme["text"])
        if hasattr(self.top_section, 'anomaly_text'):
            self.top_section.anomaly_text.config(bg=self.theme["card_bg"], fg=self.theme["text"])
        if hasattr(self, 'chat_display'):
            self.chat_display.config(bg=self.theme["card_bg"], fg=self.theme["text"])
        
        # Update backgrounds
        self.root.configure(bg=self.theme["bg"])
        
        # Force a redraw of the UI
        self.root.update()

    def start_background_tasks(self):
        """Start background data updating"""
        self.update_data()

    def update_data(self):
        """Update all data and UI elements"""
        try:
            # Get current CPU and memory usage
            cpu_percent = psutil.cpu_percent()
            mem_percent = psutil.virtual_memory().percent
            
            # Get disk usage for the main disk
            try:
                if platform.system() == 'Windows':
                    disk_percent = psutil.disk_usage('C:\\').percent
                else:
                    disk_percent = psutil.disk_usage('/').percent
            except Exception as e:
                print(f"Error getting disk usage: {e}")
                disk_percent = 50.0  # Default value if there's an error
            
            # Update history data
            current_time = datetime.now()
            
            # Initialize history lists if they don't exist
            if not hasattr(self, 'timestamps'):
                self.timestamps = []
            if not hasattr(self, 'cpu_usage_history'):
                self.cpu_usage_history = []
            if not hasattr(self, 'mem_usage_history'):
                self.mem_usage_history = []
            if not hasattr(self, 'disk_usage_history'):
                self.disk_usage_history = []
            
            # Add current data to history
            self.timestamps.append(current_time)
            self.cpu_usage_history.append(float(cpu_percent))
            self.mem_usage_history.append(float(mem_percent))
            self.disk_usage_history.append(float(disk_percent))
            
            # Keep only the last 3600 data points (1 hour at 1-second intervals)
            max_history = 3600
            if len(self.timestamps) > max_history:
                self.timestamps = self.timestamps[-max_history:]
                self.cpu_usage_history = self.cpu_usage_history[-max_history:]
                self.mem_usage_history = self.mem_usage_history[-max_history:]
                self.disk_usage_history = self.disk_usage_history[-max_history:]
            
            # Check for alerts
            self.check_alerts(cpu_percent, mem_percent, disk_percent)
            
            # Update gauges
            self.top_section.update_gauges(cpu_percent, mem_percent, disk_percent)
            
            # Update process list
            self.update_process_list()
            
            # Update AI components
            self.update_ai_components()
            
            # Update performance graphs - pass all required data
            if hasattr(self, 'middle_section') and len(self.timestamps) >= 2:
                self.middle_section.update_performance_graphs(
                    self.timestamps,
                    self.cpu_usage_history,
                    self.mem_usage_history,
                    self.disk_usage_history
                )
            
            # Schedule next update
            try:
                refresh_rate = int(self.refresh_rate.get()) * 1000  # Convert to milliseconds
            except (ValueError, AttributeError):
                refresh_rate = 1000  # Default to 1 second
            
            self.root.after(refresh_rate, self.update_data)
        except Exception as e:
            print(f"Error in update_data: {e}")
            # Ensure we reschedule the update even if there's an error
            self.root.after(1000, self.update_data)

    def check_alerts(self, cpu_percent, mem_percent, disk_percent=None):
        """Check if usage exceeds alert thresholds and log alerts"""
        current_time = datetime.now().strftime("%H:%M:%S")
        alert_triggered = False
        
        if cpu_percent > self.alert_thresholds["cpu"]:
            alert_msg = f"[{current_time}] WARNING: CPU usage at {cpu_percent:.1f}% exceeded threshold ({self.alert_thresholds['cpu']}%)"
            self.log_alert(alert_msg)
            alert_triggered = True
        
        if mem_percent > self.alert_thresholds["memory"]:
            alert_msg = f"[{current_time}] WARNING: Memory usage at {mem_percent:.1f}% exceeded threshold ({self.alert_thresholds['memory']}%)"
            self.log_alert(alert_msg)
            alert_triggered = True
        
        if disk_percent and disk_percent > self.alert_thresholds["disk"]:
            alert_msg = f"[{current_time}] WARNING: Disk usage at {disk_percent:.1f}% exceeded threshold ({self.alert_thresholds['disk']}%)"
            self.log_alert(alert_msg)
            alert_triggered = True
        
        # Show a popup for the first alert only to avoid spamming
        if alert_triggered and not hasattr(self, 'alert_shown'):
            messagebox.showwarning("System Alert", "Resource usage threshold exceeded.\nCheck the alerts panel for details.")
            self.alert_shown = True
            # Reset the alert flag after 60 seconds
            self.root.after(60000, self.reset_alert_flag)

    def reset_alert_flag(self):
        """Reset the alert flag to allow new popup alerts"""
        if hasattr(self, 'alert_shown'):
            delattr(self, 'alert_shown')

    def log_alert(self, message):
        """Add an alert to the alerts panel"""
        self.alerts.append(message)
        
        # Keep only the last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Update the alerts text widget
        self.middle_section.update_alerts_text(self.alerts)

    def kill_process(self):
        """Kill the selected process"""
        selected = self.middle_section.get_selected_process()
        
        # Debug print
        print(f"Kill process requested for: {selected}")
        
        if not selected:
            messagebox.showinfo("Info", "Please select a process to kill.")
            return
        
        try:
            pid = int(selected[0])
            process_name = selected[1]
            
            # Confirm before killing
            confirm = messagebox.askyesno(
                "Confirm Kill Process", 
                f"Are you sure you want to kill process '{process_name}' (PID: {pid})?"
            )
            
            if not confirm:
                return
            
            # Try to kill the process
            process = psutil.Process(pid)
            process.kill()
            
            # Wait briefly to confirm it's killed
            time.sleep(0.1)
            
            # Check if process still exists
            if psutil.pid_exists(pid):
                messagebox.showerror("Error", f"Failed to kill process {process_name} (PID: {pid})")
            else:
                messagebox.showinfo("Success", f"Process {process_name} (PID: {pid}) has been terminated")
                
                # Refresh the process list
                self.middle_section.update_process_list()
                
        except psutil.NoSuchProcess:
            messagebox.showinfo("Info", f"Process with PID {pid} no longer exists")
        except psutil.AccessDenied:
            messagebox.showerror("Error", f"Access denied when trying to kill process {process_name} (PID: {pid})")
        except Exception as e:
            messagebox.showerror("Error", f"Error killing process: {str(e)}")

    def change_priority(self, priority):
        """Change the priority of the selected process"""
        selected = self.middle_section.get_selected_process()
        if not selected:
            messagebox.showinfo("Info", "Please select a process to change priority.")
            return
        
        pid = int(selected[0])
        result, message = change_process_priority(pid, priority)
        
        if result:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def update_alert_thresholds(self):
        """Update alert thresholds"""
        try:
            # Validate thresholds
            cpu_threshold = int(self.cpu_threshold.get())
            mem_threshold = int(self.mem_threshold.get())
            disk_threshold = int(self.disk_threshold.get())
            
            if not (0 <= cpu_threshold <= 100):
                raise ValueError("CPU threshold must be between 0 and 100")
            if not (0 <= mem_threshold <= 100):
                raise ValueError("Memory threshold must be between 0 and 100")
            if not (0 <= disk_threshold <= 100):
                raise ValueError("Disk threshold must be between 0 and 100")
            
            # Update thresholds
            self.alert_thresholds = {
                "cpu": cpu_threshold,
                "memory": mem_threshold,
                "disk": disk_threshold
            }
            
            # Log the change
            self.log_alert(f"Alert thresholds updated: CPU {cpu_threshold}%, Memory {mem_threshold}%, Disk {disk_threshold}%")
        except ValueError as e:
            # Show error message
            messagebox.showerror("Invalid Threshold", str(e))

    def show_process_details(self):
        """Show detailed information about the selected process"""
        # Get the selected process - use our own method since we're in app.py
        selected = self.get_selected_process()
        
        # Debug print to verify what we're getting
        print(f"Process details requested for: {selected}")
        
        if not selected:
            messagebox.showinfo("Info", "Please select a process to view details.")
            return
        
        try:
            # Make sure we have a valid PID
            pid = int(selected[0])
            process_name = selected[1]
            
            # Create a details window
            details_window = tk.Toplevel(self.root)
            details_window.title(f"Process Details: {process_name} (PID: {pid})")
            details_window.geometry("600x500")
            details_window.configure(bg=self.theme["bg"])
            details_window.transient(self.root)  # Make it a transient window
            
            # Create a frame for the details
            details_frame = ttk.Frame(details_window, style="Card.TFrame")
            details_frame.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Add a title
            title_label = ttk.Label(details_frame, 
                                   text=f"PROCESS DETAILS: {process_name.upper()}", 
                                   style="Title.TLabel",
                                   font=("Segoe UI", 14, "bold"))
            title_label.pack(pady=(0, 15), anchor="w")
            
            # Create a notebook for tabs
            details_notebook = ttk.Notebook(details_frame)
            details_notebook.pack(fill="both", expand=True)
            
            # Basic Info Tab
            basic_tab = ttk.Frame(details_notebook, style="Card.TFrame")
            details_notebook.add(basic_tab, text="Basic Info")
            
            # Performance Tab
            perf_tab = ttk.Frame(details_notebook, style="Card.TFrame")
            details_notebook.add(perf_tab, text="Performance")
            
            # Files Tab
            files_tab = ttk.Frame(details_notebook, style="Card.TFrame")
            details_notebook.add(files_tab, text="Files")
            
            # Get process details
            try:
                process = psutil.Process(pid)
                
                # Basic Info Tab Content
                basic_frame = ttk.Frame(basic_tab, style="Card.TFrame")
                basic_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Create a grid for basic info
                row = 0
                for label, value in [
                    ("PID", pid),
                    ("Name", process.name()),
                    ("Status", process.status()),
                    ("Created", datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')),
                    ("Username", process.username()),
                    ("Terminal", getattr(process, 'terminal', lambda: 'N/A')()),
                    ("Command Line", " ".join(process.cmdline()) if process.cmdline() else "N/A"),
                    ("Executable", process.exe()),
                    ("Current Working Directory", process.cwd()),
                    ("CPU Affinity", ", ".join(map(str, process.cpu_affinity())) if hasattr(process, 'cpu_affinity') else "N/A"),
                    ("Nice Value", process.nice()),
                    ("Number of Threads", process.num_threads()),
                    ("Parent PID", process.ppid()),
                ]:
                    title = ttk.Label(basic_frame, text=f"{label}:", style="InfoTitle.TLabel", width=20, anchor="e")
                    title.grid(row=row, column=0, padx=(0, 10), pady=5, sticky="e")
                    
                    value_label = ttk.Label(basic_frame, text=str(value), style="Info.TLabel", wraplength=400)
                    value_label.grid(row=row, column=1, pady=5, sticky="w")
                    
                    row += 1
                
                # Performance Tab Content
                perf_frame = ttk.Frame(perf_tab, style="Card.TFrame")
                perf_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Memory info
                mem_info = process.memory_info()
                mem_frame = ttk.LabelFrame(perf_frame, text="Memory Usage", style="Card.TFrame")
                mem_frame.pack(fill="x", pady=10)
                
                row = 0
                for label, value in [
                    ("RSS (Physical Memory)", f"{mem_info.rss / (1024**2):.2f} MB"),
                    ("VMS (Virtual Memory)", f"{mem_info.vms / (1024**2):.2f} MB"),
                    ("Shared", f"{getattr(mem_info, 'shared', 0) / (1024**2):.2f} MB"),
                    ("Text", f"{getattr(mem_info, 'text', 0) / (1024**2):.2f} MB"),
                    ("Data", f"{getattr(mem_info, 'data', 0) / (1024**2):.2f} MB"),
                ]:
                    title = ttk.Label(mem_frame, text=f"{label}:", style="InfoTitle.TLabel", width=20, anchor="e")
                    title.grid(row=row, column=0, padx=(10, 10), pady=5, sticky="e")
                    
                    value_label = ttk.Label(mem_frame, text=str(value), style="Info.TLabel")
                    value_label.grid(row=row, column=1, pady=5, sticky="w")
                    
                    row += 1
                
                # CPU info
                cpu_frame = ttk.LabelFrame(perf_frame, text="CPU Usage", style="Card.TFrame")
                cpu_frame.pack(fill="x", pady=10)
                
                cpu_percent = process.cpu_percent(interval=0.1)
                cpu_times = process.cpu_times()
                
                row = 0
                for label, value in [
                    ("CPU Usage", f"{cpu_percent:.2f}%"),
                    ("User Time", f"{cpu_times.user:.2f} seconds"),
                    ("System Time", f"{cpu_times.system:.2f} seconds"),
                    ("Children User Time", f"{getattr(cpu_times, 'children_user', 0):.2f} seconds"),
                    ("Children System Time", f"{getattr(cpu_times, 'children_system', 0):.2f} seconds"),
                ]:
                    title = ttk.Label(cpu_frame, text=f"{label}:", style="InfoTitle.TLabel", width=20, anchor="e")
                    title.grid(row=row, column=0, padx=(10, 10), pady=5, sticky="e")
                    
                    value_label = ttk.Label(cpu_frame, text=str(value), style="Info.TLabel")
                    value_label.grid(row=row, column=1, pady=5, sticky="w")
                    
                    row += 1
                
                # IO info
                io_frame = ttk.LabelFrame(perf_frame, text="I/O Statistics", style="Card.TFrame")
                io_frame.pack(fill="x", pady=10)
                
                try:
                    io_counters = process.io_counters()
                    
                    row = 0
                    for label, value in [
                        ("Read Count", io_counters.read_count),
                        ("Write Count", io_counters.write_count),
                        ("Read Bytes", f"{io_counters.read_bytes / (1024**2):.2f} MB"),
                        ("Write Bytes", f"{io_counters.write_bytes / (1024**2):.2f} MB"),
                    ]:
                        title = ttk.Label(io_frame, text=f"{label}:", style="InfoTitle.TLabel", width=20, anchor="e")
                        title.grid(row=row, column=0, padx=(10, 10), pady=5, sticky="e")
                        
                        value_label = ttk.Label(io_frame, text=str(value), style="Info.TLabel")
                        value_label.grid(row=row, column=1, pady=5, sticky="w")
                        
                        row += 1
                except:
                    ttk.Label(io_frame, text="I/O statistics not available for this process", style="Info.TLabel").pack(padx=10, pady=10)
                
                # Files Tab Content
                files_frame = ttk.Frame(files_tab, style="Card.TFrame")
                files_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Open files
                try:
                    open_files = process.open_files()
                    
                    if open_files:
                        ttk.Label(files_frame, text="Open Files:", style="Title.TLabel").pack(anchor="w", pady=(0, 5))
                        
                        # Create a treeview for open files
                        files_tree = ttk.Treeview(files_frame, columns=("path", "fd", "position", "mode", "flags"), show="headings", height=10)
                        files_tree.pack(fill="both", expand=True)
                        
                        # Configure columns
                        files_tree.heading("path", text="Path")
                        files_tree.heading("fd", text="File Descriptor")
                        files_tree.heading("position", text="Position")
                        files_tree.heading("mode", text="Mode")
                        files_tree.heading("flags", text="Flags")
                        
                        files_tree.column("path", width=300)
                        files_tree.column("fd", width=50)
                        files_tree.column("position", width=70)
                        files_tree.column("mode", width=70)
                        files_tree.column("flags", width=70)
                        
                        # Add files to treeview
                        for file in open_files:
                            files_tree.insert("", "end", values=(
                                file.path,
                                getattr(file, 'fd', 'N/A'),
                                getattr(file, 'position', 'N/A'),
                                getattr(file, 'mode', 'N/A'),
                                getattr(file, 'flags', 'N/A')
                            ))
                    else:
                        ttk.Label(files_frame, text="No open files found", style="Info.TLabel").pack(padx=10, pady=10)
                except:
                    ttk.Label(files_frame, text="Open files information not available for this process", style="Info.TLabel").pack(padx=10, pady=10)
                
                # Add a refresh button
                refresh_btn = ttk.Button(
                    details_frame, 
                    text="Refresh", 
                    command=lambda: self.refresh_process_details(details_window, pid, process_name),
                    style="Accent.TButton"
                )
                refresh_btn.pack(pady=10)
                
            except psutil.NoSuchProcess:
                ttk.Label(basic_tab, text=f"Process with PID {pid} no longer exists", style="Info.TLabel").pack(padx=20, pady=20)
            except psutil.AccessDenied:
                ttk.Label(basic_tab, text=f"Access denied to process with PID {pid}", style="Info.TLabel").pack(padx=20, pady=20)
            except Exception as e:
                ttk.Label(basic_tab, text=f"Error retrieving process details: {str(e)}", style="Info.TLabel").pack(padx=20, pady=20)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show process details: {str(e)}")

    def refresh_process_details(self, window, pid, name):
        """Refresh the process details window"""
        # Close the current window
        window.destroy()
        
        # Open a new details window
        self.show_process_details()

    def export_process_list(self):
        """Export the current process list to a CSV file"""
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Process List"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            processes = self.middle_section.get_all_processes()
            
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["PID", "Name", "CPU%", "Memory (MB)", "Status"])
                
                # Write data
                for process in processes:
                    writer.writerow(process)
            
            messagebox.showinfo("Success", f"Process list exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
        
    def on_closing(self):
        """Handle window closing"""
        self.root.destroy() 

    def update_ai_components(self):
        """Update AI components with new data"""
        # Get predictions if we have enough data
        predictions = self.resource_predictor.get_predictions(
            self.cpu_usage_history,
            self.mem_usage_history,
            self.disk_usage_history
        )
        
        # Train or update anomaly detection model if needed
        if self.anomaly_detector.should_train(len(self.cpu_usage_history)):
            self.anomaly_detector.train(
                self.cpu_usage_history,
                self.mem_usage_history,
                self.disk_usage_history
            )
        
        # Detect anomalies in current data
        anomaly_result = None
        if self.anomaly_detector.is_trained:
            anomaly_result = self.anomaly_detector.detect_anomalies(
                self.cpu_usage_history,
                self.mem_usage_history,
                self.disk_usage_history
            )
            
            # Log anomaly if detected
            if anomaly_result and anomaly_result['is_anomaly']:
                anomaly_msg = (
                    f"[{anomaly_result['detection_time']}] ANOMALY DETECTED: "
                    f"CPU {anomaly_result['cpu']:.1f}%, "
                    f"MEM {anomaly_result['memory']:.1f}%, "
                    f"DISK {anomaly_result['disk']:.1f}%"
                )
                self.recent_anomalies.append(anomaly_msg)
                self.log_alert(anomaly_msg)
                
                # Keep only the last 20 anomalies
                if len(self.recent_anomalies) > 20:
                    self.recent_anomalies = self.recent_anomalies[-20:]
        
        # Update the AI panels in the UI
        self.top_section.update_ai_insights(predictions, anomaly_result, self.recent_anomalies)
        self.middle_section.update_detailed_ai_insights(predictions, anomaly_result, self.recent_anomalies)

    def refresh_ui(self):
        """Refresh the UI components"""
        # Clear the main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Recreate the UI
        self.create_ui()
        
        # Force an immediate data update
        self.update_data()

    def update_performance_graphs(self):
        """Update the performance graphs with real-time data"""
        try:
            if not hasattr(self, 'perf_axes') or not self.perf_axes or len(self.perf_axes) < 3:
                print("Performance axes not initialized correctly")
                return
            
            # Get the timestamps and history data
            timestamps = self.timestamps
            cpu_history = self.cpu_usage_history
            mem_history = self.mem_usage_history
            disk_history = self.disk_usage_history
            
            # Clear "Collecting data..." text from all subplots
            for ax in self.perf_axes:
                for txt in ax.texts:
                    txt.remove()
            
            # Check if we have enough data to display
            if not timestamps or len(timestamps) < 2:
                # Not enough data yet, show "Collecting data..." message
                for ax in self.perf_axes:
                    ax.text(0.5, 0.5, "Collecting data...", 
                            horizontalalignment='center',
                            verticalalignment='center',
                            transform=ax.transAxes,
                            color=self.theme["text"],
                            fontsize=10)
                self.perf_fig.tight_layout()
                self.perf_canvas.draw()
                return
            
            # Make sure data lengths match
            min_length = min(len(timestamps), len(cpu_history), len(mem_history), len(disk_history))
            if min_length < 2:
                # Still collecting enough data
                return
            
            # Get time range selection
            time_range_text = self.time_range.get() if hasattr(self, 'time_range') else "5 minutes"
            
            # Convert time range to number of data points (assuming 1 second updates)
            if time_range_text == "5 minutes":
                num_points = 5 * 60
            elif time_range_text == "15 minutes":
                num_points = 15 * 60
            else:  # 1 hour
                num_points = 60 * 60
            
            # Limit data to the selected time range
            if len(timestamps) > num_points:
                timestamps = timestamps[-num_points:]
                cpu_history = cpu_history[-num_points:]
                mem_history = mem_history[-num_points:]
                disk_history = disk_history[-num_points:]
            
            # Clear all axes
            for ax in self.perf_axes:
                ax.clear()
            
            # Use indices for x-axis to prevent matplotlib issues
            x_indices = list(range(len(timestamps)))
            
            # Define vibrant colors for better visibility
            cpu_color = "#FF5555"  # Bright red
            mem_color = "#5555FF"  # Bright blue
            disk_color = "#55FF55"  # Bright green
            
            # Configure axis titles and styling
            self.perf_axes[0].set_title("CPU Usage (%)", color=self.theme["text"], fontsize=9)
            self.perf_axes[1].set_title("Memory Usage (%)", color=self.theme["text"], fontsize=9)
            self.perf_axes[2].set_title("Disk Usage (%)", color=self.theme["text"], fontsize=9)
            
            # Configure each axis with proper styling
            for ax in self.perf_axes:
                ax.set_facecolor(self.theme["chart_bg"])
                ax.set_ylim(0, 100)  # Usage percentage 0-100%
                ax.grid(True, linestyle='--', alpha=0.6, color=self.theme["grid_color"])
                ax.tick_params(colors=self.theme["text"], labelsize=8)
            
            # Format timestamps for display on x-axis
            # Show a few evenly spaced labels
            if len(timestamps) > 0:
                num_labels = min(5, len(timestamps))
                step = max(1, len(timestamps) // num_labels)
                positions = [x_indices[i] for i in range(0, len(x_indices), step)]
                
                if positions:  # Ensure we have positions before creating labels
                    labels = [timestamps[i].strftime("%H:%M:%S") for i in range(0, len(timestamps), step)]
                    
                    for ax in self.perf_axes:
                        ax.set_xticks(positions)
                        ax.set_xticklabels(labels, rotation=45, ha='right')
            
            # Plot the data with filled areas
            if len(cpu_history) > 0:
                # CPU Usage plot
                self.perf_axes[0].plot(x_indices, cpu_history, color=cpu_color, linewidth=2)
                self.perf_axes[0].fill_between(x_indices, 0, cpu_history, color=cpu_color, alpha=0.3)
                
                # Memory Usage plot
                self.perf_axes[1].plot(x_indices, mem_history, color=mem_color, linewidth=2)
                self.perf_axes[1].fill_between(x_indices, 0, mem_history, color=mem_color, alpha=0.3)
                
                # Disk Usage plot
                self.perf_axes[2].plot(x_indices, disk_history, color=disk_color, linewidth=2)
                self.perf_axes[2].fill_between(x_indices, 0, disk_history, color=disk_color, alpha=0.3)
            
            # Apply tight layout to adjust spacing between subplots
            self.perf_fig.tight_layout()
            
            # Draw the updated figure
            self.perf_canvas.draw()
            
        except Exception as e:
            print(f"Error updating performance graphs: {e}")
            import traceback
            traceback.print_exc()

    def create_virtual_assistant(self, parent):
        """Create the Virtual Assistant section with minimum height"""
        # Set minimum height for virtual assistant section
        parent.pack_propagate(False)
        
        # Ensure there's a minimum height for the assistant frame
        min_height = 150
        current_height = parent.winfo_height()
        if current_height < min_height:
            parent.configure(height=min_height)
        
        # Title and assistant in the same row to save vertical space
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Title on left
        assistant_title = ttk.Label(header_frame,
                                  text="VIRTUAL ASSISTANT",
                                  style="Title.TLabel",
                                  font=("Segoe UI", 12, "bold"))
        assistant_title.pack(side="left")
        
        # Assistant content
        assistant_content = ttk.Frame(parent, style="Card.TFrame")
        assistant_content.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Chat display with increased height
        self.chat_display = tk.Text(
            assistant_content,
            height=6,  # Increased height for better visibility
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            font=("Segoe UI", 9),
            wrap="word"
        )
        
        # Add scrollbar to ensure content is accessible
        chat_scrollbar = ttk.Scrollbar(assistant_content, orient="vertical", command=self.chat_display.yview)
        self.chat_display.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_display.pack(side="left", fill="both", expand=True)
        chat_scrollbar.pack(side="right", fill="y")
        
        self.chat_display.config(state="disabled")
        
        # Initial welcome message
        self.update_chat_display("Assistant: Hello! I can help you monitor your system. Ask me questions like 'What's using the most CPU?' or 'How much memory do I have?'")
        
        # Input area in a separate frame
        input_frame = ttk.Frame(parent, style="Card.TFrame")
        input_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.user_input = ttk.Entry(input_frame, width=30)
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.process_user_input)
        
        send_btn = ttk.Button(input_frame,
                             text="Ask",
                             command=self.process_user_input,
                             style="Accent.TButton")
        send_btn.pack(side="right")

    def process_user_input(self, event=None):
        """Process user input from the virtual assistant"""
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        
        # Display user query
        self.update_chat_display(f"You: {user_text}")
        
        # Clear input box
        self.user_input.delete(0, tk.END)
        
        # Process query and generate response
        response = self.generate_assistant_response(user_text)
        
        # Display assistant response
        self.update_chat_display(f"Assistant: {response}")

    def update_chat_display(self, message):
        """Update the chat display with a new message"""
        self.chat_display.config(state="normal")
        
        # Add timestamp
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Add message with timestamp
        if self.chat_display.get("1.0", tk.END).strip():
            self.chat_display.insert(tk.END, f"\n\n[{current_time}] {message}")
        else:
            self.chat_display.insert(tk.END, f"[{current_time}] {message}")
        
        # Scroll to the end
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def generate_assistant_response(self, query):
        """Generate a response based on the user's query"""
        query = query.lower()
        
        # CPU related queries
        if "cpu" in query:
            if "most" in query or "top" in query:
                # Get top CPU consuming process
                try:
                    processes = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                        try:
                            processes.append((proc.info['pid'], proc.info['name'], proc.info['cpu_percent']))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    processes.sort(key=lambda x: x[2], reverse=True)
                    if processes:
                        top_proc = processes[0]
                        return f"The process using the most CPU is {top_proc[1]} (PID: {top_proc[0]}) at {top_proc[2]:.1f}%"
                    else:
                        return "I couldn't retrieve the top CPU consuming process."
                except Exception as e:
                    return f"I encountered an error while checking CPU usage: {str(e)}"
            else:
                # General CPU info
                try:
                    cpu_percent = psutil.cpu_percent()
                    cpu_count = psutil.cpu_count()
                    physical_cores = psutil.cpu_count(logical=False)
                    
                    return f"CPU usage is currently at {cpu_percent:.1f}%. You have {physical_cores} physical cores and {cpu_count} logical processors."
                except Exception as e:
                    return f"I encountered an error while checking CPU info: {str(e)}"
        
        # Memory related queries
        elif "memory" in query or "ram" in query:
            try:
                mem = psutil.virtual_memory()
                mem_total_gb = mem.total / (1024**3)
                mem_used_gb = mem.used / (1024**3)
                mem_percent = mem.percent
                
                return f"You have {mem_total_gb:.1f} GB of RAM, with {mem_used_gb:.1f} GB ({mem_percent:.1f}%) currently in use."
            except Exception as e:
                return f"I encountered an error while checking memory: {str(e)}"
        
        # Disk related queries
        elif "disk" in query or "storage" in query or "space" in query:
            try:
                if platform.system() == 'Windows':
                    drive = 'C:\\'
                else:
                    drive = '/'
                
                disk = psutil.disk_usage(drive)
                disk_total_gb = disk.total / (1024**3)
                disk_used_gb = disk.used / (1024**3)
                disk_free_gb = disk.free / (1024**3)
                disk_percent = disk.percent
                
                return f"Your main disk has {disk_total_gb:.1f} GB total space, with {disk_used_gb:.1f} GB used ({disk_percent:.1f}%) and {disk_free_gb:.1f} GB free."
            except Exception as e:
                return f"I encountered an error while checking disk space: {str(e)}"
        
        # Process related queries
        elif "process" in query or "running" in query:
            try:
                process_count = len(list(psutil.process_iter()))
                return f"There are currently {process_count} processes running on your system."
            except Exception as e:
                return f"I encountered an error while checking processes: {str(e)}"
        
        # System uptime
        elif "uptime" in query or "how long" in query:
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                
                days, remainder = divmod(uptime_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                uptime_str = ""
                if days > 0:
                    uptime_str += f"{int(days)} days, "
                if hours > 0 or days > 0:
                    uptime_str += f"{int(hours)} hours, "
                if minutes > 0 or hours > 0 or days > 0:
                    uptime_str += f"{int(minutes)} minutes, "
                uptime_str += f"{int(seconds)} seconds"
                
                return f"Your system has been running for {uptime_str}."
            except Exception as e:
                return f"I encountered an error while checking uptime: {str(e)}"
        
        # Help command
        elif "help" in query or "what can you do" in query:
            return "I can provide information about your system. Try asking me about CPU usage, memory, disk space, running processes, or system uptime."
        
        # If we don't recognize the query
        else:
            return "I'm not sure how to answer that. Try asking about CPU usage, memory, disk space, running processes, or system uptime." 

    def create_process_controls_panel(self, parent):
        """Create a more compact process controls panel"""
        # Create a frame for the controls panel
        controls_panel = ttk.Frame(parent, style="Card.TFrame")
        controls_panel.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Create a single row for essential controls
        controls_row = ttk.Frame(controls_panel, style="Card.TFrame")
        controls_row.pack(fill="x")
        
        # Process control buttons (left side)
        button_frame = ttk.Frame(controls_row, style="Card.TFrame")
        button_frame.pack(side="left")
        
        # Kill Process button (smaller)
        kill_btn = ttk.Button(button_frame, 
                             text="Kill Process", 
                             command=self.kill_process,
                             style="Danger.TButton",
                             width=10)
        kill_btn.pack(side="left", padx=2)
        
        # Process Details button (smaller)
        details_btn = ttk.Button(button_frame, 
                                text="Details", 
                                command=self.show_process_details,
                                style="Accent.TButton",
                                width=6)
        details_btn.pack(side="left", padx=2)
        
        # System info (right side)
        self.system_info_label = ttk.Label(
            controls_row, 
            text="Processes: -- | Memory: -- MB | CPU Avg: --%", 
            style="TLabel"
        )
        self.system_info_label.pack(side="right", padx=5)

    def update_process_list(self):
        """Update the process list with current processes - with proper filtering"""
        try:
            # Get filter text
            filter_text = self.filter_var.get().lower()
            print(f"Filtering with: '{filter_text}'")  # Debug print
            
            # Clear existing items
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            # Get process list
            processes = []
            total_processes = 0
            visible_processes = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    total_processes += 1
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    
                    # Apply filter if text is provided
                    if not filter_text or filter_text in proc_name:
                        processes.append((
                            proc_info['pid'],
                            proc_info['name'],
                            f"{proc_info['cpu_percent']:.1f}",
                            f"{proc_info['memory_info'].rss / (1024 * 1024):.1f}",  # Convert to MB
                            proc_info['status']
                        ))
                        visible_processes += 1
                    
                    # Limit to 100 processes for better performance
                    if visible_processes >= 100 and not filter_text:
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    pass
            
            # Sort processes by CPU usage
            processes.sort(key=lambda x: float(x[2]), reverse=True)
            
            # Insert into treeview
            for proc in processes:
                self.process_tree.insert('', 'end', values=proc)
            
            # Update process count
            count_text = f"{visible_processes} of {total_processes} processes"
            if filter_text:
                count_text = f"{visible_processes} matches (filter: '{filter_text}') of {total_processes} processes"
            
            self.process_count.config(text=count_text)
            
            # Update the system info label
            self.update_system_info_label()
        except Exception as e:
            print(f"Error updating process list: {e}")

    def update_system_info_label(self):
        """Update the system information label at the bottom of the process list"""
        try:
            # Get all processes
            processes = list(psutil.process_iter(['pid', 'name', 'status', 'memory_info']))
            
            # Count processes
            total_processes = len(processes)
            
            # Calculate total memory usage
            total_memory = sum(p.info['memory_info'].rss for p in processes if p.info['memory_info'])
            total_memory_mb = total_memory / (1024 * 1024)
            
            # Calculate average CPU usage
            avg_cpu = sum(self.cpu_usage_history[-10:]) / min(10, len(self.cpu_usage_history)) if self.cpu_usage_history else 0
            
            # Update the system info label
            self.system_info_label.config(
                text=f"Processes: {total_processes} | Memory: {total_memory_mb:.1f} MB | CPU Avg: {avg_cpu:.1f}%"
            )
        except Exception as e:
            # Graceful error handling
            print(f"Error updating system info label: {e}")
            self.system_info_label.config(text="Processes: -- | Memory: -- MB | CPU Avg: --%")

    def on_process_select(self, event):
        """Handle process selection"""
        # Get the selected item
        selected = self.process_tree.selection()
        if selected:
            # Store the selected process info for quick access
            self.selected_process = self.process_tree.item(selected[0])['values']
        else:
            self.selected_process = None

    def create_context_menu(self):
        """Create a right-click context menu for the process list"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=self.theme["card_bg"], fg=self.theme["text"])
        self.context_menu.add_command(label="Kill Process", command=self.kill_process)
        self.context_menu.add_command(label="Process Details", command=self.show_process_details)
        self.context_menu.add_separator()
        
        # Priority submenu
        priority_menu = tk.Menu(self.context_menu, tearoff=0, bg=self.theme["card_bg"], fg=self.theme["text"])
        priority_menu.add_command(label="High", command=lambda: self.change_priority(-10))
        priority_menu.add_command(label="Normal", command=lambda: self.change_priority(0))
        priority_menu.add_command(label="Low", command=lambda: self.change_priority(19))
        self.context_menu.add_cascade(label="Set Priority", menu=priority_menu)
        
        # Bind right-click to show context menu
        self.process_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show the context menu on right-click"""
        # Select the item under the cursor
        item = self.process_tree.identify_row(event.y)
        if item:
            self.process_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def get_selected_process(self):
        """Get the selected process from the treeview"""
        selected = self.process_tree.selection()
        if not selected:
            return None
        
        # Get the values from the selected item
        values = self.process_tree.item(selected[0])['values']
        
        # Debug print to verify we're getting values
        print(f"Selected process: {values}")
        
        # Make sure we have values before returning
        if values and len(values) >= 5:
            return values
        return None

    def create_performance_graphs(self, parent):
        """Create performance graphs section with proper theme colors"""
        # Graph header with title and time range in the same row
        graph_header = ttk.Frame(parent, style="Card.TFrame")
        graph_header.pack(fill="x", padx=10, pady=5)
        
        graph_title = ttk.Label(graph_header, 
                               text="SYSTEM PERFORMANCE", 
                               style="Title.TLabel",
                               font=("Segoe UI", 12, "bold"))
        graph_title.pack(side="left")
        
        # Time range selector with callback
        time_frame = ttk.Frame(graph_header, style="Card.TFrame")
        time_frame.pack(side="right")
        
        time_label = ttk.Label(time_frame, text="Time Range:", style="TLabel")
        time_label.pack(side="left", padx=(0, 5))
        
        self.time_range = ttk.Combobox(time_frame,
                                      values=["5 minutes", "15 minutes", "1 hour"],
                                      width=10,
                                      state="readonly")
        self.time_range.set("5 minutes")
        self.time_range.pack(side="left")
        
        # Add binding to update graphs when time range changes
        self.time_range.bind("<<ComboboxSelected>>", self.on_time_range_change)
        
        # Graph container
        graph_container = ttk.Frame(parent, style="Card.TFrame")
        graph_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Create figure and subplots with more compact sizing
        self.perf_fig = plt.Figure(figsize=(5, 5), dpi=100)
        self.perf_fig.patch.set_facecolor(self.theme["card_bg"])  # Ensure background matches theme
        
        # Use tighter spacing between subplots
        self.perf_fig.subplots_adjust(hspace=0.4)
        
        # Create three subplots for CPU, memory, and disk
        self.perf_axes = []
        
        # CPU subplot
        cpu_ax = self.perf_fig.add_subplot(311)
        cpu_ax.set_facecolor(self.theme["chart_bg"])  # Match chart background to theme
        cpu_ax.set_title("CPU Usage (%)", color=self.theme["text"], fontsize=9)
        cpu_ax.set_ylim(0, 100)
        cpu_ax.grid(True, linestyle='--', alpha=0.6, color=self.theme["grid_color"])
        cpu_ax.tick_params(colors=self.theme["text"], labelsize=8)
        self.perf_axes.append(cpu_ax)
        
        # Memory subplot
        mem_ax = self.perf_fig.add_subplot(312)
        mem_ax.set_facecolor(self.theme["chart_bg"])  # Match chart background to theme
        mem_ax.set_title("Memory Usage (%)", color=self.theme["text"], fontsize=9)
        mem_ax.set_ylim(0, 100)
        mem_ax.grid(True, linestyle='--', alpha=0.6, color=self.theme["grid_color"])
        mem_ax.tick_params(colors=self.theme["text"], labelsize=8)
        self.perf_axes.append(mem_ax)
        
        # Disk subplot
        disk_ax = self.perf_fig.add_subplot(313)
        disk_ax.set_facecolor(self.theme["chart_bg"])  # Match chart background to theme
        disk_ax.set_title("Disk Usage (%)", color=self.theme["text"], fontsize=9)
        disk_ax.set_ylim(0, 100)
        disk_ax.grid(True, linestyle='--', alpha=0.6, color=self.theme["grid_color"])
        disk_ax.tick_params(colors=self.theme["text"], labelsize=8)
        self.perf_axes.append(disk_ax)
        
        # Create canvas with the figure
        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, graph_container)
        self.perf_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Initial plot with empty data to ensure axes are visible
        self._initialize_empty_plots()

    def _initialize_empty_plots(self):
        """Initialize empty plots with proper styling"""
        try:
            if hasattr(self, 'perf_axes'):
                for i, ax in enumerate(self.perf_axes):
                    # Clear the axis
                    ax.clear()
                    
                    # Set facecolor and grid
                    ax.set_facecolor(self.theme["chart_bg"])
                    ax.grid(True, linestyle='--', alpha=0.6, color=self.theme["grid_color"])
                    
                    # Set y-axis limits for percentage display
                    ax.set_ylim(0, 100)
                    
                    # Set title based on index
                    if i == 0:
                        title = "CPU Usage (%)"
                    elif i == 1:
                        title = "Memory Usage (%)"
                    else:
                        title = "Disk Usage (%)"
                    
                    ax.set_title(title, color=self.theme["text"], fontsize=9)
                    
                    # Add "Collecting data..." text
                    ax.text(0.5, 0.5, "Collecting data...", 
                            horizontalalignment='center',
                            verticalalignment='center',
                            transform=ax.transAxes,
                            color=self.theme["text"],
                            fontsize=10)
                    
                    # Set tick colors
                    ax.tick_params(colors=self.theme["text"], labelsize=8)
                
                # Apply tight layout and draw
                self.perf_fig.tight_layout()
                self.perf_canvas.draw()
        except Exception as e:
            print(f"Error initializing empty plots: {e}")

    def on_time_range_change(self, event=None):
        """Handle time range selection change"""
        # Update the performance graphs with the new time range
        self.update_performance_graphs()

    def update_performance_graph_colors(self):
        """Update the performance graph colors to match the current theme"""
        try:
            if not hasattr(self, 'perf_fig') or not hasattr(self, 'perf_axes'):
                return
            
            # Update figure background
            self.perf_fig.patch.set_facecolor(self.theme["card_bg"])
            
            # Update axes styling
            for i, ax in enumerate(self.perf_axes):
                ax.set_facecolor(self.theme["chart_bg"])
                
                # Update grid color
                ax.grid(color=self.theme["grid_color"], linestyle='--', alpha=0.6)
                
                # Update text colors
                ax.tick_params(colors=self.theme["text"])
                
                # Update title color
                title = ax.get_title()
                if title:
                    if i == 0:
                        ax.set_title(title, color=self.theme["text"])
                    elif i == 1:
                        ax.set_title(title, color=self.theme["text"])
                    elif i == 2:
                        ax.set_title(title, color=self.theme["text"])
            
            # Redraw the canvas
            if hasattr(self, 'perf_canvas'):
                self.perf_canvas.draw()
        except Exception as e:
            print(f"Error updating performance graph colors: {e}")

    def refresh_dashboard(self):
        """Refresh the entire dashboard"""
        try:
            # Show a loading message
            loading_window = tk.Toplevel(self.root)
            loading_window.title("Refreshing Dashboard")
            loading_window.geometry("300x100")
            loading_window.transient(self.root)
            loading_window.grab_set()
            
            loading_label = ttk.Label(loading_window, 
                                     text="Refreshing dashboard...\nPlease wait.",
                                     font=("Segoe UI", 12))
            loading_label.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Update the UI to show the loading window
            self.root.update()
            
            # Explicitly refresh system info
            self.top_section.update_system_info()
            
            # Force update of all data
            self.update_data()
            
            # Update performance graphs
            self.update_performance_graphs()
            
            # Show success message
            loading_label.config(text="Dashboard refreshed successfully!")
            self.root.after(1000, loading_window.destroy)
            
        except Exception as e:
            # Show error message if refresh fails
            messagebox.showerror("Refresh Error", f"Error refreshing dashboard: {str(e)}")
            print(f"Error in refresh_dashboard: {e}")

    def show_settings_dialog(self):
        """Show the settings dialog with features overview"""
        try:
            # Create a dialog window
            settings_dialog = tk.Toplevel(self.root)
            settings_dialog.title("Dashboard Features")
            settings_dialog.geometry("600x500")
            settings_dialog.configure(bg=self.theme["bg"])
            settings_dialog.transient(self.root)  # Make it a transient window
            settings_dialog.grab_set()            # Make it modal
            
            # Add title
            title_label = ttk.Label(settings_dialog, 
                                   text="Dashboard Features & Settings", 
                                   style="Title.TLabel",
                                   font=("Segoe UI", 16, "bold"))
            title_label.pack(pady=(15, 20))
            
            # Create a notebook for tabs
            settings_notebook = ttk.Notebook(settings_dialog)
            settings_notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            # Features Tab
            features_tab = ttk.Frame(settings_notebook, style="Card.TFrame")
            settings_notebook.add(features_tab, text="Features")
            
            # Settings Tab
            settings_tab = ttk.Frame(settings_notebook, style="Card.TFrame")
            settings_notebook.add(settings_tab, text="Settings")
            
            # About Tab
            about_tab = ttk.Frame(settings_notebook, style="Card.TFrame")
            settings_notebook.add(about_tab, text="About")
            
            # Features Tab Content - scrollable
            features_canvas = tk.Canvas(features_tab, bg=self.theme["card_bg"])
            features_canvas.pack(side="left", fill="both", expand=True)
            
            features_scrollbar = ttk.Scrollbar(features_tab, orient="vertical", command=features_canvas.yview)
            features_scrollbar.pack(side="right", fill="y")
            
            features_canvas.configure(yscrollcommand=features_scrollbar.set)
            features_canvas.bind('<Configure>', lambda e: features_canvas.configure(scrollregion=features_canvas.bbox("all")))
            
            features_content = ttk.Frame(features_canvas, style="Card.TFrame")
            features_canvas.create_window((0, 0), window=features_content, anchor="nw")
            
            # Add features descriptions
            features = [
                ("System Monitor", "Real-time monitoring of CPU, memory, and disk usage with visual gauges."),
                ("Process Management", "View, sort, and filter running processes. Kill processes or view detailed information."),
                ("Performance Graphs", "Track CPU, memory, and disk usage over time with dynamic graphs."),
                ("Theme Customization", "Multiple color themes to personalize your dashboard."),
                ("AI Insights", "AI-powered predictions and anomaly detection for system resources."),
                ("Smart Recommendations", "Get intelligent suggestions to optimize your system performance."),
                ("Virtual Assistant", "Ask questions about your system using natural language."),
                ("Alert System", "Configurable alerts when system resources exceed thresholds."),
                ("Export Capability", "Export process list and system information to CSV files."),
                ("Detailed Process Info", "View comprehensive details about any running process."),
            ]
            
            for i, (feature_name, feature_desc) in enumerate(features):
                feature_frame = ttk.Frame(features_content, style="Card.TFrame")
                feature_frame.pack(fill="x", padx=10, pady=5)
                
                feature_title = ttk.Label(feature_frame, 
                                         text=feature_name, 
                                         style="TLabel",
                                         font=("Segoe UI", 11, "bold"))
                feature_title.pack(anchor="w", padx=5, pady=(5, 2))
                
                feature_desc_label = ttk.Label(feature_frame, 
                                              text=feature_desc, 
                                              style="TLabel",
                                              wraplength=500)
                feature_desc_label.pack(anchor="w", padx=15, pady=(0, 5))
            
            # Settings Tab Content
            settings_frame = ttk.Frame(settings_tab, style="Card.TFrame")
            settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Refresh rate setting
            refresh_frame = ttk.LabelFrame(settings_frame, text="Refresh Rate", style="Card.TFrame")
            refresh_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Label(refresh_frame, text="Update interval (seconds):", style="TLabel").pack(side="left", padx=10, pady=10)
            
            refresh_entry = ttk.Entry(refresh_frame, width=5)
            refresh_entry.insert(0, self.refresh_rate.get() if hasattr(self, 'refresh_rate') else "1")
            refresh_entry.pack(side="left", padx=5, pady=10)
            
            def apply_refresh():
                try:
                    new_rate = int(refresh_entry.get())
                    if 1 <= new_rate <= 10:
                        if hasattr(self, 'refresh_rate'):
                            self.refresh_rate.delete(0, tk.END)
                            self.refresh_rate.insert(0, str(new_rate))
                    else:
                        messagebox.showwarning("Invalid Value", "Refresh rate should be between 1 and 10 seconds.")
                except ValueError:
                    messagebox.showwarning("Invalid Value", "Please enter a valid number.")
            
            ttk.Button(refresh_frame, text="Apply", command=apply_refresh, style="Accent.TButton").pack(side="left", padx=10, pady=10)
            
            # Alert thresholds setting
            alerts_frame = ttk.LabelFrame(settings_frame, text="Alert Thresholds", style="Card.TFrame")
            alerts_frame.pack(fill="x", padx=10, pady=10)
            
            # CPU threshold
            cpu_frame = ttk.Frame(alerts_frame, style="Card.TFrame")
            cpu_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(cpu_frame, text="CPU usage threshold (%):", style="TLabel").pack(side="left")
            
            cpu_threshold_entry = ttk.Entry(cpu_frame, width=5)
            cpu_threshold_entry.insert(0, str(self.alert_thresholds.get("cpu", 80)) if hasattr(self, 'alert_thresholds') else "80")
            cpu_threshold_entry.pack(side="left", padx=5)
            
            # Memory threshold
            mem_frame = ttk.Frame(alerts_frame, style="Card.TFrame")
            mem_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(mem_frame, text="Memory usage threshold (%):", style="TLabel").pack(side="left")
            
            mem_threshold_entry = ttk.Entry(mem_frame, width=5)
            mem_threshold_entry.insert(0, str(self.alert_thresholds.get("memory", 80)) if hasattr(self, 'alert_thresholds') else "80")
            mem_threshold_entry.pack(side="left", padx=5)
            
            # Disk threshold
            disk_frame = ttk.Frame(alerts_frame, style="Card.TFrame")
            disk_frame.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(disk_frame, text="Disk usage threshold (%):", style="TLabel").pack(side="left")
            
            disk_threshold_entry = ttk.Entry(disk_frame, width=5)
            disk_threshold_entry.insert(0, str(self.alert_thresholds.get("disk", 90)) if hasattr(self, 'alert_thresholds') else "90")
            disk_threshold_entry.pack(side="left", padx=5)
            
            def apply_thresholds():
                try:
                    cpu_val = int(cpu_threshold_entry.get())
                    mem_val = int(mem_threshold_entry.get())
                    disk_val = int(disk_threshold_entry.get())
                    
                    if not (0 <= cpu_val <= 100 and 0 <= mem_val <= 100 and 0 <= disk_val <= 100):
                        messagebox.showwarning("Invalid Values", "Thresholds should be between 0 and 100%.")
                        return
                    
                    if hasattr(self, 'alert_thresholds'):
                        self.alert_thresholds["cpu"] = cpu_val
                        self.alert_thresholds["memory"] = mem_val
                        self.alert_thresholds["disk"] = disk_val
                        
                        # Try to update the thresholds in various places throughout the app
                        if hasattr(self, 'update_alert_thresholds'):
                            self.update_alert_thresholds()
                        
                    messagebox.showinfo("Success", "Alert thresholds updated successfully.")
                except ValueError:
                    messagebox.showwarning("Invalid Values", "Please enter valid numbers.")
            
            ttk.Button(alerts_frame, text="Apply", command=apply_thresholds, style="Accent.TButton").pack(anchor="e", padx=10, pady=10)
            
            # About Tab Content
            about_frame = ttk.Frame(about_tab, style="Card.TFrame")
            about_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # App title and version
            app_title = ttk.Label(about_frame, 
                                 text="Advanced Process Monitoring Dashboard", 
                                 style="Title.TLabel",
                                 font=("Segoe UI", 14, "bold"))
            app_title.pack(anchor="center", pady=(20, 5))
            
            app_version = ttk.Label(about_frame, 
                                   text="Version 1.5.0", 
                                   style="TLabel")
            app_version.pack(anchor="center", pady=(0, 20))
            
            # Description
            description = """This advanced system monitoring dashboard provides real-time insights into your computer's performance and running processes. With AI-powered predictions, customizable alerts, and comprehensive process management tools, you can optimize your system's performance and identify issues before they impact your experience."""
            
            desc_label = ttk.Label(about_frame, 
                                  text=description, 
                                  style="TLabel",
                                  wraplength=500,
                                  justify="center")
            desc_label.pack(anchor="center", padx=20, pady=10)
            
            # Credits
            credits_label = ttk.Label(about_frame, 
                                     text="Created with Python, tkinter, and psutil", 
                                     style="TLabel",
                                     font=("Segoe UI", 9, "italic"))
            credits_label.pack(anchor="center", pady=(20, 5))
            
            # Add close button
            close_btn = ttk.Button(
                settings_dialog,
                text="Close",
                style="Accent.TButton",
                command=settings_dialog.destroy
            )
            close_btn.pack(pady=(0, 15))
        except Exception as e:
            print(f"Error displaying settings dialog: {e}")
            messagebox.showerror("Error", "Could not display settings dialog. Please try again.")

    def on_filter_change(self, *args):
        """Handle changes to the filter text field and update the process list accordingly"""
        try:
            # Since trace callbacks can be triggered for various reasons,
            # we use a small delay to avoid excessive updates while typing
            if hasattr(self, '_filter_after_id'):
                self.root.after_cancel(self._filter_after_id)
            
            # Schedule the update with a small delay for better performance
            self._filter_after_id = self.root.after(300, self.update_process_list)
        except Exception as e:
            print(f"Error in filter change handler: {e}")
            # Ensure the process list still updates even if there's an error
            self.update_process_list()