#!/usr/bin/env python3
"""TinyOS Agent — Resource discovery across all transports.

Scans LAN, WiFi, Bluetooth, USB, and Thunderbolt for nearby devices
and resources. Designed to run scans in parallel where safe, sequential
where radio contention exists.

Usage:
    from agent.discovery import scan_all, ScanResult
    results = scan_all()  # Returns list of ScanResult
"""

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional


class Transport(str, Enum):
    LAN = "lan"
    MDNS = "mdns"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    USB = "usb"
    THUNDERBOLT = "thunderbolt"


@dataclass
class ScanResult:
    """A discovered device or resource."""
    transport: str          # Transport enum value
    name: str               # Device/service name
    address: str            # IP, MAC, bus ID, etc.
    kind: str               # "host", "service", "gpu", "storage", "radio", etc.
    details: dict = field(default_factory=dict)

    def summary_line(self, width: int = 70) -> str:
        """Single-line summary for TUI display."""
        tag = self.transport.upper()[:4].ljust(4)
        kind_tag = self.kind[:6].ljust(6)
        name_part = self.name[:28].ljust(28)
        addr_part = self.address[:22]
        return f" {tag}  {kind_tag}  {name_part}  {addr_part}"


def _run(cmd: list, timeout: int = 15) -> str:
    """Run command, return stdout or empty string on failure."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


# ── LAN scan (ARP) ──────────────────────────────────────────────────────────

def scan_lan() -> List[ScanResult]:
    """ARP scan for hosts on all local subnets."""
    results = []

    # Get local interfaces and subnets
    out = _run(["ip", "-4", "-o", "addr", "show"])
    subnets = []
    for line in out.splitlines():
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
        if m and not line.strip().startswith("1:"):  # Skip loopback
            subnets.append(m.group(1))

    # Try nmap ping scan (fast, no root needed for -sn)
    for subnet in subnets:
        out = _run(["nmap", "-sn", "-n", subnet], timeout=30)
        for block in out.split("Nmap scan report for "):
            block = block.strip()
            if not block:
                continue
            ip_match = re.match(r"(\d+\.\d+\.\d+\.\d+)", block)
            if ip_match:
                ip = ip_match.group(1)
                mac_match = re.search(r"MAC Address: ([\w:]+)\s*\(?(.*?)\)?$", block, re.M)
                mac = mac_match.group(1) if mac_match else ""
                vendor = mac_match.group(2).strip("()") if mac_match else ""
                results.append(ScanResult(
                    transport=Transport.LAN,
                    name=vendor or ip,
                    address=ip,
                    kind="host",
                    details={"mac": mac, "vendor": vendor},
                ))

    return results


# ── mDNS/Avahi scan ─────────────────────────────────────────────────────────

def scan_mdns() -> List[ScanResult]:
    """Browse mDNS services via avahi-browse."""
    results = []
    out = _run(["avahi-browse", "-a", "-t", "-r", "-p"], timeout=10)

    for line in out.splitlines():
        if not line.startswith("="):
            continue
        parts = line.split(";")
        if len(parts) < 10:
            continue
        # =;interface;protocol;name;type;domain;hostname;address;port;txt
        name = parts[3]
        stype = parts[4]
        hostname = parts[6]
        address = parts[7]
        port = parts[8]
        results.append(ScanResult(
            transport=Transport.MDNS,
            name=f"{name} ({stype})",
            address=f"{address}:{port}",
            kind="service",
            details={"hostname": hostname, "type": stype},
        ))

    return results


# ── WiFi scan ────────────────────────────────────────────────────────────────

def scan_wifi() -> List[ScanResult]:
    """Scan for WiFi networks via iw."""
    results = []

    # Find wireless interfaces
    out = _run(["iw", "dev"])
    interfaces = []
    for line in out.splitlines():
        m = re.match(r"\s+Interface\s+(\S+)", line)
        if m:
            interfaces.append(m.group(1))

    for iface in interfaces:
        out = _run(["iw", iface, "scan"], timeout=20)
        current = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("BSS "):
                if current.get("bssid"):
                    results.append(_wifi_result(current))
                bssid = re.match(r"BSS ([\w:]+)", line)
                current = {"bssid": bssid.group(1) if bssid else "", "ssid": "", "signal": "", "freq": ""}
            elif line.startswith("SSID:"):
                current["ssid"] = line.split(":", 1)[1].strip()
            elif line.startswith("signal:"):
                current["signal"] = line.split(":", 1)[1].strip()
            elif line.startswith("freq:"):
                current["freq"] = line.split(":", 1)[1].strip()
        if current.get("bssid"):
            results.append(_wifi_result(current))

    return results


def _wifi_result(info: dict) -> ScanResult:
    ssid = info.get("ssid", "Hidden")
    return ScanResult(
        transport=Transport.WIFI,
        name=ssid or "Hidden Network",
        address=info.get("bssid", ""),
        kind="radio",
        details={k: v for k, v in info.items() if v},
    )


# ── Bluetooth scan ───────────────────────────────────────────────────────────

def scan_bluetooth() -> List[ScanResult]:
    """Scan for Bluetooth devices via bluetoothctl."""
    results = []

    # Start scan for a few seconds, then read devices
    _run(["bluetoothctl", "power", "on"], timeout=5)
    # Use timeout-based discovery
    proc = subprocess.Popen(
        ["bluetoothctl", "scan", "on"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    time.sleep(8)  # Discover for 8 seconds
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    # List discovered devices
    out = _run(["bluetoothctl", "devices"], timeout=5)
    for line in out.splitlines():
        m = re.match(r"Device\s+([\w:]+)\s+(.*)", line)
        if m:
            mac = m.group(1)
            name = m.group(2).strip()
            results.append(ScanResult(
                transport=Transport.BLUETOOTH,
                name=name or mac,
                address=mac,
                kind="radio",
                details={"mac": mac},
            ))

    return results


# ── USB scan ─────────────────────────────────────────────────────────────────

def scan_usb() -> List[ScanResult]:
    """List USB devices, flag GPUs and interesting peripherals."""
    results = []
    out = _run(["lsusb"])

    for line in out.splitlines():
        m = re.match(r"Bus (\d+) Device (\d+): ID ([\w:]+)\s*(.*)", line)
        if not m:
            continue
        bus, dev, usb_id, desc = m.groups()
        desc = desc.strip()

        # Classify
        kind = "device"
        desc_lower = desc.lower()
        if any(w in desc_lower for w in ("gpu", "vga", "display", "graphics", "geforce", "radeon")):
            kind = "gpu"
        elif any(w in desc_lower for w in ("storage", "mass storage", "disk")):
            kind = "storage"
        elif any(w in desc_lower for w in ("bluetooth",)):
            kind = "radio"
        elif any(w in desc_lower for w in ("network", "ethernet", "wifi", "wireless")):
            kind = "radio"
        elif any(w in desc_lower for w in ("hub",)):
            continue  # Skip hubs, not interesting

        results.append(ScanResult(
            transport=Transport.USB,
            name=desc or usb_id,
            address=f"bus{bus}:dev{dev}",
            kind=kind,
            details={"usb_id": usb_id},
        ))

    return results


# ── Thunderbolt / eGPU scan ──────────────────────────────────────────────────

def scan_thunderbolt() -> List[ScanResult]:
    """List Thunderbolt devices via boltctl."""
    results = []
    out = _run(["boltctl", "list"])

    if not out.strip():
        return results

    current = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            if current.get("name"):
                results.append(ScanResult(
                    transport=Transport.THUNDERBOLT,
                    name=current.get("name", "Unknown"),
                    address=current.get("uuid", ""),
                    kind="gpu" if "gpu" in current.get("name", "").lower() else "device",
                    details=current,
                ))
            current = {}
        elif ":" in line:
            key, _, val = line.partition(":")
            current[key.strip().lower()] = val.strip()

    if current.get("name"):
        results.append(ScanResult(
            transport=Transport.THUNDERBOLT,
            name=current.get("name", "Unknown"),
            address=current.get("uuid", ""),
            kind="gpu" if "gpu" in current.get("name", "").lower() else "device",
            details=current,
        ))

    return results


# ── PCI eGPU hotplug detection ───────────────────────────────────────────────

def scan_pci_gpus() -> List[ScanResult]:
    """Detect GPUs on PCI bus (includes eGPUs connected via Thunderbolt)."""
    results = []
    out = _run(["lspci", "-nn"])

    for line in out.splitlines():
        if any(cls in line for cls in ["VGA compatible", "3D controller", "Display controller"]):
            m = re.match(r"(\S+)\s+(.*)", line)
            if m:
                pci_id = m.group(1)
                desc = m.group(2)
                results.append(ScanResult(
                    transport=Transport.USB,  # PCI, but grouped with hardware
                    name=desc,
                    address=f"pci:{pci_id}",
                    kind="gpu",
                    details={"pci_slot": pci_id},
                ))

    return results


# ── Orchestrator ─────────────────────────────────────────────────────────────

def scan_all(
    enable_lan: bool = True,
    enable_mdns: bool = True,
    enable_wifi: bool = True,
    enable_bluetooth: bool = True,
    enable_usb: bool = True,
    enable_thunderbolt: bool = True,
    progress_callback=None,
) -> List[ScanResult]:
    """Run all discovery scans. Network in parallel, radio sequential.

    Args:
        progress_callback: Optional callable(transport_name, status) for TUI updates.

    Returns:
        Combined list of ScanResult from all transports.
    """
    all_results: List[ScanResult] = []

    def _notify(transport: str, status: str):
        if progress_callback:
            progress_callback(transport, status)

    # Phase 1: Instant scans (USB, PCI, Thunderbolt) — no contention
    instant_scanners = []
    if enable_usb:
        instant_scanners.append(("USB", scan_usb))
        instant_scanners.append(("PCI GPUs", scan_pci_gpus))
    if enable_thunderbolt:
        instant_scanners.append(("Thunderbolt", scan_thunderbolt))

    for name, scanner in instant_scanners:
        _notify(name, "scanning")
        try:
            all_results.extend(scanner())
        except Exception:
            pass
        _notify(name, "done")

    # Phase 2: Network scans in parallel (LAN + mDNS) — no radio contention
    network_scanners = []
    if enable_lan:
        network_scanners.append(("LAN", scan_lan))
    if enable_mdns:
        network_scanners.append(("mDNS", scan_mdns))

    if network_scanners:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {}
            for name, scanner in network_scanners:
                _notify(name, "scanning")
                futures[pool.submit(scanner)] = name

            for future in as_completed(futures):
                name = futures[future]
                try:
                    all_results.extend(future.result())
                except Exception:
                    pass
                _notify(name, "done")

    # Phase 3: Radio scans SEQUENTIAL (WiFi then Bluetooth — shared radio)
    if enable_wifi:
        _notify("WiFi", "scanning")
        try:
            all_results.extend(scan_wifi())
        except Exception:
            pass
        _notify("WiFi", "done")

    if enable_bluetooth:
        _notify("Bluetooth", "scanning")
        try:
            all_results.extend(scan_bluetooth())
        except Exception:
            pass
        _notify("Bluetooth", "done")

    return all_results


def save_scan(results: List[ScanResult], path: str):
    """Save scan results to JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)


def format_table(results: List[ScanResult], width: int = 70) -> List[str]:
    """Format scan results as ASCII table lines for TUI display."""
    if not results:
        return ["  No devices found."]

    lines = []
    header = " TYPE  KIND    NAME                          ADDRESS"
    sep = " " + "─" * (min(width, 68) - 2)
    lines.append(header)
    lines.append(sep)

    # Group by transport
    by_transport = {}
    for r in results:
        by_transport.setdefault(r.transport, []).append(r)

    for transport in Transport:
        items = by_transport.get(transport.value, [])
        if not items:
            continue
        for r in items:
            lines.append(r.summary_line(width))

    lines.append(sep)
    lines.append(f" Total: {len(results)} devices/services found")
    return lines
