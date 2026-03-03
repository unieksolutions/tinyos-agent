"""Hardware detection module — discovers GPU, CPU, RAM, storage."""

import json
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class GPUInfo:
    index: int
    vendor: str
    model: str
    vram_mb: int = 0
    driver: str = ""
    pci_slot: str = ""


@dataclass
class CPUInfo:
    model: str = ""
    cores: int = 0
    threads: int = 0
    freq_mhz: float = 0.0
    architecture: str = ""


@dataclass
class RAMInfo:
    total_mb: int = 0
    available_mb: int = 0


@dataclass
class DiskInfo:
    device: str = ""
    model: str = ""
    size_gb: float = 0.0
    free_gb: float = 0.0
    mount: str = ""


@dataclass
class HardwareReport:
    hostname: str = ""
    gpus: List[GPUInfo] = field(default_factory=list)
    cpu: CPUInfo = field(default_factory=CPUInfo)
    ram: RAMInfo = field(default_factory=RAMInfo)
    disks: List[DiskInfo] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent)

    def summary_lines(self) -> List[str]:
        """Return human-readable summary lines for TUI display."""
        lines = []
        if self.gpus:
            for gpu in self.gpus:
                vram = f" ({gpu.vram_mb} MB)" if gpu.vram_mb else ""
                lines.append(f"  GPU: {gpu.vendor} {gpu.model}{vram}")
        else:
            lines.append("  GPU: None detected")

        lines.append(f"  CPU: {self.cpu.model} ({self.cpu.cores} cores, {self.cpu.threads} threads)")
        lines.append(f"  RAM: {self.ram.total_mb} MB total, {self.ram.available_mb} MB available")

        for disk in self.disks:
            lines.append(f"  Disk: {disk.device} — {disk.size_gb:.1f} GB (free: {disk.free_gb:.1f} GB)")

        return lines


def _run(cmd: List[str], default: str = "") -> str:
    """Run a command and return stdout, or default on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else default
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return default


def detect_gpus() -> List[GPUInfo]:
    """Detect GPUs via sysfs and lspci."""
    gpus = []

    # Try lspci for GPU enumeration
    lspci_out = _run(["lspci", "-nn"])
    if lspci_out:
        gpu_idx = 0
        for line in lspci_out.splitlines():
            # Match VGA and 3D controller lines
            if re.search(r"(VGA|3D|Display)", line, re.IGNORECASE):
                pci_slot = line.split()[0] if line.split() else ""
                # Extract vendor and model from the description
                desc = line.split(": ", 1)[-1] if ": " in line else line
                vendor = "Unknown"
                model = desc

                if "AMD" in desc or "ATI" in desc or "Advanced Micro" in desc:
                    vendor = "AMD"
                elif "NVIDIA" in desc:
                    vendor = "NVIDIA"
                elif "Intel" in desc:
                    vendor = "Intel"
                elif "virtio" in desc.lower() or "Red Hat" in desc:
                    vendor = "virtio"

                # Clean model name
                model = re.sub(r"\[.*?\]", "", desc).strip()

                gpu = GPUInfo(
                    index=gpu_idx,
                    vendor=vendor,
                    model=model,
                    pci_slot=pci_slot,
                )
                gpu_idx += 1

                # Try to get VRAM from sysfs
                vram = _read_gpu_vram(pci_slot)
                if vram:
                    gpu.vram_mb = vram

                # Try to detect driver
                driver = _read_gpu_driver(pci_slot)
                if driver:
                    gpu.driver = driver

                gpus.append(gpu)

    return gpus


def _read_gpu_vram(pci_slot: str) -> int:
    """Read VRAM from sysfs for a PCI device."""
    # AMD: /sys/class/drm/card*/device/mem_info_vram_total
    try:
        for card_dir in sorted(Path("/sys/class/drm").glob("card[0-9]*")):
            device_dir = card_dir / "device"
            vram_file = device_dir / "mem_info_vram_total"
            if vram_file.exists():
                vram_bytes = int(vram_file.read_text().strip())
                return vram_bytes // (1024 * 1024)
    except (OSError, ValueError):
        pass

    # NVIDIA: try nvidia-smi
    smi_out = _run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
    if smi_out:
        try:
            return int(smi_out.splitlines()[0].strip())
        except (ValueError, IndexError):
            pass

    return 0


def _read_gpu_driver(pci_slot: str) -> str:
    """Detect which kernel driver is bound to a GPU."""
    try:
        for card_dir in sorted(Path("/sys/class/drm").glob("card[0-9]*")):
            driver_link = card_dir / "device" / "driver"
            if driver_link.is_symlink():
                return os.path.basename(os.readlink(str(driver_link)))
    except OSError:
        pass
    return ""


def detect_cpu() -> CPUInfo:
    """Detect CPU info from /proc/cpuinfo and lscpu."""
    info = CPUInfo()

    # Try lscpu first (cleaner output)
    lscpu_out = _run(["lscpu"])
    if lscpu_out:
        for line in lscpu_out.splitlines():
            if line.startswith("Model name:"):
                info.model = line.split(":", 1)[1].strip()
            elif line.startswith("CPU(s):"):
                try:
                    info.threads = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Core(s) per socket:"):
                try:
                    cores_per = int(line.split(":", 1)[1].strip())
                    info.cores = cores_per  # Will multiply by sockets below
                except ValueError:
                    pass
            elif line.startswith("Socket(s):"):
                try:
                    sockets = int(line.split(":", 1)[1].strip())
                    info.cores = info.cores * sockets if info.cores else sockets
                except ValueError:
                    pass
            elif line.startswith("CPU max MHz:") or line.startswith("CPU MHz:"):
                try:
                    info.freq_mhz = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Architecture:"):
                info.architecture = line.split(":", 1)[1].strip()

    # Fallback to /proc/cpuinfo
    if not info.model:
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            for line in cpuinfo.splitlines():
                if line.startswith("model name"):
                    info.model = line.split(":", 1)[1].strip()
                    break
            # Count processors
            info.threads = cpuinfo.count("processor\t:")
            if not info.cores:
                info.cores = info.threads
        except OSError:
            pass

    return info


def detect_ram() -> RAMInfo:
    """Detect RAM from /proc/meminfo."""
    info = RAMInfo()
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                info.total_mb = int(line.split()[1]) // 1024
            elif line.startswith("MemAvailable:"):
                info.available_mb = int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return info


def detect_disks() -> List[DiskInfo]:
    """Detect mounted disks from df."""
    disks = []
    df_out = _run(["df", "-BG", "--output=source,size,avail,target"])
    if df_out:
        for line in df_out.splitlines()[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4 and parts[0].startswith("/dev/"):
                try:
                    disk = DiskInfo(
                        device=parts[0],
                        size_gb=float(parts[1].rstrip("G")),
                        free_gb=float(parts[2].rstrip("G")),
                        mount=parts[3],
                    )
                    disks.append(disk)
                except (ValueError, IndexError):
                    pass
    return disks


def detect_hostname() -> str:
    """Get system hostname."""
    try:
        return Path("/etc/hostname").read_text().strip()
    except OSError:
        return _run(["hostname"], "tinyos")


def detect_all() -> HardwareReport:
    """Run full hardware detection and return a complete report."""
    return HardwareReport(
        hostname=detect_hostname(),
        gpus=detect_gpus(),
        cpu=detect_cpu(),
        ram=detect_ram(),
        disks=detect_disks(),
    )


def save_report(report: HardwareReport, path: str = "/opt/tinyos-agent/data/hardware.json"):
    """Save hardware report to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(report.to_json())


if __name__ == "__main__":
    report = detect_all()
    print(report.to_json())
