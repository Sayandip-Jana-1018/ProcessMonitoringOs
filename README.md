### **Project Titile: Real Time Process Monitoring Dashboard**
- Authors: Sayandip Jana, Mohit Kumar Mishra, Anurag Pandey

### Screenshot of Dashboard:
![image](https://github.com/user-attachments/assets/fac667ef-b991-48ed-b3f1-4cff0055ebc2)

### 1. Project Overview
**Goals**:  
The goal is to transform your current task manager-like dashboard into an advanced, visually appealing, and innovative real-time process monitoring tool. It should not only display process states, CPU usage, and memory consumption but also empower administrators with efficient process management and proactive issue detection.

**Expected Outcomes**:  
- A sleek, modern, and intuitive graphical user interface (GUI) that enhances user experience.  
- Real-time monitoring with enriched data visualization and actionable insights.  
- Innovative features like anomaly detection, historical trends, and enhanced process management capabilities.  

**Scope**:  
The project focuses on local system monitoring (with potential for remote monitoring later), targeting administrators who need to oversee and manage system processes efficiently. It includes UI enhancements, new functionalities, and modular code organization while maintaining performance.

---

### 2. Module-Wise Breakdown
To make the project manageable and scalable, divide it into three core modules:

#### GUI Module
- **Purpose**: Handles the user interface, displaying process information, controls, and system metrics in a visually appealing way.  
- **Role**: Acts as the front-facing layer, ensuring usability and interactivity for administrators.

#### Data Visualization Module
- **Purpose**: Generates and updates real-time graphs and charts to represent system and process metrics.  
- **Role**: Provides visual insights into resource usage trends and patterns, making data easier to interpret.

#### ML Module
- **Purpose**: Implements intelligent features like anomaly detection or resource usage forecasting.  
- **Role**: Adds a proactive layer to identify potential issues before they escalate, enhancing the dashboard’s utility.

---

### 3. Functionalities
Here are key features for each module, with examples to illustrate their implementation:

#### GUI Module
- **Process List Display with Filtering and Sorting**:  
  Show a table of processes with columns like PID, Name, CPU%, Memory, etc., sortable by clicking column headers. Add a search bar to filter by name or user.  
  *Example*: Clicking "CPU%" sorts processes by descending CPU usage; typing "python" filters to Python processes.  
- **Context Menus**:  
  Right-click a process to access options like "Kill," "Change Priority," or "View Details."  
  *Example*: Right-clicking a process opens a menu with "Kill Process" and "Set Priority to High."  
- **Process Details Pane**:  
  Selecting a process shows detailed info (e.g., command line, start time) in a side panel.  
  *Example*: Clicking PID 1234 displays its full command line and thread count.  
- **Notification Area**:  
  Display alerts (e.g., high CPU usage) subtly within the UI instead of pop-ups.  
  *Example*: A red banner at the bottom says, "CPU at 85% - Check Process XYZ."  

#### Data Visualization Module
- **Real-Time Graphs**:  
  Plot CPU and memory usage over time with smooth updates. Add per-core CPU usage or memory breakdown.  
  *Example*: Two line graphs show total CPU% (red) and memory% (blue), updating every 2 seconds.  
- **Top Resource Consumers Bar Chart**:  
  Display a dynamic bar chart of the top 5 CPU or memory-intensive processes.  
  *Example*: Horizontal bars show "chrome.exe" at 40% CPU, "python.exe" at 25%, etc.  
- **Historical Data Visualization**:  
  Store and display usage trends for selected processes over time.  
  *Example*: A graph shows "notepad.exe" CPU usage for the last 10 minutes.  

#### ML Module
- **Anomaly Detection**:  
  Flag processes with unusual resource usage based on statistical thresholds (e.g., z-scores).  
  *Example*: "firefox.exe" using 90% CPU (3 standard deviations above average) gets highlighted in red.  
- **Resource Usage Forecasting**:  
  Predict future CPU/memory usage for "watched" processes using simple models like moving averages.  
  *Example*: A graph shows "java.exe" predicted to hit 80% memory in 5 minutes.  
- **Alert Generation**:  
  Trigger notifications when anomalies or forecasts exceed user-defined thresholds.  
  *Example*: "Warning: Process XYZ memory usage trending high - forecasted at 90%."  

---

### 4. Technology Recommendations
Given your current Python-based implementation, here’s a tailored tech stack:

- **Programming Language**:  
  - **Python**: Stick with Python for consistency and its rich ecosystem of libraries.  

- **Libraries and Tools**:  
  - **GUI**:  
    - **Tkinter with ttk**: Use themed widgets (`ttk`) for a modern look. Consider `ttkbootstrap` for Bootstrap-inspired styles or explore **PyQt/PySide** for more advanced UI capabilities.  
  - **Data Visualization**:  
    - **Matplotlib**: Continue using it for real-time plots, enhanced with `seaborn` for better aesthetics. Alternatively, **Plotly** offers interactive plots embeddable in Tkinter.  
  - **ML**:  
    - **NumPy**: For statistical anomaly detection (e.g., mean, standard deviation).  
    - **Scikit-learn**: For lightweight ML models like Isolation Forest (optional).  
  - **Data Collection**:  
    - **psutil**: Already in use—perfect for process and system metrics.  
  - **Storage (Optional)**:  
    - **Collections.deque**: For in-memory rolling windows of historical data.  
    - **SQLite**: If persistent storage is needed later (e.g., for snapshots).  

- **Additional Tools**:  
  - **Threading**: Use Python’s `threading` module (as in your code) for non-blocking updates.  
  - **Pillow**: For adding icons or images to buttons in Tkinter.  

---

### 5. Execution Plan
Here’s a step-by-step guide to implement the enhancements efficiently:

#### Step 1: Modernize the GUI
- **Reorganize Layout**:  
  - Use a grid layout with `ttk.Frame`:  
    - Top: Toolbar (search bar, action buttons with icons).  
    - Middle: Process list (`ttk.Treeview`).  
    - Bottom: Graphs and notification area.  
  - *Tip*: Use `grid()` instead of `pack()` for precise control.  
- **Apply Modern Styling**:  
  - Integrate `ttkbootstrap` or a custom theme (e.g., "azure").  
  - Add icons to buttons using `PIL` (e.g., trash icon for "Kill").  
  - Use a dark theme with accent colors (e.g., gray background, red for alerts).  
- **Enhance Interactivity**:  
  - Add sorting to `Treeview` columns (e.g., `tree.heading("CPU%", command=sort_by_cpu)`).  
  - Implement context menus with `tk.Menu`.  
  - Create a details pane with `ttk.LabelFrame`.  

#### Step 2: Improve Data Visualization
- **Enhance Graphs**:  
  - Add subplots for per-core CPU usage or memory breakdown in `matplotlib`.  
  - Use `plt.style.use('seaborn-darkgrid')` for a modern look.  
- **Add Top Consumers Chart**:  
  - Create a bar chart updating every 5 seconds with top 5 processes by CPU/memory.  
  - *Tip*: Use a separate `FigureCanvasTkAgg` instance.  
- **Enable Historical Data**:  
  - Store data in a `deque` (e.g., last 10 minutes, 200 points).  
  - Plot historical trends for selected processes on click.  

#### Step 3: Implement Innovative Features
- **Historical Data Tracking**:  
  - Modify `get_processes()` to append data to a dictionary of `deque` objects per PID.  
  - Display trends in a new graph when a process is selected.  
- **Anomaly Detection**:  
  - Calculate rolling mean and standard deviation for CPU/memory per process.  
  - Highlight processes exceeding 3 standard deviations in the `Treeview` with tags (e.g., `tree.tag_configure('anomaly', background='yellow')`).  
- **Notifications**:  
  - Replace `messagebox` alerts with a `ttk.Label` in a notification frame that updates dynamically.  

#### Step 4: Optimize Performance
- **Efficient Updates**:  
  - Update only changed rows in `Treeview` instead of clearing and repopulating.  
  - Use `after()` with adjustable intervals (e.g., 2-5 seconds) based on system load.  
- **Threading**:  
  - Keep graph updates in a separate thread (as you’ve done).  
  - Add a "Pause" button to stop updates temporarily.  

#### Step 5: Test and Refine
- **Testing**:  
  - Simulate high CPU/memory usage (e.g., run a stress test) to verify alerts and visuals.  
- **User Feedback**:  
  - Adjust UI elements (e.g., font size, colors) based on usability feedback.  
- **Documentation**:  
  - Add tooltips or a help section explaining features.  

---

### Suggested Code Changes
Here’s how to apply some of these ideas to your existing code:

#### Modern UI with ttkbootstrap
```python
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

root = ttk.Window(themename="darkly")  # Modern dark theme
root.title("Real-Time Process Monitoring Dashboard")
root.geometry("900x600")

tree = ttk.Treeview(root, columns=columns, show="headings", style="primary.Treeview")
# ... rest of your Treeview setup ...

kill_btn = ttk.Button(btn_frame, text="Kill Process", command=kill_process, style="danger.TButton")
```

#### Historical Data Tracking
```python
from collections import deque, defaultdict

process_history = defaultdict(lambda: {'cpu': deque(maxlen=200), 'mem': deque(maxlen=200)})

def get_processes():
    process_list = []
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
        info = proc.info
        info['memory_info'] = info['memory_info'].rss // 1024**2
        process_list.append(info)
        process_history[info['pid']]['cpu'].append(info['cpu_percent'])
        process_history[info['pid']]['mem'].append(info['memory_info'])
    return process_list
```

#### Anomaly Detection
```python
import numpy as np

def check_anomalies():
    for pid, data in process_history.items():
        cpu_data = list(data['cpu'])
        if len(cpu_data) > 10:  # Enough data points
            mean, std = np.mean(cpu_data), np.std(cpu_data)
            if cpu_data[-1] > mean + 3 * std:
                tree.tag_configure('anomaly', background='yellow')
                tree.item(tree.get_children()[pid_index], tags='anomaly')
    root.after(5000, check_anomalies)
```

---

### Innovative Enhancements
Beyond the basics, consider these innovative additions:
- **Process Grouping**: Group processes by application or user in the `Treeview` for better organization.  
- **Snapshot Feature**: Save current process states to a CSV file for later comparison.  
- **Remote Monitoring (Future)**: Use `paramiko` for SSH to monitor remote machines.  
- **Predictive Alerts**: Forecast system overload based on trends and alert administrators.  

---

### Conclusion
By modernizing the UI with a sleek theme, enhancing visualizations with historical data and top consumer charts, and adding anomaly detection, your dashboard will stand out as both functional and innovative. Start with GUI improvements, then layer in visualization and ML features, ensuring performance remains smooth. This approach balances your existing code with significant upgrades tailored to the project’s goals.

# Advanced Process Monitoring Dashboard

A sophisticated, feature-rich system monitoring application built with Python that provides real-time insights into system performance with AI-powered analytics.

![Dashboard Screenshot](https://github.com/user-attachments/assets/0b60728d-59d7-4ea0-b62a-00d32fe18770)

## 🌟 Features

### 💻 System Monitoring
- **Real-time Resource Tracking**: Monitor CPU, memory, disk, and network usage with beautiful gauges and graphs
- **Process Management**: View, filter, sort, and manage all running processes
- **Detailed Process Information**: Get comprehensive details about any process including memory usage, CPU utilization, threads, and more
- **Process Control**: Kill processes, change priorities, and manage system resources efficiently

### 📊 Data Visualization
- **Interactive Performance Graphs**: Track system performance over time with customizable time ranges (5 minutes, 15 minutes, 1 hour)
- **Resource Usage Gauges**: Visual indicators of current system resource utilization
- **Process Intelligence**: Visualize process relationships and dependencies with intelligent categorization
- **Customizable Themes**: Multiple theme options including Sunrise, Twilight, Midnight, and Forest

### 🧠 Process Intelligence
- **Resource Usage Analysis**: Detailed breakdown of system resource consumption
- **Process Relations**: Visualization of relationships between processes
- **System Summary**:
  - Total process count
  - Memory usage statistics
  - CPU usage overview
- **Resource-Intensive Process Identification**:
  - CPU-intensive processes with usage statistics
  - Memory-intensive processes with detailed memory consumption
- **Resource Trends**: Tracking and analysis of usage patterns over time
- **Optimization Suggestions**: Recommendations for improving system performance

### 🤖 AI Insights
- **Data Collection Tracking**: Shows how long metrics have been collected (e.g., "0.0 mins")
- **Model Training Status**: Indicates AI model training progress
- **AI Status Monitoring**: Shows current state of AI components
- **Predictive Analytics**:
  - CPU usage predictions with current and forecasted values
  - Trend analysis (stable, increasing, decreasing)
- **Anomaly Detection**: Identifies unusual system behavior with detailed analysis
- **Interactive AI Buttons**: Dedicated buttons for predictions and anomaly detection

### 💬 Virtual Assistant
- **Conversational Interface**: Chat-based interaction for system queries
- **Quick Command Buttons**: One-click access to common information:
  - CPU details
  - Memory status
  - Disk information
  - Network statistics
  - Process lists
  - Help documentation
- **Natural Language Processing**: Ability to understand and respond to queries about system performance
- **Contextual Responses**: Provides relevant system information based on user questions

### 📝 Smart Recommendations
- **System Warnings**: Alerts when resource usage approaches high levels
- **Optimization Suggestions**:
  - CPU optimization recommendations (e.g., "CPU usage is optimal at 1.1%")
  - Memory optimization tips (e.g., "Elevated memory usage at 65.6%")
  - Application management advice (e.g., "Restart memory-intensive applications periodically")
- **Resource Management Tips**: Contextual advice based on current system state

## 🛠️ Technical Implementation

### Architecture
The application follows a modular architecture with clear separation of concerns:

```
ProcessMonitoringOs/
├── main.py              # Application entry point
├── config.py            # Configuration settings and themes
├── ui/                  # User interface components
│   ├── app.py           # Main application window
│   ├── sections.py      # UI sections (Top, Middle)
│   ├── footer.py        # Footer component
│   ├── gauges.py        # Resource usage gauges
│   └── graphs.py        # Performance graphs
├── utils/               # Utility functions
│   ├── process_utils.py # Process management utilities
│   └── ai_utils.py      # AI and ML components
```

### Key Components

#### UI Framework
- Built with **Tkinter** and **ttk** for a modern, responsive interface
- Custom-styled widgets with themed components:
  - Circular gauges with dynamic color changes
  - Custom buttons with hover effects
  - Tabular data with alternating row colors
  - Responsive charts with interactive elements
- Sectioned layout with three main areas:
  - Top section: System Monitor, AI Insights, Smart Recommendations
  - Middle section: Process List and System Performance graphs
  - Bottom section: Status bar and controls

#### Data Processing
- **psutil** for efficient system metrics collection:
  - CPU statistics (usage, cores, threads)
  - Memory information (used, available, percent)
  - Disk usage (free space, used space, percent)
  - Process details (PID, name, CPU%, memory usage)
- Real-time data processing with optimized update intervals
- Efficient data structures for storing historical performance data

#### AI & Machine Learning
- **Anomaly Detection**: Implemented using Isolation Forest algorithm from scikit-learn
  - Identifies unusual patterns in resource usage
  - Provides severity assessment of detected anomalies
- **Predictive Analytics**: Time-series forecasting with ARIMA models from statsmodels
  - Predicts future resource usage based on historical patterns
  - Calculates trend directions (stable, increasing, decreasing)
- **Process Intelligence**:
  - Categorizes processes by type and function
  - Identifies relationships between processes
  - Analyzes resource consumption patterns

#### Visualization
- **Matplotlib** for high-quality, customizable graphs and charts:
  - Line charts for temporal data
  - Bar charts for comparative analysis
  - Custom visualizations for process relationships
- Custom gauge widgets implemented with Tkinter canvas:
  - Dynamic color changes based on usage levels
  - Smooth animations for value transitions
  - Informative tooltips on hover
- Process list with sortable columns and search functionality

## 💡 Advanced Features

### Process Intelligence
The Process Intelligence feature provides deep insights into system processes:

- **System Summary**:
  - Total process count with active/inactive breakdown
  - Memory usage statistics across process categories
  - CPU utilization patterns by process type

- **Process Categorization**:
  - **System Processes**: Core OS components (e.g., System, Registry)
  - **Background Services**: Services running without user interaction
  - **User Applications**: Programs launched by the user (e.g., Windsurf.exe)
  - **Development Tools**: Programming and development utilities
  - **Media & Graphics**: Audio/video/graphics applications
  - **Network Services**: Internet and network-related processes

- **Resource Usage Analysis**:
  - Identifies CPU-intensive processes with usage statistics
  - Highlights memory-intensive processes with detailed memory consumption
  - Tracks resource usage trends over time

- **Process Relationships**:
  - Parent-child relationships between processes
  - Dependency mapping between related processes
  - Impact analysis of process termination

### AI Insights
The AI components provide sophisticated analysis and predictions:

- **Data Collection and Training**:
  - Continuous collection of system metrics
  - Periodic model training based on accumulated data
  - Status indicators for training progress

- **Anomaly Analysis**:
  - Multi-level anomaly detection (critical, warning, normal)
  - Detailed breakdown of detected anomalies by resource type
  - Severity assessment with recommended actions
  - Historical anomaly tracking for pattern recognition

- **Resource Predictions**:
  - Short-term forecasts of CPU, memory, and disk usage
  - Trend analysis with directional indicators
  - Confidence levels for predictions
  - Comparative analysis of predicted vs. actual values

- **Performance Optimization**:
  - Context-aware recommendations based on system state
  - Prioritized suggestions for resource management
  - Impact assessment of recommended actions

### Virtual Assistant
The integrated virtual assistant provides an intuitive interface for system interaction:

- **Conversational Capabilities**:
  - Natural language understanding for system queries
  - Contextual responses based on current system state
  - Helpful suggestions for common tasks

- **Information Retrieval**:
  - Detailed CPU information (usage, cores, threads)
  - Memory statistics (used, available, allocation)
  - Disk space analysis (free space, usage patterns)
  - Network activity monitoring (sent/received data)
  - Process information (running processes, resource usage)

- **Quick Commands**:
  - One-click buttons for common queries
  - Instant access to system information
  - Streamlined interface for frequent tasks

- **Help and Documentation**:
  - Built-in help system with usage examples
  - Troubleshooting suggestions
  - Feature explanations and tips

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Required packages:
  - **tkinter**: UI framework
  - **psutil**: System metrics collection
  - **matplotlib**: Data visualization
  - **numpy** & **pandas**: Data processing
  - **scikit-learn**: Machine learning components
  - **statsmodels**: Time series analysis

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ProcessMonitoringOs.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## 🎨 Themes

The application features a vibrant, modern UI with a customizable color scheme:

- **Current Theme**: Bright theme with pink accent colors
- **UI Elements**:
  - Section headers with distinct color coding
  - Circular gauges with percentage indicators
  - Clean, readable fonts for all text elements
  - Consistent styling across all components

## 📈 Performance Considerations

- **Efficient Resource Usage**:
  - The application is optimized to use minimal resources while monitoring
  - Typical CPU usage is less than 2% during normal operation
  - Memory footprint is kept below 100MB

- **Data Management**:
  - Optimized data collection intervals (configurable)
  - Efficient storage of historical data
  - Automatic cleanup of old metrics to prevent memory leaks

- **Responsive UI**:
  - Background processing for intensive tasks
  - Non-blocking updates for performance graphs
  - Throttled refresh rates for smooth operation

## 🔧 Customization

Users can customize various aspects of the application:

- **Display Options**:
  - Process list columns and sorting
  - Graph time ranges and visualization styles
  - Gauge appearance and thresholds

- **Monitoring Settings**:
  - Update intervals for metrics collection
  - Alert thresholds for resource usage
  - Process filtering and categorization rules

- **AI Components**:
  - Training frequency for ML models
  - Sensitivity settings for anomaly detection
  - Prediction horizon for forecasting

## 👥 Contributors

- Sayandip Jana
- Mohit Kumar Mishra
- Anurag Pandey

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with ❤️ and Python*
