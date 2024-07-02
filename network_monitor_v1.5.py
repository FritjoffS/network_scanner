import sys
import time
import logging
from collections import deque
import socket
import subprocess
import psutil
import speedtest
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QTextEdit, QProgressBar, 
                             QSpinBox, QDoubleSpinBox, QFormLayout, QGroupBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg

logging.basicConfig(filename='network_monitor_v1.5.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkMonitor(QThread):
    update_signal = pyqtSignal(str)
    speed_update_signal = pyqtSignal(int, int)
    graph_update_signal = pyqtSignal(int, int)

    def __init__(self, target_ip, anomaly_threshold=2, check_interval=1, history_size=60):
        super().__init__()
        self.target_ip = target_ip
        self.anomaly_threshold = anomaly_threshold
        self.check_interval = check_interval
        self.previous_bytes_sent = psutil.net_io_counters().bytes_sent
        self.previous_bytes_recv = psutil.net_io_counters().bytes_recv
        self.speed_history = deque(maxlen=history_size)
        self.connection_history = deque(maxlen=10)
        self.running = True

    def run(self):
        while self.running:
            bytes_sent, bytes_recv = self.get_network_speed()
            total_bytes = bytes_sent + bytes_recv
            self.speed_update_signal.emit(bytes_sent, bytes_recv)
            self.graph_update_signal.emit(bytes_sent, bytes_recv)
            self.update_signal.emit(f"Network activity: {total_bytes} bytes/sec")

            if self.detect_anomalies(total_bytes):
                self.update_signal.emit("Anomaly detected in network activity!")
                self.troubleshoot()

            time.sleep(self.check_interval)

    def stop(self):
        self.running = False

    def get_network_speed(self):
        current_bytes_sent = psutil.net_io_counters().bytes_sent
        current_bytes_recv = psutil.net_io_counters().bytes_recv

        bytes_sent = current_bytes_sent - self.previous_bytes_sent
        bytes_recv = current_bytes_recv - self.previous_bytes_recv

        self.previous_bytes_sent = current_bytes_sent
        self.previous_bytes_recv = current_bytes_recv

        return bytes_sent, bytes_recv

    def detect_anomalies(self, current_speed):
        self.speed_history.append(current_speed)
        if len(self.speed_history) < 10:
            return False
        mean = sum(self.speed_history) / len(self.speed_history)
        std_dev = (sum((x - mean) ** 2 for x in self.speed_history) / len(self.speed_history)) ** 0.5
        return abs(current_speed - mean) > (self.anomaly_threshold * std_dev)

    def troubleshoot(self):
        self.check_dns_resolution()
        self.check_latency()
        self.check_packet_loss()
        self.check_http_response()
        download_speed, upload_speed = self.check_internet_speed()
        stability = self.analyze_connection_stability()
        self.update_signal.emit(f"Connection stability: {stability}")

    def check_dns_resolution(self):
        try:
            socket.gethostbyname('www.google.com')
            self.update_signal.emit("DNS resolution: OK")
        except socket.gaierror:
            self.update_signal.emit("DNS resolution: FAILED")

    def check_latency(self):
        try:
            result = subprocess.run(["ping", "-c", "4", self.target_ip], 
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                latency = float(result.stdout.split('/')[-3])
                self.connection_history.append(latency)
                self.update_signal.emit(f"Latency to {self.target_ip}: {latency} ms")
            else:
                self.update_signal.emit(f"Ping to {self.target_ip} failed")
        except subprocess.TimeoutExpired:
            self.update_signal.emit(f"Ping to {self.target_ip} timed out")
        except Exception as e:
            self.update_signal.emit(f"Error checking latency: {str(e)}")

    def check_packet_loss(self):
        try:
            result = subprocess.run(["ping", "-c", "10", self.target_ip], 
                                    capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                sent = received = 0
                for line in result.stdout.splitlines():
                    if "packets transmitted" in line:
                        sent, received = map(int, line.split()[0:3:2])
                        break
                loss = (sent - received) / sent * 100 if sent > 0 else 0
                self.update_signal.emit(f"Packet loss to {self.target_ip}: {loss:.2f}%")
            else:
                self.update_signal.emit(f"Packet loss test to {self.target_ip} failed")
        except subprocess.TimeoutExpired:
            self.update_signal.emit(f"Packet loss test to {self.target_ip} timed out")
        except Exception as e:
            self.update_signal.emit(f"Error checking packet loss: {str(e)}")

    def check_http_response(self, url="http://www.google.com"):
        try:
            response = requests.get(url, timeout=5)
            self.update_signal.emit(f"HTTP response from {url}: {response.status_code}")
        except requests.RequestException as e:
            self.update_signal.emit(f"Error checking HTTP response: {str(e)}")

    def check_internet_speed(self):
        try:
            st = speedtest.Speedtest()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            self.update_signal.emit(f"Download speed: {download_speed:.2f} Mbps")
            self.update_signal.emit(f"Upload speed: {upload_speed:.2f} Mbps")
            return download_speed, upload_speed
        except Exception as e:
            self.update_signal.emit(f"Error checking internet speed: {str(e)}")
            return None, None

    def analyze_connection_stability(self):
        if len(self.connection_history) < 5:
            return "Not enough data for stability analysis"
        variations = [abs(self.connection_history[i] - self.connection_history[i-1]) 
                      for i in range(1, len(self.connection_history))]
        avg_variation = sum(variations) / len(variations)
        if avg_variation < 5:
            return "Stable connection"
        elif avg_variation < 20:
            return "Moderate fluctuations"
        else:
            return "Unstable connection"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Monitor")
        self.setGeometry(100, 100, 800, 800)  # Increased height for new controls

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Settings Group
        settings_group = QGroupBox("Monitor Settings")
        settings_layout = QFormLayout()

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter target IP")
        settings_layout.addRow("Target IP:", self.ip_input)

        self.anomaly_threshold_input = QDoubleSpinBox()
        self.anomaly_threshold_input.setRange(0.1, 10)
        self.anomaly_threshold_input.setSingleStep(0.1)
        self.anomaly_threshold_input.setValue(2)
        settings_layout.addRow("Anomaly Threshold:", self.anomaly_threshold_input)

        self.check_interval_input = QDoubleSpinBox()
        self.check_interval_input.setRange(0.1, 10)
        self.check_interval_input.setSingleStep(0.1)
        self.check_interval_input.setValue(1)
        settings_layout.addRow("Check Interval (s):", self.check_interval_input)

        self.history_size_input = QSpinBox()
        self.history_size_input.setRange(10, 300)
        self.history_size_input.setSingleStep(10)
        self.history_size_input.setValue(60)
        settings_layout.addRow("History Size:", self.history_size_input)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Start/Stop buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Monitoring")
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        main_layout.addLayout(button_layout)

        # Network speed display
        speed_layout = QHBoxLayout()
        self.upload_bar = QProgressBar()
        self.download_bar = QProgressBar()
        speed_layout.addWidget(QLabel("Upload:"))
        speed_layout.addWidget(self.upload_bar)
        speed_layout.addWidget(QLabel("Download:"))
        speed_layout.addWidget(self.download_bar)
        main_layout.addLayout(speed_layout)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        main_layout.addWidget(self.log_display)

        # Graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Network Speed Over Time")
        self.graph_widget.setLabel('left', 'Speed (bytes/sec)')
        self.graph_widget.setLabel('bottom', 'Time (seconds)')
        self.graph_widget.showGrid(x=True, y=True)
        self.upload_curve = self.graph_widget.plot(pen='b', name='Upload')
        self.download_curve = self.graph_widget.plot(pen='r', name='Download')
        self.graph_widget.addLegend()
        main_layout.addWidget(self.graph_widget)

        central_widget.setLayout(main_layout)

        # Data for graph
        self.times = []
        self.upload_speeds = []
        self.download_speeds = []
        self.start_time = time.time()

        # Connect buttons
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)

        self.monitor_thread = None

    def start_monitoring(self):
        target_ip = self.ip_input.text()
        if not target_ip:
            self.log_display.append("Please enter a target IP address.")
            return

        anomaly_threshold = self.anomaly_threshold_input.value()
        check_interval = self.check_interval_input.value()
        history_size = self.history_size_input.value()

        self.monitor_thread = NetworkMonitor(target_ip, anomaly_threshold, check_interval, history_size)
        self.monitor_thread.update_signal.connect(self.update_log)
        self.monitor_thread.speed_update_signal.connect(self.update_speed_bars)
        self.monitor_thread.graph_update_signal.connect(self.update_graph)
        self.monitor_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.ip_input.setEnabled(False)
        self.anomaly_threshold_input.setEnabled(False)
        self.check_interval_input.setEnabled(False)
        self.history_size_input.setEnabled(False)

        # Reset graph data
        self.times = []
        self.upload_speeds = []
        self.download_speeds = []
        self.start_time = time.time()

    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.ip_input.setEnabled(True)
        self.anomaly_threshold_input.setEnabled(True)
        self.check_interval_input.setEnabled(True)
        self.history_size_input.setEnabled(True)

    def update_log(self, message):
        self.log_display.append(message)

    def update_speed_bars(self, upload, download):
        self.upload_bar.setValue(min(upload // 1024, 100))  # Convert to KB and cap at 100
        self.download_bar.setValue(min(download // 1024, 100))  # Convert to KB and cap at 100

    def update_graph(self, upload, download):
        current_time = time.time() - self.start_time
        self.times.append(current_time)
        self.upload_speeds.append(upload)
        self.download_speeds.append(download)

        # Keep only the last 'history_size' seconds of data
        history_size = self.history_size_input.value()
        if len(self.times) > history_size:
            self.times = self.times[-history_size:]
            self.upload_speeds = self.upload_speeds[-history_size:]
            self.download_speeds = self.download_speeds[-history_size:]

        self.upload_curve.setData(self.times, self.upload_speeds)
        self.download_curve.setData(self.times, self.download_speeds)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
