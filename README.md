# Network Monitor

Network Monitor is a Python-based GUI application that provides real-time monitoring and analysis of network activity. It offers a user-friendly interface for tracking network speeds, detecting anomalies, and performing basic network diagnostics.

## Features

- Real-time monitoring of network upload and download speeds
- Customizable anomaly detection
- Visual representation of network activity through graphs and progress bars
- Basic network diagnostics including DNS resolution, latency checks, and packet loss analysis
- Adjustable monitoring parameters through the GUI
- Detailed logging of network events and anomalies

## Requirements

- Python 3.7+
- PyQt5
- pyqtgraph
- psutil
- speedtest-cli
- requests

## Installation

1. Clone this repository:

git clone https://github.com/yourusername/network-monitor.git
cd network-monitor

2. Install the required dependencies:

pip install pyqt5 pyqtgraph psutil speedtest-cli requests


## Usage

Run the application using Python:

python network_monitor.py


Once the application starts:

1. Enter the target IP address you want to monitor.
2. Adjust the monitoring settings if needed:
   - Anomaly Threshold: Sensitivity of anomaly detection (default: 2)
   - Check Interval: Time between each network check in seconds (default: 1)
   - History Size: Number of data points to keep in history (default: 60)
3. Click "Start Monitoring" to begin.
4. The application will display real-time network speeds and a graph of recent activity.
5. Any detected anomalies or network issues will be logged in the text area.
6. Click "Stop Monitoring" to end the session.

## Customization

You can adjust the following parameters through the GUI:

- Target IP: The IP address to monitor and use for network tests
- Anomaly Threshold: How sensitive the anomaly detection should be
- Check Interval: How frequently the network should be checked
- History Size: How many recent data points should be kept for analysis and graphing

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed.
2. Check that you have the necessary permissions to perform network operations.
3. Some features may require running the application with administrator/root privileges.

## Contributing

Contributions to the Network Monitor are welcome! Please feel free to submit pull requests, create issues or spread the word.

This is what is going on:

Add a graph to visualize network speed over time. - ok
Implement a feature to save logs to a file.
Add options to customize anomaly thresholds and other parameters through the GUI. - ok
Incorporate a feature to schedule monitoring sessions.
Add system tray integration for minimized monitoring.
Implement alerts or notifications for significant anomalies.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the PyQt, pyqtgraph, and psutil teams for their excellent libraries.
- Inspired by the need for a user-friendly, customizable network monitoring tool.

