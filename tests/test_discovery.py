"""Tests for agent.discovery module."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from agent.discovery import (
    Transport,
    ScanResult,
    scan_usb,
    scan_pci_gpus,
    scan_lan,
    scan_mdns,
    scan_wifi,
    scan_bluetooth,
    scan_thunderbolt,
    scan_all,
    save_scan,
    format_table,
)


# ── ScanResult tests ────────────────────────────────────────────────────────

def test_scan_result_summary_line():
    r = ScanResult(
        transport=Transport.LAN,
        name="My Router",
        address="192.168.1.1",
        kind="host",
    )
    line = r.summary_line()
    assert "LAN" in line
    assert "My Router" in line
    assert "192.168.1.1" in line


def test_scan_result_summary_line_truncates():
    r = ScanResult(
        transport=Transport.WIFI,
        name="A" * 50,
        address="aa:bb:cc:dd:ee:ff",
        kind="radio",
    )
    line = r.summary_line(width=70)
    assert len(r.name[:28]) <= 28


# ── USB scan tests ───────────────────────────────────────────────────────────

MOCK_LSUSB = """Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 002: ID 0bda:8153 Realtek Semiconductor Corp. RTL8153 Gigabit Ethernet Adapter
Bus 002 Device 003: ID 10de:1234 NVIDIA Corp. GeForce GTX eGPU
Bus 002 Device 004: ID 0951:1666 Kingston Technology DataTraveler mass storage
"""


@patch("agent.discovery._run")
def test_scan_usb_parses_devices(mock_run):
    mock_run.return_value = MOCK_LSUSB
    results = scan_usb()
    # Hub is skipped, so 3 devices
    assert len(results) == 3
    names = [r.name for r in results]
    assert any("Realtek" in n for n in names)
    assert any("NVIDIA" in n or "GeForce" in n for n in names)


@patch("agent.discovery._run")
def test_scan_usb_classifies_gpu(mock_run):
    mock_run.return_value = MOCK_LSUSB
    results = scan_usb()
    gpus = [r for r in results if r.kind == "gpu"]
    assert len(gpus) == 1
    assert "GeForce" in gpus[0].name


@patch("agent.discovery._run")
def test_scan_usb_empty(mock_run):
    mock_run.return_value = ""
    results = scan_usb()
    assert results == []


# ── PCI GPU scan tests ───────────────────────────────────────────────────────

MOCK_LSPCI = """00:02.0 VGA compatible controller: Intel Corporation HD Graphics 630
01:00.0 3D controller: NVIDIA Corporation GP107 [GeForce GTX 1050] (rev a1)
02:00.0 Network controller: Intel Corporation Wireless 8265
"""


@patch("agent.discovery._run")
def test_scan_pci_gpus(mock_run):
    mock_run.return_value = MOCK_LSPCI
    results = scan_pci_gpus()
    assert len(results) == 2
    assert all(r.kind == "gpu" for r in results)


# ── LAN scan tests ───────────────────────────────────────────────────────────

MOCK_IP_ADDR = """2: eth0    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
"""

MOCK_NMAP = """Starting Nmap 7.94
Nmap scan report for 192.168.1.1
Host is up (0.0010s latency).
MAC Address: AA:BB:CC:DD:EE:FF (TP-Link)

Nmap scan report for 192.168.1.50
Host is up (0.0020s latency).
MAC Address: 11:22:33:44:55:66 (Raspberry Pi)

Nmap done: 256 IP addresses (2 hosts up)
"""


@patch("agent.discovery._run")
def test_scan_lan(mock_run):
    def side_effect(cmd, **kwargs):
        if cmd[0] == "ip":
            return MOCK_IP_ADDR
        elif cmd[0] == "nmap":
            return MOCK_NMAP
        return ""
    mock_run.side_effect = side_effect
    results = scan_lan()
    assert len(results) == 2
    assert any("192.168.1.1" in r.address for r in results)


# ── mDNS scan tests ──────────────────────────────────────────────────────────

MOCK_AVAHI = """=;eth0;IPv4;My Printer;_ipp._tcp;local;printer.local;192.168.1.50;631;""
=;eth0;IPv4;TinyOS Node;_sharemesh._tcp;local;node1.local;192.168.1.60;8080;"gpu=rtx3080"
"""


@patch("agent.discovery._run")
def test_scan_mdns(mock_run):
    mock_run.return_value = MOCK_AVAHI
    results = scan_mdns()
    assert len(results) == 2
    assert all(r.transport == Transport.MDNS for r in results)
    assert any("sharemesh" in r.name for r in results)


# ── WiFi scan tests ──────────────────────────────────────────────────────────

MOCK_IW_DEV = """phy#0
	Interface wlan0
		type managed
