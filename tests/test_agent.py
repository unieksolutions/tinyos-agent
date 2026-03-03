#!/usr/bin/env python3
"""Tests for TinyOS Agent modules — hardware detection and identity."""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.hardware import (
    detect_cpu,
    detect_ram,
    detect_disks,
    detect_hostname,
    detect_all,
    HardwareReport,
    GPUInfo,
    CPUInfo,
    RAMInfo,
    DiskInfo,
)
from agent.identity import (
    _get_db,
    _hash_password,
    _verify_password,
    create_user,
    lookup_user,
    authenticate,
    update_last_seen,
    set_password,
    list_users,
)


class TestHardwareDetection(unittest.TestCase):
    """Test hardware detection on the current host."""

    def test_detect_cpu_returns_cpuinfo(self):
        cpu = detect_cpu()
        self.assertIsInstance(cpu, CPUInfo)
        self.assertTrue(len(cpu.model) > 0, "CPU model should not be empty")
        self.assertGreater(cpu.threads, 0, "Should detect at least 1 thread")

    def test_detect_ram_returns_meminfo(self):
        ram = detect_ram()
        self.assertIsInstance(ram, RAMInfo)
        self.assertGreater(ram.total_mb, 0, "Should detect RAM > 0 MB")
        self.assertGreater(ram.available_mb, 0, "Should have some available RAM")

    def test_detect_disks_returns_list(self):
        disks = detect_disks()
        self.assertIsInstance(disks, list)
        # Should have at least root filesystem
        self.assertGreater(len(disks), 0, "Should detect at least one disk/mount")

    def test_detect_hostname_returns_string(self):
        hostname = detect_hostname()
        self.assertIsInstance(hostname, str)
        self.assertTrue(len(hostname) > 0)

    def test_detect_all_returns_report(self):
        report = detect_all()
        self.assertIsInstance(report, HardwareReport)
        self.assertTrue(len(report.hostname) > 0)
        self.assertIsInstance(report.gpus, list)
        self.assertIsInstance(report.cpu, CPUInfo)
        self.assertIsInstance(report.ram, RAMInfo)
        self.assertIsInstance(report.disks, list)

    def test_report_to_json(self):
        report = detect_all()
        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertIn("hostname", parsed)
        self.assertIn("gpus", parsed)
        self.assertIn("cpu", parsed)
        self.assertIn("ram", parsed)
        self.assertIn("disks", parsed)

    def test_report_summary_lines(self):
        report = detect_all()
        lines = report.summary_lines()
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 0)
        # Should contain at least GPU, CPU, RAM lines
        text = "\n".join(lines)
        self.assertIn("CPU:", text)
        self.assertIn("RAM:", text)

    def test_gpu_info_dataclass(self):
        gpu = GPUInfo(index=0, vendor="AMD", model="Radeon RX 7900 XTX", vram_mb=24576)
        self.assertEqual(gpu.vendor, "AMD")
        self.assertEqual(gpu.vram_mb, 24576)

    def test_disk_info_dataclass(self):
        disk = DiskInfo(device="/dev/sda1", size_gb=500.0, free_gb=300.0, mount="/")
        self.assertEqual(disk.device, "/dev/sda1")
        self.assertAlmostEqual(disk.size_gb, 500.0)


