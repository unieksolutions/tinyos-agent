<!--
ts: 2026-03-04T10:00:00Z | git: a8ee2e2 | path: /opt/projects/tinyos-agent
-->

# TinyOS Agent

**Minimal live-USB operating system with an integrated AI agent, hardware detection, and ShareMesh distributed GPU/VRAM sharing.**

Boot any x86_64 machine from USB → auto-detect hardware (GPU, CPU, RAM) → run AI models locally via llama.cpp with Vulkan → join a mesh network to share compute resources with nearby nodes.

## Vision

**TinyOS Agent** is a bootable Debian-based live USB image that turns any PC into a node in the **ShareMesh** network. ShareMesh enables nearby machines to pool their GPU and VRAM resources so that a better AI model can be loaded and run across the mesh — instead of each node being limited to what it can run alone.

**Key idea:** One node with a powerful GPU (e.g. RTX 4090, 24GB VRAM) can serve model inference for the entire local mesh, while less powerful nodes contribute CPU/RAM or act as clients.

### Core Components
1. **TinyOS** — Minimal Debian bookworm live image, boots from USB on any x86_64 hardware
2. **Agent** — Python curses TUI that greets the user, detects hardware, handles identity
3. **llama.cpp** — Built with Vulkan backend for GPU-accelerated inference (AMD, NVIDIA, Intel)
4. **ShareMesh** (future) — Mesh networking layer to discover and share compute resources

## Current Status

**Version:** 0.2.0 | **Phase:** 2 of 5 complete | See [STATUS.md](STATUS.md)

- ✅ Agent TUI (curses): splash, hardware display, identity/auth, main menu
- ✅ Hardware detection: GPU (lspci/sysfs/nvidia-smi), CPU, RAM, disks
- ✅ User identity: SQLite + bcrypt/sha256 auth
- ✅ Live-build ISO pipeline: Debian bookworm, UEFI, Vulkan packages
- ✅ llama.cpp Vulkan build (chroot hook compiles from source at b8185)
- ✅ Tests: 25 Python tests pass, 76/80 config tests pass
- 🚧 ISO not yet successfully built end-to-end
- ❌ ShareMesh not started (architecture needed)
- ❌ Multi-arch (ARM/RISC-V) not yet implemented

## Project Structure

```
tinyos-agent/
├── agent/                    # Python agent package
│   ├── __init__.py           # Version (0.2.0)
│   ├── __main__.py           # Entry: python3 -m agent
│   ├── main.py               # Curses TUI: splash, greeting, auth, menu
│   ├── hardware.py           # GPU/CPU/RAM/disk detection
│   ├── identity.py           # SQLite user DB, bcrypt/sha256 auth
│   └── tinyos-agent.service  # systemd service (auto-start on tty1)
├── build/                    # Debian live-build tree
│   ├── lb_config             # live-build configuration script
│   └── config/
│       ├── package-lists/    # Packages installed in ISO
│       ├── hooks/chroot/     # Build hooks (locale, GPU modules, user, autologin, llama.cpp)
│       ├── hooks/live/       # Runtime hooks
│       └── includes.chroot/  # Files copied into image
├── scripts/
│   ├── build-llamacpp.sh     # Standalone llama.cpp Vulkan build script
│   ├── sync-agent.sh         # Copy agent code into live-build tree
│   └── test-gpu-detect.sh    # Verify llama.cpp Vulkan GPU detection
├── tests/
│   ├── test_agent.py         # 25 unit tests (hardware + identity)
│   └── test_config.sh        # 82 config validation tests
├── vendor/llama.cpp/
│   └── VERSION               # Pinned version: b8185
└── Makefile                  # Build system: make deps, make base-image, make test-boot
```

## Quick Start (Build Host)

```bash
cd /opt/projects/tinyos-agent
make deps                   # Install live-build, QEMU, OVMF (needs sudo)
./scripts/sync-agent.sh     # Copy agent into build tree
make base-image             # Build ISO (needs sudo, ~20 min)
make test-boot              # Boot ISO in QEMU to verify
```

## Documentation

| File | Purpose |
|------|---------|
| [START.md](START.md) | Bootstrap instructions and file index |
| [STATUS.md](STATUS.md) | Current project status and progress |
| [BACKLOG.md](BACKLOG.md) | Prioritized work items |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design: agent, live-build, ShareMesh |
| [DESIGN.md](DESIGN.md) | UI/UX specifications (TUI, future web) |
| [VERSIONS.md](VERSIONS.md) | Version tracking and dependencies |
| [DEPLOY.md](DEPLOY.md) | Deployment procedures |
| [SECRETS.md](SECRETS.md) | Credential locations |

## Target Hardware

**Goal: any hardware should be able to connect.**

| Architecture | Status | Notes |
|-------------|--------|-------|
| x86_64 | 🟢 Active | Primary target, Debian bookworm live-build |
| ARM64 (RPi, etc.) | 🔴 Planned | Requires cross-build or native ARM live-build |
| RISC-V | 🔴 Future | Experimental |

## GPU Support (via llama.cpp Vulkan)

| Vendor | Driver | Status |
|--------|--------|--------|
| AMD (RDNA/GCN) | radv (Mesa) | 🟢 Supported |
| NVIDIA | nouveau / proprietary | 🟢 Supported |
| Intel (integrated/Arc) | ANV (Mesa) | 🟡 Untested |
| CPU fallback | N/A | 🟢 Automatic |

## Standards

- **Language:** English for code and documentation
- **Source of truth:** `/opt/projects/tinyos-agent`
- **Tickets:** Synced with ticket service at `http://192.168.42.21:5401`

## ⚠️ For MODIFYING existing services - MANDATORY:

### Migration Requirements
⚠️ **BEFORE making any changes:**
- Create backup of current working state
- Test migration path for existing data/users
- Verify backwards compatibility
- Document rollback procedure if changes break functionality

**Rule: If current functionality works, preserve it. Only extend, don't replace.**
