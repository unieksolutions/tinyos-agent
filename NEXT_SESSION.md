<!--
Session continuation prompt for TinyOS Agent
Updated: 2026-03-08T13:00:00Z
-->

# Next Session: TinyOS Agent

## Session Context

You are continuing work on the **TinyOS Agent** project at `/opt/projects/tinyos-agent`.

**This session (2026-03-07 to 2026-03-08) completed Phase 3 + started Phase 4:**

### What was accomplished:
- ✅ **Phase 3 COMPLETE** — ISO boots: GRUB 2.12 → kernel 6.12 → agent TUI on tty1
- ✅ Build #11 successful (11 attempts total, see STATUS.md for full history)
- ✅ Host `/usr/lib/live/build/lb_binary_iso` patched: `grub-mkimage -p /boot/grub` + embedded modules (`normal configfile linux search`)
- ✅ getty@tty1 masked, agent service owns tty1, fallback shell on tty2
- ✅ llama-cli, llama-server, Vulkan 1.4.305 verified on booted ISO
- ✅ SECRETS.md scrubbed from git history (tinyos-agent + 26 other repos)
- ✅ Bootstrap template updated: SECRETS.md in .gitignore
- ✅ **Discovery module** (`agent/discovery.py`) — 6 transport scanners
- ✅ TUI onboarding: "Scan for resources?" + "Share your resources?" questions
- ✅ 42/42 Python tests pass

### Host patches (NOT in git, applied to build host):
The following patches are on the Ubuntu build host and must be reapplied if live-build is reinstalled:
```
/usr/lib/live/build/lb_binary_iso line 172:
  grub-mkimage -p /boot/grub -d ${input_dir} -o ${core_img} -O i386-pc biosdisk iso9660 normal configfile linux search
```

---

## Immediate Next Steps

### 1. MESH-001 — Design ShareMesh architecture
This is the main work for next session. Key decisions:

**Resource advertisement (Q2 from onboarding: "Share your resources?"):**
- Use avahi/mDNS to advertise `_sharemesh._tcp` service
- TXT records: GPU model, VRAM, loaded models, CPU cores, RAM
- Each node publishes what it has and what it can share

**Discovery protocol (Q1 from onboarding: "Scan for resources?"):**
- The discovery module already scans 6 transports (LAN, mDNS, WiFi, BT, USB, Thunderbolt)
- Next: filter scan results for ShareMesh nodes specifically
- Show mesh peers separately from generic devices in TUI

**Resource negotiation:**
- How nodes request GPU time / model inference from peers
- llama-server on GPU node, HTTP API for clients
- VRAM negotiation: who loads which model

### 2. Build new ISO with discovery packages
The package list was updated but no new ISO built yet:
```bash
cd /opt/projects/tinyos-agent && bash scripts/sync-agent.sh && cd build && sudo lb clean --purge && sudo lb build 2>&1 | tee build.log
```
New packages: avahi-utils, iw, bluez, nmap, bolt

### 3. Test discovery on real hardware
Boot ISO on physical machine (not QEMU) to test actual WiFi/BT/LAN scanning.

---

## QEMU Screenshot Method (no VNC client needed)

```python
import socket, time
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/tmp/qemu-monitor.sock')
time.sleep(0.3); sock.recv(4096)
sock.sendall(b'screendump /tmp/qemu-screen.ppm\n')
time.sleep(2); sock.recv(4096)
sock.close()

from PIL import Image
Image.open('/tmp/qemu-screen.ppm').save('/tmp/qemu-screen.png')
```

Keystrokes: `sock.sendall(b'sendkey ret\n')`
Special keys: space='spc', hyphen='minus', slash='slash'

---

## Project Structure

```
/opt/projects/tinyos-agent/
├── agent/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py            # TUI: splash, onboarding, menu, settings
│   ├── hardware.py         # GPU/CPU/RAM/disk detection
│   ├── identity.py         # User auth, SQLite, bcrypt
│   └── discovery.py        # NEW: 6-transport scanner (LAN, mDNS, WiFi, BT, USB, TB)
├── build/                   # Debian live-build tree
│   ├── config/hooks/        # FLAT directory (lb 3.0!)
│   │   ├── 0040-autologin   # Masks getty@tty1, autologin on tty2
│   │   └── ...              # 8 hooks total
│   └── config/package-lists/tinyos.list.chroot  # 93 packages
├── tests/
│   ├── test_hardware.py     # 25 tests
│   └── test_discovery.py    # 17 tests
├── scripts/
└── Makefile
```

---

## Key Technical Details

- **Base OS:** Debian 13 Trixie | **Kernel:** 6.12.63 | **Vulkan:** 1.4.305
- **llama.cpp:** b8185 with GGML_VULKAN=ON
- **live-build:** 3.0~a57-1 (Ubuntu host) — many quirks, see STATUS.md
- **Bootloader:** GRUB 2 (BIOS only, no UEFI yet)
- **Build time:** ~30-40 min | **ISO size:** 615MB
- **KVM:** `sg kvm -c "qemu-system-x86_64 -enable-kvm -m 2G -smp 2 -cdrom build/tinyos-agent.iso -boot d -vnc :1 -monitor unix:/tmp/qemu-monitor.sock,server,nowait"`

## Important Constraints

- **sudo required** for `lb build`
- **Always `--purge`** when config changes
- **No VNC client** — use QEMU monitor screendump
- **Commit AND push** after completing work
- **SECRETS.md is gitignored** — never track credential files