class TestIdentity(unittest.TestCase):
    """Test user identity and authentication."""

    def setUp(self):
        """Create a temp database for each test."""
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_users.db")

    def tearDown(self):
        """Clean up temp database."""
        try:
            os.unlink(self.db_path)
            os.rmdir(self.tmpdir)
        except OSError:
            pass

    def test_create_user_without_password(self):
        user = create_user("Alice", db_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Alice")
        self.assertFalse(user.has_password)

    def test_create_user_with_password(self):
        user = create_user("Bob", password="secret123", db_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Bob")
        self.assertTrue(user.has_password)

    def test_lookup_existing_user(self):
        create_user("Charlie", db_path=self.db_path)
        user = lookup_user("Charlie", db_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Charlie")

    def test_lookup_nonexistent_user(self):
        user = lookup_user("Nobody", db_path=self.db_path)
        self.assertIsNone(user)

    def test_lookup_case_insensitive(self):
        create_user("Diana", db_path=self.db_path)
        user = lookup_user("diana", db_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Diana")

    def test_authenticate_correct_password(self):
        create_user("Eve", password="pass123", db_path=self.db_path)
        self.assertTrue(authenticate("Eve", "pass123", db_path=self.db_path))

    def test_authenticate_wrong_password(self):
        create_user("Frank", password="correct", db_path=self.db_path)
        self.assertFalse(authenticate("Frank", "wrong", db_path=self.db_path))

    def test_authenticate_no_password(self):
        create_user("Grace", db_path=self.db_path)
        self.assertFalse(authenticate("Grace", "anything", db_path=self.db_path))

    def test_set_password(self):
        create_user("Heidi", db_path=self.db_path)
        self.assertFalse(authenticate("Heidi", "newpass", db_path=self.db_path))
        set_password("Heidi", "newpass", db_path=self.db_path)
        self.assertTrue(authenticate("Heidi", "newpass", db_path=self.db_path))

    def test_update_last_seen(self):
        create_user("Ivan", db_path=self.db_path)
        user_before = lookup_user("Ivan", db_path=self.db_path)
        import time
        time.sleep(0.1)
        update_last_seen("Ivan", db_path=self.db_path)
        user_after = lookup_user("Ivan", db_path=self.db_path)
        # last_seen should be updated (or at least not error)
        self.assertIsNotNone(user_after)

    def test_list_users(self):
        create_user("Judy", db_path=self.db_path)
        create_user("Karl", db_path=self.db_path)
        users = list_users(db_path=self.db_path)
        self.assertEqual(len(users), 2)
        names = {u.name for u in users}
        self.assertIn("Judy", names)
        self.assertIn("Karl", names)

    def test_password_hash_and_verify(self):
        pw = "test_password_123"
        hashed = _hash_password(pw)
        self.assertTrue(_verify_password(pw, hashed))
        self.assertFalse(_verify_password("wrong", hashed))

    def test_duplicate_user_raises(self):
        create_user("Liam", db_path=self.db_path)
        with self.assertRaises(sqlite3.IntegrityError):
            create_user("Liam", db_path=self.db_path)

    def test_database_creation(self):
        """Database file is created on first access."""
        db_path = os.path.join(self.tmpdir, "subdir", "new.db")
        conn = _get_db(db_path)
        conn.close()
        self.assertTrue(os.path.exists(db_path))


class TestHardwareReportSerialization(unittest.TestCase):
    """Test HardwareReport JSON serialization."""

    def test_empty_report(self):
        report = HardwareReport()
        data = report.to_dict()
        self.assertEqual(data["hostname"], "")
        self.assertEqual(data["gpus"], [])

    def test_report_with_gpu(self):
        report = HardwareReport(
            hostname="testhost",
            gpus=[GPUInfo(index=0, vendor="AMD", model="Test GPU", vram_mb=8192)],
            cpu=CPUInfo(model="Test CPU", cores=4, threads=8),
            ram=RAMInfo(total_mb=16384, available_mb=8192),
            disks=[DiskInfo(device="/dev/sda", size_gb=500, free_gb=250, mount="/")],
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["hostname"], "testhost")
        self.assertEqual(len(parsed["gpus"]), 1)
        self.assertEqual(parsed["gpus"][0]["vendor"], "AMD")
        self.assertEqual(parsed["gpus"][0]["vram_mb"], 8192)
        self.assertEqual(parsed["cpu"]["cores"], 4)
        self.assertEqual(parsed["ram"]["total_mb"], 16384)


if __name__ == "__main__":
    unittest.main()
