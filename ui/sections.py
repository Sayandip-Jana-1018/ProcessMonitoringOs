import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil
from datetime import datetime
import numpy as np
import platform
import time
from tkinter import messagebox

from ui.gauges import create_gauge, update_gauge
from ui.graphs import create_performance_graphs, update_performance_graphs
from config import THEMES

class TopSection:
    def __init__(self, parent, app):
        """Initialize the TopSection with horizontal gauges and side-by-side panels"""
        self.app = app
        self.theme = app.theme
        
        # Create top frame with transparent background
        self.frame = ttk.Frame(parent, style="Card.TFrame")
        self.frame.pack(fill="x", pady=(0, 10))
        
        # Create a horizontal layout for all top section elements
        top_container = ttk.Frame(self.frame, style="Card.TFrame")
        top_container.pack(fill="x", expand=True)
        
        # Left: Title and system info
        left_frame = ttk.Frame(top_container, style="Card.TFrame")
        left_frame.pack(side="left", fill="y", padx=5)
        
        # Title with improved styling
        title_frame = ttk.Frame(left_frame, style="Card.TFrame")
        title_frame.pack(fill="x", pady=(5, 10))
        
        title_label = ttk.Label(title_frame, 
                               text="SYSTEM MONITOR", 
                               style="Title.TLabel",
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(side="left")
        
        # Add modern icon buttons (right side of title)
        icons_frame = ttk.Frame(title_frame, style="Card.TFrame")
        icons_frame.pack(side="right")
        
        # Refresh Button with icon
        refresh_btn = ttk.Button(icons_frame, 
                                text="🔄", 
                                command=self.app.refresh_dashboard,
                                style="IconButton.TButton",
                                width=2)
        refresh_btn.pack(side="left", padx=2)
        
        # Theme Button with icon - direct theme cycling
        self.theme_btn = ttk.Button(icons_frame, 
                                  text=THEMES[app.current_theme]["icon"], 
                                  command=self.cycle_theme,
                                  style="IconButton.TButton",
                                  width=2)
        self.theme_btn.pack(side="left", padx=2)
        
        # Settings Button with gear icon
        settings_btn = ttk.Button(icons_frame, 
                                 text="⚙️", 
                                 command=self.app.show_settings_dialog,
                                 style="IconButton.TButton",
                                 width=2)
        settings_btn.pack(side="left", padx=2)
        
        # System info in grid layout
        info_frame = ttk.Frame(left_frame, style="Card.TFrame")
        info_frame.pack(fill="x")
        
        # Create labels with right alignment for titles
        labels = ["OS", "CPU", "RAM", "Uptime"]
        self.info_labels = {}
        
        for i, label in enumerate(labels):
            title = ttk.Label(info_frame, 
                            text=f"{label}:", 
                            style="InfoTitle.TLabel",
                            font=("Segoe UI", 10))
            title.grid(row=i, column=0, padx=(0, 10), pady=2, sticky="e")
            
            value = ttk.Label(info_frame, 
                            text="Loading...", 
                            style="Info.TLabel",
                            font=("Segoe UI", 10))
            value.grid(row=i, column=1, pady=2, sticky="w")
            self.info_labels[label] = value
        
        # Center: Gauges in a horizontal layout with transparent background
        gauge_frame = ttk.Frame(top_container, style="TransparentCard.TFrame")
        gauge_frame.pack(side="left", fill="y", padx=10)
        
        # Create gauges in a horizontal row
        gauge_row = ttk.Frame(gauge_frame, style="TransparentCard.TFrame")
        gauge_row.pack(fill="x", expand=True)
        
        # Store gauge references for later updates
        self.gauges = []
        
        # Create CPU gauge
        self.cpu_fig, self.cpu_ax = create_gauge(gauge_row, self.theme, "CPU")
        self.gauges.append((self.cpu_fig, self.cpu_ax))
        
        # Create Memory gauge
        self.mem_fig, self.mem_ax = create_gauge(gauge_row, self.theme, "MEM")
        self.gauges.append((self.mem_fig, self.mem_ax))
        
        # Create Disk gauge
        self.disk_fig, self.disk_ax = create_gauge(gauge_row, self.theme, "DISK")
        self.gauges.append((self.disk_fig, self.disk_ax))
        
        # Right side: Split into two columns for AI Insights and Smart Recommendations
        right_container = ttk.Frame(top_container, style="Card.TFrame")
        right_container.pack(side="right", fill="both", expand=True, padx=5)
        
        # AI Insights panel (left half of right container)
        ai_frame = ttk.Frame(right_container, style="Card.TFrame")
        ai_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.create_ai_insights(ai_frame)
        
        # Smart Recommendations panel (right half of right container)
        recommendations_frame = ttk.Frame(right_container, style="Card.TFrame")
        recommendations_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.create_smart_recommendations(recommendations_frame)
        
        # Start updating system info immediately
        self.update_system_info()

    def create_ai_insights(self, parent):
        """Create the AI insights section with dedicated container"""
        # AI Insights header with enhanced visibility
        ai_header = ttk.Label(parent, 
                             text="AI INSIGHTS", 
                             style="Title.TLabel",
                             font=("Segoe UI", 12, "bold"))
        ai_header.pack(anchor="center", pady=(5, 10))
        
        # Create a notebook for tabs
        self.ai_notebook = ttk.Notebook(parent)
        self.ai_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Predictions tab
        self.predictions_frame = ttk.Frame(self.ai_notebook, style="Card.TFrame")
        self.ai_notebook.add(self.predictions_frame, text="Predictions")
        
        # Prediction status with improved visibility
        self.prediction_status = ttk.Label(
            self.predictions_frame, 
            text="Collecting data for predictions...",
            style="TLabel",
            font=("Segoe UI", 9, "bold")
        )
        self.prediction_status.pack(anchor="w", padx=10, pady=5)
        
        # Prediction results
        self.prediction_results = ttk.Label(
            self.predictions_frame,
            text="",
            style="TLabel",
            wraplength=230,
            font=("Segoe UI", 9)
        )
        self.prediction_results.pack(anchor="w", padx=10, pady=5, fill="x")
        
        # Anomaly Detection tab
        self.anomaly_frame = ttk.Frame(self.ai_notebook, style="Card.TFrame")
        self.ai_notebook.add(self.anomaly_frame, text="Anomaly Detection")
        
        # Anomaly status
        self.anomaly_status = ttk.Label(
            self.anomaly_frame,
            text="Training anomaly detection model...",
            style="TLabel",
            font=("Segoe UI", 9, "bold")
        )
        self.anomaly_status.pack(anchor="w", padx=10, pady=5)
        
        # Anomaly results
        self.anomaly_results = ttk.Label(
            self.anomaly_frame,
            text="",
            style="TLabel",
            wraplength=230,
            font=("Segoe UI", 9)
        )
        self.anomaly_results.pack(anchor="w", padx=10, pady=5, fill="x")
        
        # Recent anomalies list
        anomaly_list_label = ttk.Label(
            self.anomaly_frame,
            text="Recent Anomalies:",
            style="TLabel",
            font=("Segoe UI", 9, "bold")
        )
        anomaly_list_label.pack(anchor="w", padx=10, pady=5)
        
        # Create a text widget for anomalies
        self.anomaly_text = tk.Text(
            self.anomaly_frame,
            height=5,
            width=25,
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            font=("Consolas", 8),
            wrap="word"
        )
        self.anomaly_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.anomaly_text.config(state="disabled")

    def create_smart_recommendations(self, parent):
        """Create the Smart Recommendations panel with more space for detailed content"""
        # Title
        recommendations_title = ttk.Label(parent,
                                        text="SMART RECOMMENDATIONS",
                                        style="Title.TLabel",
                                        font=("Segoe UI", 12, "bold"))
        recommendations_title.pack(anchor="center", pady=(5, 10))
        
        # Recommendations content with increased height
        self.recommendations_content = tk.Text(
            parent,
            height=14,  # Increased height for more detailed recommendations
            width=30,
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            font=("Segoe UI", 9),
            wrap="word",
            relief="flat",
            padx=10,
            pady=10
        )
        self.recommendations_content.pack(fill="both", expand=True, padx=5, pady=5)
        self.recommendations_content.config(state="disabled")
        
        # Immediately update recommendations
        self.update_smart_recommendations()

    def update_system_info(self):
        """Update the system information labels with current data"""
        try:
            # OS information
            os_info = f"{platform.system()} {platform.release()}"
            self.info_labels["OS"].config(text=os_info)
            
            # CPU information
            cpu_count = psutil.cpu_count()
            physical_cores = psutil.cpu_count(logical=False)
            cpu_percent = psutil.cpu_percent()
            cpu_info = f"{physical_cores} cores ({cpu_count} logical), {cpu_percent}% used"
            self.info_labels["CPU"].config(text=cpu_info)
            
            # RAM information
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024**3)
            used_gb = mem.used / (1024**3)
            ram_info = f"{used_gb:.1f} GB / {total_gb:.1f} GB ({mem.percent}%)"
            self.info_labels["RAM"].config(text=ram_info)
            
            # Uptime information
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                uptime_info = f"{int(days)}d {int(hours)}h {int(minutes)}m"
            elif hours > 0:
                uptime_info = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            else:
                uptime_info = f"{int(minutes)}m {int(seconds)}s"
            
            self.info_labels["Uptime"].config(text=uptime_info)
            
            # Schedule next update (every 10 seconds for system info is reasonable)
            self.frame.after(10000, self.update_system_info)
            
        except Exception as e:
            print(f"Error updating system info: {e}")
            # Handle errors gracefully by showing "Error" in the fields
            for label in self.info_labels:
                self.info_labels[label].config(text="Error")

    def update_gauges(self, cpu_percent, mem_percent, disk_percent):
        """Update gauge charts for CPU, memory and disk"""
        update_gauge(self.cpu_ax, cpu_percent, "CPU", self.theme)
        update_gauge(self.mem_ax, mem_percent, "MEM", self.theme)
        update_gauge(self.disk_ax, disk_percent, "DISK", self.theme)
        
        self.cpu_ax.figure.canvas.draw()
        self.mem_ax.figure.canvas.draw()
        self.disk_ax.figure.canvas.draw()
    
    def update_gauge_colors(self, theme):
        """Update gauge colors when theme changes"""
        try:
            # Store the current theme
            self.theme = theme
            
            # Update gauges background color
            for fig, _ in self.gauges:
                fig.patch.set_facecolor(theme["card_bg"])
            
            # Force redraw of gauges with current values
            cpu_percent = self.app.cpu_usage_history[-1] if self.app.cpu_usage_history else 0
            mem_percent = self.app.mem_usage_history[-1] if self.app.mem_usage_history else 0
            disk_percent = self.app.disk_usage_history[-1] if self.app.disk_usage_history else 0
            
            self.update_gauges(cpu_percent, mem_percent, disk_percent)
        except Exception as e:
            print(f"Error updating gauge colors: {e}")

    def refresh_system_info(self):
        """Immediately refresh the system information"""
        self.update_system_info()

    def update_graph_colors(self, theme):
        """Update graph colors when theme changes"""
        try:
            # Store the current theme
            self.theme = theme
            
            # Update the graph figure background
            self.perf_fig.patch.set_facecolor(theme["card_bg"])
            self.perf_ax.set_facecolor(theme["chart_bg"])
            
            # Update grid color
            self.perf_ax.grid(color=theme["grid_color"], linestyle='--', alpha=0.6)
            
            # Update line colors
            if hasattr(self, 'cpu_line') and self.cpu_line:
                self.cpu_line.set_color(theme["cpu_color"])
            
            if hasattr(self, 'mem_line') and self.mem_line:
                self.mem_line.set_color(theme["mem_color"])
            
            if hasattr(self, 'disk_line') and self.disk_line:
                self.disk_line.set_color(theme["disk_color"])
            
            # Update text colors
            self.perf_ax.tick_params(colors=theme["text"])
            for text in self.perf_ax.get_xticklabels() + self.perf_ax.get_yticklabels():
                text.set_color(theme["text"])
            
            # Update title color
            if self.perf_ax.get_title():
                self.perf_ax.title.set_color(theme["text"])
            
            # Redraw the canvas
            self.perf_canvas.draw()
        except Exception as e:
            print(f"Error updating graph colors: {e}")

    def cycle_theme(self):
        """Cycle through available themes without showing a dialog"""
        # Get list of theme keys
        theme_keys = list(THEMES.keys())
        
        # Find the index of the current theme
        current_index = theme_keys.index(self.app.current_theme)
        
        # Get the next theme in the cycle
        next_index = (current_index + 1) % len(theme_keys)
        next_theme = theme_keys[next_index]
        
        # Instead of calling apply_theme, call toggle_theme which exists in app.py
        self.app.toggle_theme()
        
        # Update the theme button icon
        self.theme_btn.config(text=THEMES[self.app.current_theme]["icon"])

    def update_smart_recommendations(self):
        """Update the smart recommendations with more detailed tips based on system data"""
        try:
            # Clear existing text
            self.recommendations_content.config(state="normal")
            self.recommendations_content.delete(1.0, tk.END)
            
            # Get current system info - with error handling
            cpu_percent = 0
            mem_percent = 0
            disk_percent = 0
            
            try:
                if hasattr(self.app, 'cpu_usage_history') and self.app.cpu_usage_history:
                    cpu_percent = self.app.cpu_usage_history[-1]
                else:
                    cpu_percent = psutil.cpu_percent()
                    
                if hasattr(self.app, 'mem_usage_history') and self.app.mem_usage_history:
                    mem_percent = self.app.mem_usage_history[-1]
                else:
                    mem_percent = psutil.virtual_memory().percent
                    
                if hasattr(self.app, 'disk_usage_history') and self.app.disk_usage_history:
                    disk_percent = self.app.disk_usage_history[-1]
                else:
                    try:
                        if platform.system() == 'Windows':
                            disk_percent = psutil.disk_usage('C:\\').percent
                        else:
                            disk_percent = psutil.disk_usage('/').percent
                    except:
                        disk_percent = 50  # Default value
            except Exception as e:
                print(f"Error getting system metrics: {e}")
                # Use defaults if there's an error
            
            # Generate more detailed recommendations based on current usage
            recommendations = []
            
            # Determine overall system health
            if cpu_percent > 80 or mem_percent > 80 or disk_percent > 90:
                recommendations.append("⚠️ SYSTEM ALERT: Your system resources are critically high!")
            elif cpu_percent > 60 or mem_percent > 60 or disk_percent > 75:
                recommendations.append("⚠️ SYSTEM WARNING: Resource usage is approaching high levels")
            else:
                recommendations.append("✅ Your system is running well. Here are some optimization tips:")
            
            recommendations.append("")
            
            # CPU recommendations
            recommendations.append("🔹 CPU OPTIMIZATION:")
            if cpu_percent > 80:
                recommendations.append("  • URGENT: High CPU usage detected at {:.1f}%!".format(cpu_percent))
                recommendations.append("  • Identify and close CPU-intensive applications")
                recommendations.append("  • Check Task Manager for processes using excessive CPU")
                recommendations.append("  • Consider upgrading CPU if consistently overloaded")
                recommendations.append("  • Scan for malware/crypto miners using background resources")
            elif cpu_percent > 60:
                recommendations.append("  • Moderate CPU load detected at {:.1f}%".format(cpu_percent))
                recommendations.append("  • Close unnecessary background applications")
                recommendations.append("  • Disable startup programs that aren't essential")
                recommendations.append("  • Consider limiting CPU-intensive tasks during work hours")
            else:
                recommendations.append("  • CPU usage is optimal at {:.1f}%".format(cpu_percent))
                recommendations.append("  • For better performance, keep background applications minimal")
                recommendations.append("  • Schedule resource-intensive tasks during idle periods")
            
            recommendations.append("")
            
            # Memory recommendations
            recommendations.append("🔹 MEMORY OPTIMIZATION:")
            if mem_percent > 80:
                recommendations.append("  • URGENT: High memory usage detected at {:.1f}%!".format(mem_percent))
                recommendations.append("  • Close memory-intensive applications immediately")
                recommendations.append("  • Check for memory leaks in long-running applications")
                recommendations.append("  • Restart applications that might have memory leaks")
                recommendations.append("  • Consider adding more RAM if consistently low")
                recommendations.append("  • Disable unnecessary browser extensions that consume memory")
            elif mem_percent > 60:
                recommendations.append("  • Elevated memory usage at {:.1f}%".format(mem_percent))
                recommendations.append("  • Close browser tabs you're not actively using")
                recommendations.append("  • Restart memory-intensive applications periodically")
                recommendations.append("  • Check for applications with memory leaks")
                recommendations.append("  • Limit use of memory-intensive applications simultaneously")
            else:
                recommendations.append("  • Memory usage is healthy at {:.1f}%".format(mem_percent))
                recommendations.append("  • Maintain clean memory habits by closing unused applications")
                recommendations.append("  • Restart memory-intensive applications occasionally")
            
            recommendations.append("")
            
            # Disk recommendations
            recommendations.append("🔹 DISK OPTIMIZATION:")
            if disk_percent > 90:
                recommendations.append("  • CRITICAL: Extremely low disk space at {:.1f}%!".format(disk_percent))
                recommendations.append("  • Run disk cleanup utility immediately")
                recommendations.append("  • Empty Recycle Bin / Trash")
                recommendations.append("  • Uninstall unused applications")
                recommendations.append("  • Move large files (videos, backups) to external storage")
                recommendations.append("  • Delete temporary files and browser caches")
                recommendations.append("  • Use disk analyzer to identify large unnecessary files")
            elif disk_percent > 75:
                recommendations.append("  • Disk space is running low at {:.1f}%".format(disk_percent))
                recommendations.append("  • Run disk cleanup periodically")
                recommendations.append("  • Consider uninstalling rarely used applications")
                recommendations.append("  • Move media files to external storage")
                recommendations.append("  • Clear downloads folder regularly")
            else:
                recommendations.append("  • Disk usage is at a good level ({:.1f}%)".format(disk_percent))
                recommendations.append("  • Schedule regular disk maintenance tasks")
                recommendations.append("  • Set up automatic disk cleanup weekly")
            
            recommendations.append("")
            
            # Performance tips
            recommendations.append("🔹 SYSTEM PERFORMANCE TIPS:")
            recommendations.append("  • Update your operating system regularly")
            recommendations.append("  • Install the latest drivers for your hardware")
            recommendations.append("  • Disable unnecessary startup programs")
            recommendations.append("  • Run a disk defragmentation tool (for HDDs)")
            recommendations.append("  • Check for and fix disk errors periodically")
            recommendations.append("  • Ensure your system has adequate cooling")
            recommendations.append("  • Keep your applications updated to latest versions")
            recommendations.append("  • Consider using an SSD for your operating system")
            
            # Insert all recommendations
            for recommendation in recommendations:
                self.recommendations_content.insert(tk.END, recommendation + "\n")
            
            self.recommendations_content.config(state="disabled")
        except Exception as e:
            print(f"Error updating recommendations: {e}")
            # Show a simplified message in case of error
            self.recommendations_content.config(state="normal")
            self.recommendations_content.delete(1.0, tk.END)
            self.recommendations_content.insert(tk.END, "Unable to generate recommendations.\nPlease try refreshing the dashboard.")
            self.recommendations_content.config(state="disabled")

