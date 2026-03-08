#!/usr/bin/env python3
"""TinyOS Agent — Main TUI entry point.

Runs on boot (via systemd service), greets the user, detects hardware,
handles identity/auth, and presents the main menu.

Usage:
    python3 -m agent.main          # Normal TUI mode
    python3 -m agent.main --test   # Non-interactive test mode
"""

import curses
import getpass
import os
import signal
import sys
import time
from typing import Optional

from agent import __version__
from agent.hardware import detect_all, save_report, HardwareReport
from agent.identity import (
    lookup_user,
    create_user,
    authenticate,
    update_last_seen,
    set_password,
)
from agent.discovery import scan_all, format_table, save_scan, ScanResult


# ── Constants ────────────────────────────────────────────────────────────────

AGENT_NAME = "TinyOS Agent"
DATA_DIR = os.environ.get("TINYOS_DATA_DIR", "/opt/tinyos-agent/data")
DB_PATH = os.path.join(DATA_DIR, "users.db")


# ── Curses TUI ───────────────────────────────────────────────────────────────

class AgentTUI:
    """Terminal UI for the TinyOS Agent boot experience."""

    def __init__(self, stdscr, test_mode: bool = False):
        self.stdscr = stdscr
        self.test_mode = test_mode
        self.hw_report: Optional[HardwareReport] = None
        self.scan_results: list = []
        self.current_user: Optional[str] = None
        self.running = True

        # Curses setup
        curses.curs_set(1)  # Show cursor
        curses.use_default_colors()
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, -1)      # Title
            curses.init_pair(2, curses.COLOR_GREEN, -1)      # Success
            curses.init_pair(3, curses.COLOR_YELLOW, -1)     # Warning
            curses.init_pair(4, curses.COLOR_WHITE, -1)      # Normal
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)    # Accent

        self.stdscr.timeout(-1)  # Blocking input

    def color(self, pair_num: int):
        """Get color pair attribute, or 0 if no colors."""
        if curses.has_colors():
            return curses.color_pair(pair_num)
        return 0

    def clear_and_border(self):
        """Clear screen and draw border."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        if height >= 3 and width >= 3:
            try:
                self.stdscr.border()
            except curses.error:
                pass

    def print_at(self, y: int, x: int, text: str, attr=0):
        """Safely print text at position."""
        height, width = self.stdscr.getmaxyx()
        if y < height and x < width:
            try:
                self.stdscr.addnstr(y, x, text, width - x - 1, attr)
            except curses.error:
                pass

    def print_centered(self, y: int, text: str, attr=0):
        """Print text centered on row y."""
        _, width = self.stdscr.getmaxyx()
        x = max(1, (width - len(text)) // 2)
        self.print_at(y, x, text, attr)

    def get_input(self, y: int, x: int, prompt: str, hidden: bool = False) -> str:
        """Get user input at position. Returns empty string on Ctrl-C."""
        self.print_at(y, x, prompt, self.color(4))
        self.stdscr.refresh()

        input_x = x + len(prompt)
        curses.echo()
        if hidden:
            curses.noecho()

        buf = []
        while True:
            try:
                ch = self.stdscr.getch()
                if ch in (curses.KEY_ENTER, 10, 13):
                    break
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    if buf:
                        buf.pop()
                        self.print_at(y, input_x, " " * (len(buf) + 1))
                        if not hidden:
                            self.print_at(y, input_x, "".join(buf))
                        else:
                            self.print_at(y, input_x, "*" * len(buf))
                        self.stdscr.move(y, input_x + len(buf))
                elif ch == 3:  # Ctrl-C
                    return ""
                elif 32 <= ch < 127:
                    buf.append(chr(ch))
                    if not hidden:
                        self.print_at(y, input_x, "".join(buf))
                    else:
                        self.print_at(y, input_x, "*" * len(buf))
                    self.stdscr.move(y, input_x + len(buf))
            except curses.error:
                break

        curses.noecho()
        return "".join(buf).strip()

    def show_splash(self):
        """Show the boot splash with ASCII art."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        art = [
            r"  _____  _               ___  ____  ",
            r" |_   _|(_) _ __   _   _ / _ \/ ___| ",
            r"   | |  | || '_ \ | | | | | | \___ \ ",
            r"   | |  | || | | || |_| | |_| |___) |",
            r"   |_|  |_||_| |_| \__, |\___/|____/ ",
            r"                    |___/             ",
        ]

        start_y = max(1, (height - len(art) - 6) // 2)
        for i, line in enumerate(art):
            self.print_centered(start_y + i, line, self.color(1) | curses.A_BOLD)

        self.print_centered(start_y + len(art) + 1,
                            f"Agent v{__version__}", self.color(5))
        self.print_centered(start_y + len(art) + 2,
                            "sharemesh.org", self.color(3))
        self.print_centered(start_y + len(art) + 4,
                            "Detecting hardware...", self.color(4))
        self.stdscr.refresh()

    def show_hardware(self, start_y: int) -> int:
        """Display hardware summary. Returns next available row."""
        if not self.hw_report:
            return start_y

        self.print_at(start_y, 3, "I detected:", self.color(4))
        lines = self.hw_report.summary_lines()
        for i, line in enumerate(lines):
            attr = self.color(2) if "GPU" in line and "None" not in line else self.color(4)
            self.print_at(start_y + 1 + i, 3, line, attr)

        return start_y + 1 + len(lines) + 1

    def greeting_screen(self):
        """Main greeting: show hardware, ask name, handle auth."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        # Title bar
        title = f" {AGENT_NAME} v{__version__} "
        self.print_centered(1, title, self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        # Greeting
        self.print_at(4, 3, f"Hi! I'm your {AGENT_NAME}.", self.color(1) | curses.A_BOLD)
        self.print_at(5, 3, "", self.color(4))

        # Hardware summary
        next_y = self.show_hardware(7)

        # Ask name
        name = self.get_input(next_y + 1, 3, "What's your name? ")
        if not name:
            return

        # Identity flow
        self.handle_identity(name, next_y + 3)

    def handle_identity(self, name: str, start_y: int):
        """Handle user identity: new user or returning user with auth."""
        user = lookup_user(name, DB_PATH)

        if user is None:
            # New user
            self.print_at(start_y, 3,
                          f"Nice to meet you, {name}!", self.color(2) | curses.A_BOLD)
            self.print_at(start_y + 1, 3,
                          "I'll remember you for next time.", self.color(4))

            # Ask if they want a password
            self.print_at(start_y + 3, 3,
                          "Would you like to set a password? (y/n) ", self.color(3))
            self.stdscr.refresh()

            ch = self.stdscr.getch()
            if ch in (ord("y"), ord("Y")):
                pw = self.get_input(start_y + 4, 3, "Choose a password: ", hidden=True)
                if pw:
                    pw2 = self.get_input(start_y + 5, 3, "Confirm password:  ", hidden=True)
                    if pw == pw2:
                        create_user(name, pw, DB_PATH)
                        self.print_at(start_y + 7, 3,
                                      "Account created with password!", self.color(2))
                    else:
                        create_user(name, None, DB_PATH)
                        self.print_at(start_y + 7, 3,
                                      "Passwords didn't match. Account created without password.",
                                      self.color(3))
                else:
                    create_user(name, None, DB_PATH)
            else:
                create_user(name, None, DB_PATH)
                self.print_at(start_y + 4, 3,
                              "Account created without password.", self.color(4))

            self.current_user = name

        elif user.has_password:
            # Known user with password
            self.print_at(start_y, 3,
                          f"Welcome back, {user.name}!", self.color(2) | curses.A_BOLD)
            pw = self.get_input(start_y + 1, 3, "Password: ", hidden=True)

            if pw and authenticate(user.name, pw, DB_PATH):
                update_last_seen(user.name, DB_PATH)
                self.print_at(start_y + 3, 3,
                              "Authenticated successfully!", self.color(2))
                self.current_user = user.name
            else:
                self.print_at(start_y + 3, 3,
                              "Incorrect password.", self.color(3))
                self.stdscr.refresh()
                time.sleep(2)
                return  # Back to greeting

        else:
            # Known user without password
            self.print_at(start_y, 3,
                          f"Welcome back, {user.name}!", self.color(2) | curses.A_BOLD)
            update_last_seen(user.name, DB_PATH)
            self.current_user = user.name

        self.stdscr.refresh()
        time.sleep(1)

        if self.current_user:
            self.onboarding_discovery()
            self.main_menu()

    def onboarding_discovery(self):
        """Post-auth: ask user about scanning and sharing resources."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        self.print_centered(1, f" {AGENT_NAME} v{__version__} ",
                            self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        self.print_at(4, 3, f"Welcome, {self.current_user}!", self.color(2) | curses.A_BOLD)

        # Q1: Scan for resources?
        self.print_at(6, 3, "Should I scan for nearby resources?", self.color(4))
        self.print_at(7, 3, "(LAN, WiFi, Bluetooth, USB, eGPU)", self.color(3))
        self.print_at(9, 3, "[y] Yes, scan now   [n] Not now", self.color(5))
        self.stdscr.refresh()

        do_scan = False
        while True:
            ch = self.stdscr.getch()
            if ch in (ord("y"), ord("Y")):
                do_scan = True
                break
            elif ch in (ord("n"), ord("N")):
                break

        if do_scan:
            self.run_discovery_scan()

        # Q2: Offer resources?
        self.clear_and_border()
        self.print_centered(1, f" {AGENT_NAME} v{__version__} ",
                            self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        self.print_at(4, 3, "Should I offer my resources to the mesh?", self.color(4))
        self.print_at(5, 3, "(Other devices can discover and use this node)", self.color(3))
        self.print_at(7, 3, "[y] Yes, share   [n] Not now", self.color(5))
        self.stdscr.refresh()

        while True:
            ch = self.stdscr.getch()
            if ch in (ord("y"), ord("Y")):
                # TODO: Start mDNS advertisement (Phase 4: MESH-002)
                self.print_at(9, 3, "Resource sharing enabled. (mDNS advertisement coming soon)",
                              self.color(2))
                self.stdscr.refresh()
                time.sleep(1.5)
                break
            elif ch in (ord("n"), ord("N")):
                self.print_at(9, 3, "Resource sharing disabled for now.",
                              self.color(4))
                self.stdscr.refresh()
                time.sleep(1)
                break

    def run_discovery_scan(self):
        """Run all discovery scans with live progress on screen."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        self.print_centered(1, " Scanning ", self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        status_y = 4
        statuses = {}

        def progress(transport: str, status: str):
            statuses[transport] = status
            y = status_y
            for i, (t, s) in enumerate(statuses.items()):
                icon = "..." if s == "scanning" else " ok"
                attr = self.color(3) if s == "scanning" else self.color(2)
                self.print_at(y + i, 3, f"  [{icon}] {t}", attr)
            try:
                self.stdscr.refresh()
            except curses.error:
                pass

        self.print_at(status_y - 1, 3, "Scanning all transports...", self.color(4))
        self.stdscr.refresh()

        self.scan_results = scan_all(progress_callback=progress)

        # Save results
        try:
            save_scan(self.scan_results, os.path.join(DATA_DIR, "scan.json"))
        except OSError:
            pass

        # Show summary
        result_y = status_y + len(statuses) + 1
        self.print_at(result_y, 3,
                      f"Found {len(self.scan_results)} devices/services.",
                      self.color(2) | curses.A_BOLD)
        self.print_at(result_y + 2, 3, "Press any key to continue...", self.color(4))
        self.stdscr.refresh()
        self.stdscr.getch()

    def show_scan_results(self):
        """Display scan results as ASCII table."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        self.print_centered(1, " Network Scan Results ", self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        lines = format_table(self.scan_results, width - 4)
        for i, line in enumerate(lines):
            if i + 4 >= height - 2:
                self.print_at(height - 3, 3, f"  ... and {len(lines) - i} more (scroll coming soon)",
                              self.color(3))
                break
            self.print_at(4 + i, 2, line, self.color(4))

        self.print_at(height - 2, 3, "[r] Rescan  [any] Back", self.color(5))
        self.stdscr.refresh()

        ch = self.stdscr.getch()
        if ch in (ord("r"), ord("R")):
            self.run_discovery_scan()
            self.show_scan_results()

    def main_menu(self):
        """Post-auth main menu."""
        while self.running:
            self.clear_and_border()
            height, width = self.stdscr.getmaxyx()

            title = f" {AGENT_NAME} — {self.current_user} "
            self.print_centered(1, title, self.color(1) | curses.A_BOLD)
            self.print_at(2, 1, "─" * (width - 2), self.color(5))

            menu_items = [
                ("1", "Hardware Info", "View detected hardware"),
                ("2", "Network Scan", f"Scan for nearby devices ({len(self.scan_results)} found)"),
                ("3", "Mesh Status", "ShareMesh network status (coming soon)"),
                ("4", "Settings", "Agent settings"),
                ("q", "Quit", "Shutdown agent"),
            ]

            for i, (key, label, desc) in enumerate(menu_items):
                y = 4 + i * 2
                self.print_at(y, 4, f"[{key}]", self.color(5) | curses.A_BOLD)
                self.print_at(y, 9, label, self.color(4) | curses.A_BOLD)
                self.print_at(y, 9 + len(label) + 2, f"— {desc}", self.color(4))

            # Status bar
            self.print_at(height - 2, 3, f"sharemesh.org | {self.hw_report.hostname if self.hw_report else 'tinyos'}",
                          self.color(3))

            self.stdscr.refresh()

            ch = self.stdscr.getch()
            if ch == ord("1"):
                self.show_hardware_detail()
            elif ch == ord("2"):
                self.show_scan_results()
            elif ch == ord("3"):
                self.show_coming_soon("Mesh Status")
            elif ch == ord("4"):
                self.show_settings()
            elif ch in (ord("q"), ord("Q")):
                self.running = False

    def show_hardware_detail(self):
        """Full hardware detail screen."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        self.print_centered(1, " Hardware Report ", self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        if self.hw_report:
            lines = self.hw_report.summary_lines()
            for i, line in enumerate(lines):
                self.print_at(4 + i, 3, line, self.color(4))

            # Show JSON path if saved
            json_path = os.path.join(DATA_DIR, "hardware.json")
            if os.path.exists(json_path):
                self.print_at(4 + len(lines) + 1, 3, f"Report saved: {json_path}", self.color(3))

        self.print_at(height - 2, 3, "Press any key to return...", self.color(4))
        self.stdscr.refresh()
        self.stdscr.getch()

    def show_coming_soon(self, feature: str):
        """Placeholder for features not yet implemented."""
        self.clear_and_border()
        height, _ = self.stdscr.getmaxyx()

        self.print_centered(height // 2 - 1, f"{feature}", self.color(1) | curses.A_BOLD)
        self.print_centered(height // 2 + 1, "Coming in a future release!", self.color(3))
        self.print_centered(height // 2 + 3, "Press any key to return...", self.color(4))
        self.stdscr.refresh()
        self.stdscr.getch()

    def show_settings(self):
        """Settings screen."""
        self.clear_and_border()
        height, width = self.stdscr.getmaxyx()

        self.print_centered(1, " Settings ", self.color(1) | curses.A_BOLD)
        self.print_at(2, 1, "─" * (width - 2), self.color(5))

        self.print_at(4, 4, "[1] Change/Set password", self.color(4))
        self.print_at(6, 4, "[b] Back", self.color(4))

        self.stdscr.refresh()
        ch = self.stdscr.getch()

        if ch == ord("1") and self.current_user:
            pw = self.get_input(8, 4, "New password: ", hidden=True)
            if pw:
                pw2 = self.get_input(9, 4, "Confirm:      ", hidden=True)
                if pw == pw2:
                    set_password(self.current_user, pw, DB_PATH)
                    self.print_at(11, 4, "Password updated!", self.color(2))
                else:
                    self.print_at(11, 4, "Passwords don't match.", self.color(3))
                self.stdscr.refresh()
                time.sleep(1.5)

    def run(self):
        """Main run loop."""
        # Show splash
        self.show_splash()

        # Detect hardware
        self.hw_report = detect_all()
        try:
            save_report(self.hw_report, os.path.join(DATA_DIR, "hardware.json"))
        except OSError:
            pass  # May fail on read-only FS without overlay

        # In test mode, just report and exit
        if self.test_mode:
            self.clear_and_border()
            self.print_at(2, 3, "TEST MODE — Hardware detected:", self.color(3))
            lines = self.hw_report.summary_lines()
            for i, line in enumerate(lines):
                self.print_at(4 + i, 3, line, self.color(4))
            self.print_at(4 + len(lines) + 1, 3, "Test passed. Exiting.", self.color(2))
            self.stdscr.refresh()
            time.sleep(1)
            return

        # Normal interactive flow
        while self.running:
            self.greeting_screen()
            if not self.running:
                break
            if not self.current_user:
                continue  # Re-show greeting on auth failure


def main(stdscr, test_mode: bool = False):
    """Curses wrapper entry point."""
    tui = AgentTUI(stdscr, test_mode=test_mode)
    tui.run()


def run():
    """Module entry point — called from __main__.py or systemd."""
    test_mode = "--test" in sys.argv

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Handle SIGTERM gracefully (systemd stop)
    def handle_sigterm(sig, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        curses.wrapper(lambda stdscr: main(stdscr, test_mode))
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
    finally:
        print(f"\n{AGENT_NAME} v{__version__} — Goodbye!")


if __name__ == "__main__":
    run()
