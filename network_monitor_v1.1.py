import psutil
import time
import logging
from collections import deque
import socket
import subprocess
import sys

# Set up logging
logging.basicConfig(filename='network_monitor_v1.1.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkMonitor:
    def __init__(self, target_ip):
        self.previous_bytes_sent = psutil.net_io_counters().bytes_sent
        self.previous_bytes_recv = psutil.net_io_counters().bytes_recv
        self.speed_history = deque(maxlen=60)
        self.anomaly_threshold = 2
        self.target_ip = target_ip

    def get_network_speed(self):
        try:
            current_bytes_sent = psutil.net_io_counters().bytes_sent
            current_bytes_recv = psutil.net_io_counters().bytes_recv

            bytes_sent = current_bytes_sent - self.previous_bytes_sent
            bytes_recv = current_bytes_recv - self.previous_bytes_recv

            self.previous_bytes_sent = current_bytes_sent
            self.previous_bytes_recv = current_bytes_recv

            return bytes_sent, bytes_recv
        except Exception as e:
            logging.error(f"Error getting network speed: {str(e)}")
            return 0, 0

    def detect_anomalies(self, current_speed):
        self.speed_history.append(current_speed)
        
        if len(self.speed_history) < 10:
            return False  # Not enough data to detect anomalies yet

        mean = sum(self.speed_history) / len(self.speed_history)
        std_dev = (sum((x - mean) ** 2 for x in self.speed_history) / len(self.speed_history)) ** 0.5

        return abs(current_speed - mean) > (self.anomaly_threshold * std_dev)

    def troubleshoot(self):
        try:
            # Check DNS resolution
            socket.gethostbyname('www.google.com')
            logging.info("DNS resolution: OK")
        except socket.gaierror:
            logging.warning("DNS resolution: FAILED")

        try:
            # Check connectivity to the specified IP
            subprocess.check_call(["ping", "-c", "1", self.target_ip],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"Connectivity to {self.target_ip}: OK")
        except subprocess.CalledProcessError:
            logging.warning(f"Connectivity to {self.target_ip}: FAILED")

    def monitor(self):
        try:
            while True:
                bytes_sent, bytes_recv = self.get_network_speed()
                total_bytes = bytes_sent + bytes_recv
                
                logging.info(f"Network activity: {total_bytes} bytes/sec")

                if self.detect_anomalies(total_bytes):
                    logging.warning("Anomaly detected in network activity!")
                    self.troubleshoot()

                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Monitoring stopped by user.")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    try:
        target_ip = input("Enter the IP address you want to monitor: ")
        monitor = NetworkMonitor(target_ip)
        monitor.monitor()
    except Exception as e:
        logging.critical(f"Critical error: {str(e)}")
        sys.exit(1)