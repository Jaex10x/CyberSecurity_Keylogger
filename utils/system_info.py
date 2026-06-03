"""
CyberSentinel - System Information Profiler
=============================================
Collects comprehensive system information for
security audit reports and environment profiling.

Features:
    - OS and hardware profiling
    - Network interface enumeration
    - Running process listing
    - User session information
"""

import os
import socket
import platform
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemProfiler:
    """
    Collects and organizes system information for
    cybersecurity audit documentation.
    """

    def __init__(self):
        self.profile_time = datetime.now()
        self._profile = None

    def collect_all(self) -> dict:
        """Collect all available system information."""
        self._profile = {
            "profile_timestamp": self.profile_time.isoformat(),
            "os_info": self._get_os_info(),
            "hardware": self._get_hardware_info(),
            "network": self._get_network_info(),
            "user_info": self._get_user_info(),
            "processes": self._get_top_processes(),
        }
        return self._profile

    def _get_os_info(self) -> dict:
        """Collect operating system information."""
        return {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0],
        }

    def _get_hardware_info(self) -> dict:
        """Collect hardware specifications."""
        info = {
            "cpu_count_logical": os.cpu_count(),
        }

        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            info.update({
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "cpu_freq_mhz": (
                    round(psutil.cpu_freq().current, 2)
                    if psutil.cpu_freq() else "N/A"
                ),
                "cpu_usage_percent": psutil.cpu_percent(interval=0.5),
                "ram_total_gb": round(mem.total / (1024 ** 3), 2),
                "ram_available_gb": round(mem.available / (1024 ** 3), 2),
                "ram_usage_percent": mem.percent,
                "disk_total_gb": round(disk.total / (1024 ** 3), 2),
                "disk_free_gb": round(disk.free / (1024 ** 3), 2),
                "disk_usage_percent": disk.percent,
            })

        return info

    def _get_network_info(self) -> dict:
        """Collect network interface information."""
        info = {
            "hostname": socket.gethostname(),
        }

        try:
            info["local_ip"] = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            info["local_ip"] = "Unable to resolve"

        if PSUTIL_AVAILABLE:
            interfaces = {}
            addrs = psutil.net_if_addrs()
            for iface_name, iface_addrs in addrs.items():
                iface_info = []
                for addr in iface_addrs:
                    iface_info.append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                    })
                interfaces[iface_name] = iface_info
            info["interfaces"] = interfaces

            # Network I/O stats
            net_io = psutil.net_io_counters()
            info["bytes_sent_mb"] = round(net_io.bytes_sent / (1024 ** 2), 2)
            info["bytes_recv_mb"] = round(net_io.bytes_recv / (1024 ** 2), 2)

        return info

    def _get_user_info(self) -> dict:
        """Collect current user information."""
        info = {
            "username": os.getlogin() if hasattr(os, "login") else os.environ.get("USERNAME", os.environ.get("USER", "Unknown")),
            "home_directory": str(os.path.expanduser("~")),
        }

        if PSUTIL_AVAILABLE:
            users = psutil.users()
            info["active_sessions"] = [
                {
                    "name": u.name,
                    "terminal": u.terminal or "N/A",
                    "host": u.host or "local",
                    "started": datetime.fromtimestamp(u.started).isoformat(),
                }
                for u in users
            ]

        return info

    def _get_top_processes(self, limit: int = 15) -> list:
        """Get top running processes by memory usage."""
        if not PSUTIL_AVAILABLE:
            return [{"error": "psutil not available"}]

        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                pinfo = proc.info
                processes.append({
                    "pid": pinfo["pid"],
                    "name": pinfo["name"],
                    "cpu_percent": round(pinfo["cpu_percent"] or 0, 1),
                    "memory_percent": round(pinfo["memory_percent"] or 0, 1),
                    "status": pinfo["status"],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage, return top N
        processes.sort(key=lambda p: p["memory_percent"], reverse=True)
        return processes[:limit]

    def get_summary(self) -> str:
        """Get a human-readable summary of the system profile."""
        if not self._profile:
            self.collect_all()

        os_info = self._profile["os_info"]
        hw = self._profile["hardware"]

        lines = [
            f"🖥️  System: {os_info['system']} {os_info['release']}",
            f"🏗️  Architecture: {os_info['architecture']} ({os_info['machine']})",
            f"⚙️  Processor: {os_info['processor']}",
            f"🧠  CPU Cores: {hw.get('cpu_count_physical', 'N/A')} physical / {hw['cpu_count_logical']} logical",
            f"💾  RAM: {hw.get('ram_available_gb', 'N/A')} GB free / {hw.get('ram_total_gb', 'N/A')} GB total ({hw.get('ram_usage_percent', 'N/A')}% used)",
            f"💿  Disk: {hw.get('disk_free_gb', 'N/A')} GB free / {hw.get('disk_total_gb', 'N/A')} GB total ({hw.get('disk_usage_percent', 'N/A')}% used)",
            f"🌐  Hostname: {self._profile['network']['hostname']}",
            f"📍  Local IP: {self._profile['network'].get('local_ip', 'N/A')}",
            f"🐍  Python: {os_info['python_version']}",
        ]
        return "\n".join(lines)
