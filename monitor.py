import json
import paramiko
import time
import re
from typing import Optional, Dict

class RemoteMonitor:
    def __init__(self, hostname: str, username: str, key_filename: Optional[str] = None,
                password: Optional[str] = None, port: int = 22, label: Optional[str] = None):
        self.hostname = hostname # IP address or hostname
        self.username = username # SSH username
        self.key_filename = key_filename # path to private key file
        self.password = password # optional password (if not using key)
        self.port = port # SSH port, default 22
        self.label = label or hostname  # a friendly name

    def _connect(self) -> paramiko.SSHClient:
        """Establishes an SSH connection and returns the client."""
        client = paramiko.SSHClient() # create SSH client
        client.load_system_host_keys() # load known hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # auto-add unknown hosts
        client.connect(hostname=self.hostname, 
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_filename,
                    password=self.password,
                    timeout=10)
        return client

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Polls the remote host and returns metrics (or error)."""
        metrics: Dict[str, Optional[float]] = {}
        client: Optional[paramiko.SSHClient] = None

        try:
            client = self._connect()

            # Commands
            stdin, stdout, stderr = client.exec_command("df -h /") # disk usage for root "/"
            df_out = stdout.read().decode()

            stdin, stdout, stderr = client.exec_command("free -m") # memory in MB
            free_out = stdout.read().decode()

            stdin, stdout, stderr = client.exec_command("cat /proc/loadavg") # load average
            loadavg_out = stdout.read().decode()

            stdin, stdout, stderr = client.exec_command("cat /sys/class/thermal/thermal_zone0/temp") # temperature
            temp_raw = stdout.read().decode().strip()

            # Parse disk usage (root "/")
            match = re.search(r"\s+(\d+)%\s+/", df_out) # regex to find "Used%" for "/"
            if match:
                metrics['disk_root_used_pct'] = float(match.group(1)) # percentage used
            else:
                metrics['disk_root_used_pct'] = None # if parsing fails

            # Parse memory
            for line in free_out.splitlines(): # look for line starting with "Mem:"
                if line.startswith("Mem:"): # found memory line
                    parts = line.split() # split by whitespace
                    metrics['mem_total_mb'] = float(parts[1]) # total memory in MB
                    metrics['mem_free_mb'] = float(parts[6]) if len(parts) >= 7 else float(parts[3]) # free memory in MB
                    break
            else:
                metrics['mem_total_mb'] = None # if parsing fails
                metrics['mem_free_mb'] = None # if parsing fails

            # Parse load average
            parts = loadavg_out.split() # split by whitespace
            if len(parts) >= 3: # need at least 3 parts
                metrics['cpu_load_1m'] = float(parts[0]) # 1 minute load average
                metrics['cpu_load_5m'] = float(parts[1]) # 5 minute load average
                metrics['cpu_load_15m'] = float(parts[2]) # 15 minute load average
            else:
                metrics['cpu_load_1m'] = metrics['cpu_load_5m'] = metrics['cpu_load_15m'] = None # if parsing fails

            # Parse temperature
            try:
                temp_c = float(temp_raw) / 1000.0 # convert millidegree to degree
                metrics['temperature_c'] = temp_c # temperature in Celsius
            except (ValueError, TypeError): # if conversion fails
                metrics['temperature_c'] = None # if parsing fails

            return metrics

        except Exception as e:
            return {"error": str(e)}

        finally:
            if client is not None:
                client.close()

def load_hosts_from_json(json_file_path: str):
    """Reads a JSON file which defines a list of hosts. Returns a list of RemoteMonitor objects."""
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    hosts_config = data.get("hosts", [])
    monitors = []

    for h in hosts_config:
        hostname = h.get("hostname")
        username = h.get("username")
        key_filename = h.get("key_filename")
        password = h.get("password")  # optional
        port = h.get("port", 22)
        label = h.get("label")  # optional friendly name

        if hostname and username: # must have at least hostname and username
            mon = RemoteMonitor(hostname=hostname,
                                username=username,
                                key_filename=key_filename,
                                password=password,
                                port=port,
                                label=label)
            monitors.append(mon)
        else:
            print(f"[Warning] Skipping invalid host config: {h}") # log warning for invalid config

    return monitors

def main():
    hosts_file = "hosts.json"
    monitors = load_hosts_from_json(hosts_file)

    poll_interval_seconds = 1

    while True:
        print(f"--- Polling hosts ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
        for mon in monitors:
            m = mon.get_metrics()
            print(f"Host {mon.label} ({mon.hostname}): {m}")
        time.sleep(poll_interval_seconds)

if __name__ == "__main__": 
    main() 
