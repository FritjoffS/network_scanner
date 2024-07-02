import psutil
import time
import logging
from collections import deque
import socket
import subprocess
import sys
import platform
import speedtest
import requests

logging.basicConfig(filename='network_monitor_v1.2.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class NetworkMonitor:
    def __init__(self, target_ip):
        self.previous_bytes_sent = psutil.net_io_counters().bytes_sent
        self.previous_bytes_recv = psutil.net_io_counters().bytes_recv
        self.speed_history = deque(maxlen=60)
        self.anomaly_threshold = 2
        self.target_ip = target_ip
        self.connection_history = deque(maxlen=10)

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
            return False

        mean = sum(self.speed_history) / len(self.speed_history)
        std_dev = (sum((x - mean) ** 2 for x in self.speed_history) / len(self.speed_history)) ** 0.5

        return abs(current_speed - mean) > (self.anomaly_threshold * std_dev)

    def check_latency(self):
        try:
            result = subprocess.run(["ping", "-c", "4", self.target_ip], 
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                latency = float(result.stdout.split('/')[-3])
                self.connection_history.append(latency)
                logging.info(f"Latency to {self.target_ip}: {latency} ms")
                return latency
            else:
                logging.warning(f"Ping to {self.target_ip} failed")
                return None
        except subprocess.TimeoutExpired:
            logging.warning(f"Ping to {self.target_ip} timed out")
            return None
        except Exception as e:
            logging.error(f"Error checking latency: {str(e)}")
            return None

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

    def check_dns_resolution(self):
        try:
            socket.gethostbyname('www.google.com')
            logging.info("DNS resolution: OK")
            return True
        except socket.gaierror:
            logging.warning("DNS resolution: FAILED")
            return False

    def check_internet_speed(self):
        try:
            st = speedtest.Speedtest()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            logging.info(f"Download speed: {download_speed:.2f} Mbps")
            logging.info(f"Upload speed: {upload_speed:.2f} Mbps")
            return download_speed, upload_speed
        except Exception as e:
            logging.error(f"Error checking internet speed: {str(e)}")
            return None, None

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
                logging.info(f"Packet loss to {self.target_ip}: {loss:.2f}%")
                return loss
            else:
                logging.warning(f"Packet loss test to {self.target_ip} failed")
                return None
        except subprocess.TimeoutExpired:
            logging.warning(f"Packet loss test to {self.target_ip} timed out")
            return None
        except Exception as e:
            logging.error(f"Error checking packet loss: {str(e)}")
            return None

    def check_http_response(self, url="http://www.google.com"):
        try:
            response = requests.get(url, timeout=5)
            logging.info(f"HTTP response from {url}: {response.status_code}")
            return response.status_code
        except requests.RequestException as e:
            logging.error(f"Error checking HTTP response: {str(e)}")
            return None

    def troubleshoot(self):
        self.check_dns_resolution()
        self.check_latency()
        self.check_packet_loss()
        self.check_http_response()
        download_speed, upload_speed = self.check_internet_speed()
        stability = self.analyze_connection_stability()
        logging.info(f"Connection stability: {stability}")

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