class MiddleSection:
    def __init__(self, parent, app):
        """Initialize the middle section with process list and performance graphs"""
        self.app = app
        self.theme = app.theme
        
        # Create middle frame with padding
        self.frame = ttk.Frame(parent, style="TFrame")
        self.frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Left side: Process list (50% width)
        self.process_frame = ttk.Frame(self.frame, style="Card.TFrame")
        self.process_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        # Process list header
        header_frame = ttk.Frame(self.process_frame, style="Card.TFrame")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        # Title and process count
        title_frame = ttk.Frame(header_frame, style="Card.TFrame")
        title_frame.pack(side="left")
        
        self.title_label = ttk.Label(title_frame, 
                                    text="RUNNING PROCESSES", 
                                    style="Title.TLabel")
        self.title_label.pack(side="left")
        
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
        
        # Process list with improved styling
        self.create_process_list()
        
        # Right side: Split into two equal parts
        right_container = ttk.Frame(self.frame, style="TFrame")
        right_container.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)
        
        # Top right: Virtual Assistant
        self.assistant_frame = ttk.Frame(right_container, style="Card.TFrame")
        self.assistant_frame.pack(side="top", fill="both", expand=True, pady=(0, 5))
        
        # Create virtual assistant panel
        self.create_virtual_assistant()
        
        # Bottom right: Performance graphs
        self.graph_frame = ttk.Frame(right_container, style="Card.TFrame")
        self.graph_frame.pack(side="bottom", fill="both", expand=True, pady=(5, 0))
        
        # Graph header
        graph_header = ttk.Frame(self.graph_frame, style="Card.TFrame")
        graph_header.pack(fill="x", padx=15, pady=10)
        
        graph_title = ttk.Label(graph_header, 
                               text="SYSTEM PERFORMANCE", 
                               style="Title.TLabel")
        graph_title.pack(side="left")
        
        # Time range selector
        time_frame = ttk.Frame(graph_header, style="Card.TFrame")
        time_frame.pack(side="right")
        
        self.time_range = ttk.Combobox(time_frame,
                                      values=["5 minutes", "15 minutes", "1 hour"],
                                      width=10,
                                      state="readonly")
        self.time_range.set("5 minutes")
        self.time_range.pack(side="right")
        
        time_label = ttk.Label(time_frame, text="Time Range:", style="TLabel")
        time_label.pack(side="right", padx=(0, 5))
        
        # Create performance graphs
        self.create_performance_graphs()

    def create_process_list(self):
        """Create the process list with improved styling and performance"""
        # Process treeview with improved styling
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       rowheight=30,
                       font=("Segoe UI", 10))
        style.configure("Custom.Treeview.Heading",
                       font=("Segoe UI", 10, "bold"))
        
        # Create a container frame for the process list
        list_container = ttk.Frame(self.process_frame, style="Card.TFrame")
        list_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        columns = ("PID", "Name", "CPU%", "Memory", "Status")
        self.tree = ttk.Treeview(list_container, 
                                columns=columns, 
                                show="headings",
                                style="Custom.Treeview")
        
        # Configure columns
        self.tree.heading("PID", text="PID", command=lambda: self.sort_processes_by("PID"))
        self.tree.heading("Name", text="Process Name", command=lambda: self.sort_processes_by("Name"))
        self.tree.heading("CPU%", text="CPU %", command=lambda: self.sort_processes_by("CPU%"))
        self.tree.heading("Memory", text="Memory (MB)", command=lambda: self.sort_processes_by("Memory"))
        self.tree.heading("Status", text="Status", command=lambda: self.sort_processes_by("Status"))
        
        self.tree.column("PID", width=70, anchor="center")
        self.tree.column("Name", width=200)
        self.tree.column("CPU%", width=70, anchor="center")
        self.tree.column("Memory", width=100, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add right-click context menu
        self.create_context_menu()
        
        # Bind single-click selection to improve responsiveness
        self.tree.bind("<ButtonRelease-1>", self.on_process_select)
        
        # After creating the process list, add the process controls panel below it
        self.create_process_controls_panel()

    def create_context_menu(self):
        """Create a right-click context menu for the process list"""
        self.context_menu = tk.Menu(self.app.root, tearoff=0, bg=self.theme["card_bg"], fg=self.theme["text"])
        self.context_menu.add_command(label="Kill Process", command=self.app.kill_process)
        self.context_menu.add_command(label="Process Details", command=self.app.show_process_details)
        self.context_menu.add_separator()
        
        # Priority submenu
        priority_menu = tk.Menu(self.context_menu, tearoff=0, bg=self.theme["card_bg"], fg=self.theme["text"])
        priority_menu.add_command(label="High", command=lambda: self.app.change_priority(-10))
        priority_menu.add_command(label="Normal", command=lambda: self.app.change_priority(0))
        priority_menu.add_command(label="Low", command=lambda: self.app.change_priority(19))
        self.context_menu.add_cascade(label="Set Priority", menu=priority_menu)
        
        # Bind right-click to show context menu
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show the context menu on right-click"""
        # Select the item under the cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def create_performance_graphs(self):
        """Create performance graphs panel with improved styling"""
        # Create performance graphs
        self.perf_fig, self.perf_axes = create_performance_graphs(self.graph_frame, self.theme)
        
        # Store canvas reference
        self.perf_canvas = self.perf_fig.canvas

    def update_process_list(self):
        """Update the process list with current processes - optimized for performance"""
        try:
            # Get filter text
            filter_text = self.filter_var.get().lower()
            
            # Clear existing items only if necessary
            if hasattr(self, '_last_filter') and self._last_filter == filter_text:
                # Just update existing items without clearing
                self._update_existing_processes()
                return
            
            # Store current filter for next comparison
            self._last_filter = filter_text
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get process list - limit to top 100 processes to improve performance
            processes = []
            process_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    proc_info = proc.info
                    if filter_text in proc_info['name'].lower():
                        processes.append((
                            proc_info['pid'],
                            proc_info['name'],
                            f"{proc_info['cpu_percent']:.1f}",
                            f"{proc_info['memory_info'].rss / (1024 * 1024):.1f}",  # Convert to MB
                            proc_info['status']
                        ))
                        process_count += 1
                    
                    # Limit to 100 processes for better performance
                    if process_count >= 100 and not filter_text:
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort processes by CPU usage
            processes.sort(key=lambda x: float(x[2]), reverse=True)
            
            # Insert into treeview
            for proc in processes:
                self.tree.insert('', 'end', values=proc)
            
            # Update process count - show total processes, not just displayed ones
            total_processes = len(list(psutil.process_iter()))
            self.process_count.config(text=f"{process_count} of {total_processes} processes")
            
            # Update the system info label
            self.update_system_info_label()
        except Exception as e:
            print(f"Error updating process list: {e}")

    def _update_existing_processes(self):
        """Update only the existing processes in the list for better performance"""
        try:
            # Get all items in the tree
            items = self.tree.get_children()
            if not items:
                # If no items, do a full update
                self.update_process_list()
                return
            
            # Update each item
            for item in items:
                values = self.tree.item(item)['values']
                if not values:
                    continue
                
                try:
                    pid = int(values[0])
                    proc = psutil.Process(pid)
                    
                    # Update the values
                    new_values = (
                        pid,
                        proc.name(),
                        f"{proc.cpu_percent(interval=0):.1f}",
                        f"{proc.memory_info().rss / (1024 * 1024):.1f}",
                        proc.status()
                    )
                    
                    # Update the item
                    self.tree.item(item, values=new_values)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists, remove it
                    self.tree.delete(item)
            
            # Update the system info label
            self.update_system_info_label()
        except Exception as e:
            print(f"Error updating existing processes: {e}")
            # Fall back to full update if there's an error
            self.update_process_list()

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
            avg_cpu = sum(self.app.cpu_usage_history[-10:]) / min(10, len(self.app.cpu_usage_history)) if self.app.cpu_usage_history else 0
            
            # Update the system info label
            self.system_info_label.config(
                text=f"Processes: {total_processes} | Memory: {total_memory_mb:.1f} MB | CPU Avg: {avg_cpu:.1f}%"
            )
        except Exception as e:
            # Graceful error handling
            print(f"Error updating system info label: {e}")
            self.system_info_label.config(text="Processes: -- | Memory: -- MB | CPU Avg: --%")

    def update_performance_graphs(self, timestamps, cpu_history, mem_history, disk_history=None):
        """Update the performance graphs"""
        try:
            # Make sure we have the required data
            if not timestamps or len(timestamps) < 2:
                return
            
            # Make sure CPU and memory history data is available
            if not cpu_history or not mem_history:
                return
            
            # If disk_history is None, use a default value or zeros
            if disk_history is None and hasattr(self.app, 'disk_usage_history'):
                disk_history = self.app.disk_usage_history
            elif disk_history is None:
                disk_history = [0.0] * len(timestamps)
            
            # Ensure all data arrays have the same length
            min_length = min(len(timestamps), len(cpu_history), len(mem_history), len(disk_history))
            if min_length < 2:
                return  # Not enough data
            
            timestamps = timestamps[-min_length:]
            cpu_history = cpu_history[-min_length:]
            mem_history = mem_history[-min_length:]
            disk_history = disk_history[-min_length:]
            
            # Call the update function from graphs.py with all parameters
            update_performance_graphs(
                self.perf_axes, 
                timestamps, 
                cpu_history, 
                mem_history, 
                disk_history,
                self.theme
            )
            
            # Force a canvas redraw
            self.perf_canvas.draw_idle()
        except Exception as e:
            print(f"Error in update_performance_graphs method: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_process(self):
        """Get the selected process from the treeview"""
        selected = self.tree.selection()
        if not selected:
            return None
        
        # Get the values from the selected item
        values = self.tree.item(selected[0])['values']
        
        # Debug print to verify we're getting values
        print(f"Selected process: {values}")
        
        # Make sure we have values before returning
        if values and len(values) >= 5:
            return values
        return None

    def get_all_processes(self):
        """Get all processes from the treeview"""
        processes = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id)['values']
            processes.append(values)
        return processes

    def sort_processes_by(self, column):
        """Sort the process list by the specified column"""
        # Get all items
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # Sort items
        if column in ("CPU%", "Memory"):
            # Numeric sort for CPU and Memory
            items.sort(key=lambda x: float(x[0].replace('%', '')), reverse=True)
        else:
            # Text sort for other columns
            items.sort(reverse=True if hasattr(self, 'sort_reverse') and self.sort_reverse else False)
        
        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # Toggle sort direction for next click
        self.sort_reverse = not getattr(self, 'sort_reverse', False)
        
        # Update the headings to show sort direction
        for col in ("PID", "Name", "CPU%", "Memory", "Status"):
            if col == column:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.tree.heading(col, text=col + direction)
            else:
                self.tree.heading(col, text=col)

    def update_graph_colors(self, theme):
        """Update graph colors when theme changes"""
        try:
            # Store the current theme
            self.theme = theme
            
            # Update the graph figure background
            self.perf_fig.patch.set_facecolor(theme["card_bg"])
            self.perf_ax.set_facecolor(theme["chart_bg"])
            
            # Update grid color
            self.perf_ax.grid(color=theme["grid_color"], linestyle='--', alpha=0.6)
            
            # Update line colors
            if hasattr(self, 'cpu_line') and self.cpu_line:
                self.cpu_line.set_color(theme["cpu_color"])
            
            if hasattr(self, 'mem_line') and self.mem_line:
                self.mem_line.set_color(theme["mem_color"])
            
            if hasattr(self, 'disk_line') and self.disk_line:
                self.disk_line.set_color(theme["disk_color"])
            
            # Update text colors
            self.perf_ax.tick_params(colors=theme["text"])
            for text in self.perf_ax.get_xticklabels() + self.perf_ax.get_yticklabels():
                text.set_color(theme["text"])
            
            # Update title color
            if self.perf_ax.get_title():
                self.perf_ax.title.set_color(theme["text"])
            
            # Redraw the canvas
            self.perf_canvas.draw()
        except Exception as e:
            print(f"Error updating graph colors: {e}")

    def create_process_controls_panel(self):
        """Create a streamlined panel with process controls at the bottom of the process list"""
        # Create a frame for the controls panel that spans the full width of the process frame
        controls_panel = ttk.Frame(self.process_frame, style="Card.TFrame")
        controls_panel.pack(fill="x", side="bottom", padx=10, pady=10)
        
        # Create a horizontal separator above the controls
        ttk.Separator(self.process_frame, orient="horizontal").pack(fill="x", side="bottom", padx=10, pady=(0, 5))
        
        # Create a single row for all controls
        controls_row = ttk.Frame(controls_panel, style="Card.TFrame")
        controls_row.pack(fill="x", padx=5, pady=5)
        
        # Process control buttons (left side)
        button_frame = ttk.Frame(controls_row, style="Card.TFrame")
        button_frame.pack(side="left", padx=5)
        
        # Kill Process button
        kill_btn = ttk.Button(button_frame, 
                             text="Kill Process", 
                             command=self.app.kill_process,
                             style="Danger.TButton")
        kill_btn.pack(side="left", padx=2)
        
        # Process Details button
        details_btn = ttk.Button(button_frame, 
                                text="Process Details", 
                                command=self.app.show_process_details,
                                style="Accent.TButton")
        details_btn.pack(side="left", padx=2)
        
        # Export button
        export_btn = ttk.Button(button_frame, 
                               text="Export List", 
                               command=self.app.export_process_list,
                               style="Success.TButton")
        export_btn.pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(controls_row, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        
        # Alert thresholds (center)
        threshold_frame = ttk.Frame(controls_row, style="Card.TFrame")
        threshold_frame.pack(side="left", padx=5)
        
        ttk.Label(threshold_frame, text="Alerts:", style="TLabel", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
        
        # CPU threshold
        ttk.Label(threshold_frame, text="CPU:", style="TLabel").pack(side="left", padx=(5, 2))
        self.app.cpu_threshold = ttk.Entry(threshold_frame, width=3)
        self.app.cpu_threshold.insert(0, "80")
        self.app.cpu_threshold.pack(side="left")
        
        # Memory threshold
        ttk.Label(threshold_frame, text="Mem:", style="TLabel").pack(side="left", padx=(5, 2))
        self.app.mem_threshold = ttk.Entry(threshold_frame, width=3)
        self.app.mem_threshold.insert(0, "80")
        self.app.mem_threshold.pack(side="left")
        
        # Disk threshold
        ttk.Label(threshold_frame, text="Disk:", style="TLabel").pack(side="left", padx=(5, 2))
        self.app.disk_threshold = ttk.Entry(threshold_frame, width=3)
        self.app.disk_threshold.insert(0, "90")
        self.app.disk_threshold.pack(side="left")
        
        # Apply button
        ttk.Button(threshold_frame, text="Apply",
                   command=self.app.update_alert_thresholds,
                   style="Accent.TButton").pack(side="left", padx=(5, 0))
        
        # Separator
        ttk.Separator(controls_row, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        
        # System info (right side)
        info_frame = ttk.Frame(controls_row, style="Card.TFrame")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # System info in a single line
        self.system_info_label = ttk.Label(
            info_frame, 
            text="Processes: 0 | Memory: 0 MB | CPU Avg: 0%", 
            style="TLabel"
        )
        self.system_info_label.pack(side="left", padx=5)
        
        # Refresh rate (far right)
        refresh_frame = ttk.Frame(controls_row, style="Card.TFrame")
        refresh_frame.pack(side="right", padx=5)
        
        ttk.Label(refresh_frame, text="Refresh:", style="TLabel").pack(side="left", padx=(0, 2))
        
        self.app.refresh_rate = ttk.Entry(refresh_frame, width=3)
        self.app.refresh_rate.insert(0, "1")  # Default to 1 second
        self.app.refresh_rate.pack(side="left")
        
        ttk.Label(refresh_frame, text="sec", style="TLabel").pack(side="left", padx=(2, 0))

    def create_virtual_assistant(self):
        """Create the Virtual Assistant interface for user interaction"""
        # Title
        assistant_title = ttk.Label(self.assistant_frame,
                                  text="VIRTUAL ASSISTANT",
                                  style="Title.TLabel",
                                  font=("Segoe UI", 12, "bold"))
        assistant_title.pack(anchor="center", pady=(10, 10))
        
        # Chat display area
        self.chat_display = tk.Text(
            self.assistant_frame,
            height=12,
            width=30,
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            font=("Segoe UI", 9),
            wrap="word",
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.chat_display.config(state="disabled")
        
        # Initial welcome message
        self.update_chat_display("Assistant: Hello! I can help you monitor your system. Ask me questions like 'What's using the most CPU?' or 'How much memory do I have?'")
        
        # Input area
        input_frame = ttk.Frame(self.assistant_frame, style="Card.TFrame")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.user_input = ttk.Entry(input_frame, width=30)
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.process_user_input)
        
        send_btn = ttk.Button(input_frame,
                             text="Ask",
                             command=self.process_user_input,
                             style="Accent.TButton")
        send_btn.pack(side="right")
    
    def update_chat_display(self, message):
        """Update the chat display with a new message"""
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, message + "\n\n")
        self.chat_display.see(tk.END)  # Scroll to the bottom
        self.chat_display.config(state="disabled")
    
    def process_user_input(self, event=None):
        """Process user input and generate a response"""
        user_query = self.user_input.get().strip()
        if not user_query:
            return
        
        # Display user query
        self.update_chat_display(f"You: {user_query}")
        
        # Clear input field
        self.user_input.delete(0, tk.END)
        
        # Generate response based on query
        response = self.generate_nlp_response(user_query)
        
        # Display response
        self.update_chat_display(f"Assistant: {response}")
    
    def generate_nlp_response(self, query):
        """Generate a response based on the user's query"""
        query = query.lower()
        
        # CPU-related queries
        if any(keyword in query for keyword in ["cpu", "processor", "core"]):
            if "most" in query and "using" in query:
                # Find process using most CPU
                top_process = self.get_top_process_by_resource("cpu")
                return f"The process using the most CPU is {top_process[0]} at {top_process[1]:.1f}%."
            else:
                # General CPU info
                cpu_percent = psutil.cpu_percent()
                cpu_count = psutil.cpu_count()
                physical_cores = psutil.cpu_count(logical=False)
                return f"Your CPU usage is {cpu_percent:.1f}%. You have {physical_cores} physical cores and {cpu_count} logical cores."
        
        # Memory-related queries
        elif any(keyword in query for keyword in ["memory", "ram", "mem"]):
            if "most" in query and "using" in query:
                # Find process using most memory
                top_process = self.get_top_process_by_resource("memory")
                return f"The process using the most memory is {top_process[0]} at {top_process[1]:.1f} MB."
            else:
                # General memory info
                mem = psutil.virtual_memory()
                total_gb = mem.total / (1024**3)
                used_gb = mem.used / (1024**3)
                free_gb = mem.available / (1024**3)
                return f"You have {total_gb:.1f}GB of RAM. Currently using {used_gb:.1f}GB ({mem.percent}%) with {free_gb:.1f}GB free."
        
        # Disk-related queries
        elif any(keyword in query for keyword in ["disk", "storage", "drive"]):
            try:
                disk = psutil.disk_usage('C:\\' if platform.system() == 'Windows' else '/')
                total_gb = disk.total / (1024**3)
                used_gb = disk.used / (1024**3)
                free_gb = disk.free / (1024**3)
                return f"Your main disk has {total_gb:.1f}GB total space. Using {used_gb:.1f}GB ({disk.percent}%) with {free_gb:.1f}GB free."
            except:
                return "I couldn't retrieve disk information."
        
        # Process-related queries
        elif any(keyword in query for keyword in ["process", "program", "app", "running"]):
            if "how many" in query:
                process_count = len(list(psutil.process_iter()))
                return f"There are currently {process_count} processes running on your system."
            elif "list" in query:
                processes = [p.name() for p in psutil.process_iter()][:5]
                return f"Here are some of the processes running: {', '.join(processes)}..."
            else:
                return "You can view all running processes in the process list below."
        
        # System-related queries
        elif any(keyword in query for keyword in ["system", "computer", "pc", "laptop"]):
            os_info = platform.system() + " " + platform.release()
            uptime_seconds = int(time.time() - psutil.boot_time())
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"You're running {os_info}. Your system has been up for {hours} hours, {minutes} minutes."
        
        # Help-related queries
        elif any(keyword in query for keyword in ["help", "can you", "what can", "how to"]):
            return "I can help you monitor your system. You can ask me about CPU usage, memory usage, disk space, running processes, and system information. Try questions like 'What's using the most CPU?' or 'How much memory do I have?'"
        
        # Default response
        else:
            return "I'm not sure how to answer that. Try asking about your CPU, memory, disk usage, or running processes."
    
    def get_top_process_by_resource(self, resource_type):
        """Get the process using the most of a specific resource"""
        if resource_type == "cpu":
            # Get processes sorted by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append((proc.info['name'], proc.info['cpu_percent']))
                except:
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x[1], reverse=True)
            
            if processes:
                return processes[0]
            else:
                return ("Unknown", 0.0)
                
        elif resource_type == "memory":
            # Get processes sorted by memory usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    processes.append((proc.info['name'], memory_mb))
                except:
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x[1], reverse=True)
            
            if processes:
                return processes[0]
            else:
                return ("Unknown", 0.0)
        
        return ("Unknown", 0.0)

    def update_detailed_ai_insights(self, predictions, anomaly_result, recent_anomalies):
        """Update the detailed AI insights in the virtual assistant"""
        # If the virtual assistant is showing, update with AI insights
        try:
            # Update chat with latest AI insights if no recent user interaction
            if hasattr(self, 'chat_display') and self.chat_display.get(1.0, tk.END).strip().endswith("?"):
                # Only update if the last message was the welcome message
                
                # Format AI insights message
                ai_message = "Here's the latest system analysis:\n\n"
                
                # Add anomaly detection info
                if anomaly_result and self.app.anomaly_detector.is_trained:
                    if anomaly_result['is_anomaly']:
                        ai_message += "⚠️ ANOMALY DETECTED: Unusual system behavior detected.\n\n"
                    else:
                        ai_message += "✓ System behavior is normal.\n\n"
                
                # Add prediction info
                if predictions and predictions.get('cpu'):
                    cpu_pred = predictions.get('cpu', [])[0]  # Get first prediction
                    mem_pred = predictions.get('memory', [])[0]
                    disk_pred = predictions.get('disk', [])[0]
                    
                    ai_message += f"Predictions for next few minutes:\n"
                    ai_message += f"- CPU: {cpu_pred:.1f}%\n"
                    ai_message += f"- Memory: {mem_pred:.1f}%\n"
                    ai_message += f"- Disk: {disk_pred:.1f}%\n\n"
                    
                    # Add warnings if needed
                    cpu_threshold = self.app.alert_thresholds["cpu"]
                    mem_threshold = self.app.alert_thresholds["memory"]
                    disk_threshold = self.app.alert_thresholds["disk"]
                    
                    warnings = []
                    if cpu_pred > cpu_threshold:
                        warnings.append(f"CPU usage may exceed {cpu_threshold}% threshold")
                    if mem_pred > mem_threshold:
                        warnings.append(f"Memory usage may exceed {mem_threshold}% threshold")
                    if disk_pred > disk_threshold:
                        warnings.append(f"Disk usage may exceed {disk_threshold}% threshold")
                    
                    if warnings:
                        ai_message += "⚠️ WARNINGS:\n- " + "\n- ".join(warnings)
                
                # Update the chat display with AI insights
                self.update_chat_display(f"Assistant: {ai_message}")
        except Exception as e:
            # Silently handle any errors to prevent application crashes
            print(f"Error updating AI insights in virtual assistant: {e}")
            pass

    def on_process_select(self, event):
        """Handle process selection"""
        # Get the selected item
        selected = self.tree.selection()
        if selected:
            # Store the selected process info for quick access
            self.selected_process = self.tree.item(selected[0])['values']
        else:
            self.selected_process = None