"""

MOCK_IW_SCAN = """BSS aa:bb:cc:dd:ee:01
	freq: 2412
	signal: -45.00 dBm
	SSID: HomeNetwork
BSS aa:bb:cc:dd:ee:02
	freq: 5180
	signal: -62.00 dBm
	SSID: OfficeWiFi
"""


@patch("agent.discovery._run")
def test_scan_wifi(mock_run):
    def side_effect(cmd, **kwargs):
        if "dev" in cmd:
            return MOCK_IW_DEV
        elif "scan" in cmd:
            return MOCK_IW_SCAN
        return ""
    mock_run.side_effect = side_effect
    results = scan_wifi()
    assert len(results) == 2
    assert any("HomeNetwork" in r.name for r in results)
    assert any("OfficeWiFi" in r.name for r in results)


# ── Bluetooth scan tests ────────────────────────────────────────────────────

MOCK_BT_DEVICES = """Device AA:BB:CC:DD:EE:01 JBL Speaker
Device AA:BB:CC:DD:EE:02 Galaxy Buds
"""


@patch("agent.discovery.subprocess")
@patch("agent.discovery._run")
def test_scan_bluetooth(mock_run, mock_subprocess):
    # Mock the Popen for scan
    mock_proc = mock_subprocess.Popen.return_value
    mock_proc.terminate.return_value = None
    mock_proc.wait.return_value = 0
    mock_proc.kill.return_value = None

    def side_effect(cmd, **kwargs):
        if "devices" in cmd:
            return MOCK_BT_DEVICES
        return ""
    mock_run.side_effect = side_effect

    # Patch time.sleep to speed up
    with patch("agent.discovery.time.sleep"):
        results = scan_bluetooth()

    assert len(results) == 2
    assert any("JBL" in r.name for r in results)


# ── Thunderbolt scan tests ──────────────────────────────────────────────────

MOCK_BOLTCTL = """name: Razer Core X eGPU
uuid: abc-123-def
status: authorized

name: CalDigit TS3 Plus
uuid: xyz-456-ghi
status: authorized
"""


@patch("agent.discovery._run")
def test_scan_thunderbolt(mock_run):
    mock_run.return_value = MOCK_BOLTCTL
    results = scan_thunderbolt()
    assert len(results) == 2
    gpus = [r for r in results if r.kind == "gpu"]
    assert len(gpus) == 1
    assert "Razer" in gpus[0].name


@patch("agent.discovery._run")
def test_scan_thunderbolt_empty(mock_run):
    mock_run.return_value = ""
    results = scan_thunderbolt()
    assert results == []


# ── Orchestrator tests ───────────────────────────────────────────────────────

@patch("agent.discovery.scan_bluetooth", return_value=[])
@patch("agent.discovery.scan_wifi", return_value=[])
@patch("agent.discovery.scan_mdns", return_value=[])
@patch("agent.discovery.scan_lan", return_value=[])
@patch("agent.discovery.scan_thunderbolt", return_value=[])
@patch("agent.discovery.scan_pci_gpus", return_value=[])
@patch("agent.discovery.scan_usb", return_value=[
    ScanResult(Transport.USB, "Keyboard", "bus1:dev2", "device"),
])
def test_scan_all_combines_results(*mocks):
    results = scan_all()
    assert len(results) == 1
    assert results[0].name == "Keyboard"


@patch("agent.discovery.scan_bluetooth", return_value=[])
@patch("agent.discovery.scan_wifi", return_value=[])
@patch("agent.discovery.scan_mdns", return_value=[])
@patch("agent.discovery.scan_lan", return_value=[])
@patch("agent.discovery.scan_thunderbolt", return_value=[])
@patch("agent.discovery.scan_pci_gpus", return_value=[])
@patch("agent.discovery.scan_usb", return_value=[])
def test_scan_all_progress_callback(*mocks):
    events = []
    def on_progress(transport, status):
        events.append((transport, status))
    scan_all(progress_callback=on_progress)
    assert len(events) > 0
    assert any(s == "done" for _, s in events)


# ── save / format tests ─────────────────────────────────────────────────────

def test_save_scan():
    results = [
        ScanResult(Transport.LAN, "Router", "192.168.1.1", "host"),
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_scan(results, path)
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["name"] == "Router"
    finally:
        os.unlink(path)


def test_format_table_empty():
    lines = format_table([])
    assert any("No devices" in l for l in lines)


def test_format_table_with_results():
    results = [
        ScanResult(Transport.LAN, "Router", "192.168.1.1", "host"),
        ScanResult(Transport.USB, "Keyboard", "bus1:dev2", "device"),
    ]
    lines = format_table(results)
    assert any("Router" in l for l in lines)
    assert any("Keyboard" in l for l in lines)
    assert any("Total: 2" in l for l in lines)
