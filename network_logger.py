#!/usr/bin/env python3
"""
Network Connection Logger
Runs in background and logs all network connections to a CSV file.
"""

import psutil
import socket
import csv
import signal
import sys
import os
import threading
import time
from datetime import datetime
from pathlib import Path


class NetworkLogger:
    LOG_FIELDS = [
        "timestamp",
        "protocol",
        "local_address",
        "local_port",
        "remote_address",
        "remote_port",
        "domain",
        "status",
        "process_name",
        "process_pid",
    ]

    def __init__(self, output_file="network_connections.csv", interval=2):
        self.output_file = Path(output_file)
        self.interval = interval
        self.running = False
        self.seen_connections = set()
        self.lock = threading.Lock()
        self.csv_file = None
        self.csv_writer = None
        self.domain_resolver = DomainResolver()
        self._pid_names = {}

    def _init_csv(self):
        file_exists = self.output_file.exists()
        self.csv_file = open(self.output_file, "a", newline="")
        self.csv_writer = csv.DictWriter(
            self.csv_file,
            fieldnames=self.LOG_FIELDS,
            extrasaction="ignore",
        )
        if not file_exists:
            self.csv_writer.writeheader()
            self.csv_file.flush()

    def _close_csv(self):
        if self.csv_file:
            self.csv_file.flush()
            self.csv_file.close()

    def _get_connections(self):
        connections = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status:
                    laddr = conn.laddr
                    raddr = conn.raddr
                    
                    laddr_ip = laddr.ip if laddr else ""
                    lport = laddr.port if laddr else ""
                    raddr_ip = raddr.ip if raddr else ""
                    rport = raddr.port if raddr else ""

                    conn_key = (
                        conn.family,
                        conn.type,
                        laddr_ip,
                        lport,
                        raddr_ip,
                        rport,
                        conn.pid,
                    )

                    pid = conn.pid
                    proc_name = ""
                    if pid:
                        if pid in self._pid_names:
                            proc_name = self._pid_names[pid]
                        else:
                            try:
                                proc_name = psutil.Process(pid).name()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                proc_name = ""
                            self._pid_names[pid] = proc_name

                    if raddr_ip:
                        self.domain_resolver.resolve(raddr_ip)

                    connections.append({
                        "proto": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                        "laddr": laddr_ip,
                        "lport": lport,
                        "raddr": raddr_ip,
                        "rport": rport,
                        "status": conn.status,
                        "pid": pid,
                        "proc": proc_name,
                        "conn_key": conn_key,
                        "laddr_str": f"{laddr_ip}:{laddr}" if laddr_ip else "",
                        "raddr_str": f"{raddr_ip}:{rport}" if raddr_ip else "",
                    })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return connections

    def _log_connections(self, connections):
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            new_conns = []
            for conn in connections:
                conn_key = conn["conn_key"]
                if conn_key not in self.seen_connections:
                    self.seen_connections.add(conn_key)
                    new_conns.append(conn)
            
            if len(self.seen_connections) > 10000:
                self.seen_connections.clear()

        domain_cache = self.domain_resolver.cache

        for conn in new_conns:
            raddr = conn.get("raddr", "")
            domain = domain_cache.get(raddr, "") if raddr else ""
            
            row = {
                "timestamp": timestamp,
                "protocol": conn.get("proto", ""),
                "local_address": conn.get("laddr", ""),
                "local_port": conn.get("lport", ""),
                "remote_address": raddr,
                "remote_port": conn.get("rport", ""),
                "domain": domain,
                "status": conn.get("status", ""),
                "process_name": conn.get("proc", ""),
                "process_pid": conn.get("pid", ""),
            }
            self.csv_writer.writerow(row)

        self.csv_file.flush()

    def run(self):
        self._init_csv()
        self.running = True
        
        print(f"Network Logger started. Logging to: {self.output_file}")
        print("Press Ctrl+C to stop.")
        
        try:
            while self.running:
                connections = self._get_connections()
                self._log_connections(connections)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self._close_csv()
            print("\nNetwork Logger stopped.")


class DomainResolver:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
        self._resolve_threads = {}

    def resolve(self, ip):
        if not ip or ip in ("0.0.0.0", "::", "*", ""):
            return

        with self.lock:
            if ip in self.cache:
                return

        with self.lock:
            if ip in self._resolve_threads:
                return
            self._resolve_threads[ip] = True

        t = threading.Thread(target=self._resolve_ip, args=(ip,), daemon=True)
        t.start()

    def _resolve_ip(self, ip):
        domain = ""
        try:
            result = socket.gethostbyaddr(ip)
            if result and result[0]:
                domain = result[0].strip(".")
                if "." in domain:
                    domain = domain.split(".")[0] + "." + ".".join(domain.split(".")[1:])
        except Exception:
            pass

        with self.lock:
            self.cache[ip] = domain
            if ip in self._resolve_threads:
                del self._resolve_threads[ip]


def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork failed: {e}\n")
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Network Connection Logger")
    parser.add_argument(
        "-o", "--output", default="network_connections.csv", help="Output CSV file"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=2, help="Scan interval in seconds"
    )
    parser.add_argument(
        "-d", "--daemon", action="store_true", help="Run as daemon"
    )
    parser.add_argument(
        "-p", "--pidfile", help="PID file path (for daemon mode)"
    )

    args = parser.parse_args()

    output_path = Path(args.output)
    if output_path.exists() and output_path.stat().st_size > 0:
        response = input(f"Append to existing {args.output}? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    if args.daemon:
        daemonize()
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    if args.pidfile:
        with open(args.pidfile, "w") as f:
            f.write(str(os.getpid()))

    logger = NetworkLogger(args.output, args.interval)
    
    def signal_handler(sig, frame):
        logger.running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.run()


if __name__ == "__main__":
    main()