class BottomSection:
    def __init__(self, parent, app):
        """Initialize the bottom section with control buttons"""
        self.app = app
        self.theme = app.theme
        
        # Create bottom frame
        self.frame = ttk.Frame(parent, style="Card.TFrame")
        self.frame.pack(fill="x", pady=(0, 10))
        
        # Create a container for the bottom section
        bottom_container = ttk.Frame(self.frame, style="Card.TFrame")
        bottom_container.pack(fill="x", padx=10, pady=10)
        
        # Left side: Process controls
        process_frame = ttk.Frame(bottom_container, style="Card.TFrame")
        process_frame.pack(side="left", fill="y", padx=(0, 20))
        
        # Process controls title
        process_title = ttk.Label(process_frame, 
                                 text="PROCESS CONTROLS", 
                                 style="Title.TLabel",
                                 font=("Segoe UI", 12, "bold"))
        process_title.pack(anchor="w", pady=(0, 10))
        
        # Process control buttons
        button_frame = ttk.Frame(process_frame, style="Card.TFrame")
        button_frame.pack(fill="x")
        
        # Kill Process button
        kill_btn = ttk.Button(button_frame, 
                             text="Kill Process", 
                             command=self.app.kill_process,
                             style="Danger.TButton")
        kill_btn.pack(side="left", padx=(0, 10))
        
        # Process Details button
        details_btn = ttk.Button(button_frame, 
                                text="Process Details", 
                                command=self.app.show_process_details,
                                style="Accent.TButton")
        details_btn.pack(side="left", padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(button_frame, 
                               text="Export Process List", 
                               command=self.app.export_process_list,
                               style="Success.TButton")
        export_btn.pack(side="left")
        
        # Center: System alerts
        alert_frame = ttk.Frame(bottom_container, style="Card.TFrame")
        alert_frame.pack(side="left", fill="y", expand=True, padx=20)
        
        # Alerts title
        alert_title = ttk.Label(alert_frame, 
                               text="SYSTEM ALERTS", 
                               style="Title.TLabel",
                               font=("Segoe UI", 12, "bold"))
        alert_title.pack(anchor="w", pady=(0, 10))
        
        # Alert thresholds
        threshold_frame = ttk.Frame(alert_frame, style="Card.TFrame")
        threshold_frame.pack(fill="x", pady=(0, 10))
        
        # CPU threshold
        ttk.Label(threshold_frame, text="CPU:", style="TLabel").pack(side="left", padx=(0, 5))
        self.cpu_threshold = ttk.Entry(threshold_frame, width=5)
        self.cpu_threshold.insert(0, "80")
        self.cpu_threshold.pack(side="left", padx=(0, 10))
        
        # Memory threshold
        ttk.Label(threshold_frame, text="Memory:", style="TLabel").pack(side="left", padx=(0, 5))
        self.mem_threshold = ttk.Entry(threshold_frame, width=5)
        self.mem_threshold.insert(0, "80")
        self.mem_threshold.pack(side="left", padx=(0, 10))
        
        # Disk threshold
        ttk.Label(threshold_frame, text="Disk:", style="TLabel").pack(side="left", padx=(0, 5))
        self.disk_threshold = ttk.Entry(threshold_frame, width=5)
        self.disk_threshold.insert(0, "90")
        self.disk_threshold.pack(side="left", padx=(0, 10))
        
        # Apply button
        ttk.Button(threshold_frame, text="Apply",
                   command=self.apply_thresholds,
                   style="Accent.TButton").pack(side="left")
        
        # Right side: Refresh rate
        refresh_frame = ttk.Frame(bottom_container, style="Card.TFrame")
        refresh_frame.pack(side="right", fill="y", padx=(20, 0))
        
        # Refresh rate title
        refresh_title = ttk.Label(refresh_frame, 
                                 text="REFRESH RATE", 
                                 style="Title.TLabel",
                                 font=("Segoe UI", 12, "bold"))
        refresh_title.pack(anchor="w", pady=(0, 10))
        
        # Refresh rate control
        rate_frame = ttk.Frame(refresh_frame, style="Card.TFrame")
        rate_frame.pack(fill="x")
        
        ttk.Label(rate_frame, text="Update interval (seconds):", style="TLabel").pack(side="left", padx=(0, 10))
        
        self.refresh_rate = ttk.Entry(rate_frame, width=5)
        self.refresh_rate.insert(0, "1")  # Default to 1 second
        self.refresh_rate.pack(side="left")
    
    def apply_thresholds(self):
        """Apply the alert thresholds"""
        try:
            cpu_threshold = int(self.cpu_threshold.get())
            mem_threshold = int(self.mem_threshold.get())
            disk_threshold = int(self.disk_threshold.get())
            self.app.update_alert_thresholds(cpu_threshold, mem_threshold, disk_threshold)
        except ValueError:
            # Error handling is done in the app class
            pass
    
    def get_refresh_rate(self):
        """Get the current refresh rate value"""
        try:
            return int(self.refresh_rate.get())
        except ValueError:
            return 1  # Default to 1 second if invalid value