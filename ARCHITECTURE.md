<!--
ts: 2026-03-04T10:00:00Z | git: a8ee2e2 | path: /opt/projects/tinyos-agent
-->

# ARCHITECTURE

System design and technical decisions for TinyOS Agent.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   TinyOS Agent Node                     │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │  Agent   │  │ llama.cpp│  │     ShareMesh         │  │
│  │  TUI     │  │ (Vulkan) │  │  (future: mesh net)   │  │
│  │  curses  │  │ cli/srv  │  │  discovery + sharing  │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬────────────┘  │
│       │              │                   │               │
│  ┌────┴──────────────┴───────────────────┴────────────┐  │
│  │              Debian bookworm (live USB)             │  │
│  │  systemd · Vulkan · firmware · Python 3 · SQLite   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                         │
│  Hardware: GPU (AMD/NVIDIA/Intel) · CPU · RAM · Disk    │
└─────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. TinyOS — Live USB Image

**Technology:** Debian bookworm, live-build, UEFI boot (grub)

The base operating system is a minimal Debian live image built with `live-build`. It boots from USB, runs entirely in RAM (with optional persistence), and requires no installation.

**Boot flow:**
```
USB boot → GRUB (UEFI) → Linux kernel → systemd
  → auto-login on tty1 (agetty)
  → tinyos-agent.service starts
  → Agent TUI (python3 -m agent.main)
```

**Key design decisions:**
- **Debian bookworm** — stable, broad hardware support, large package ecosystem
- **Non-free firmware** — included for AMD/NVIDIA GPU and WiFi chipsets
- **live-build** — standard Debian tool for building live ISOs
- **amd64 only** (for now) — ARM64 planned as separate build target
- **No installer** — boots live, no disk modification required

### 2. Agent — Python Curses TUI

**Technology:** Python 3, curses, SQLite, systemd

The agent is the user-facing application. It launches automatically on tty1 at boot.

**Module structure:**
```
agent/
├── __init__.py       # Version constant
├── __main__.py       # Entry point: python3 -m agent
├── main.py           # AgentTUI class (curses UI, menu, flow control)
├── hardware.py       # HardwareReport: GPU, CPU, RAM, disk detection
└── identity.py       # User DB: SQLite, bcrypt/sha256 passwords
```

**TUI flow:**
```
Splash (ASCII art) → Hardware detection → Greeting
  → Name prompt → Identity check:
    → New user: optional password → create in SQLite
    → Known user with password: authenticate
    → Known user without password: welcome back
  → Main menu:
    [1] Hardware Info
    [2] Network Scan (placeholder)
    [3] Mesh Status (placeholder)
    [4] Settings (password change)
    [q] Quit
```

**Data storage:**
- SQLite DB at `/opt/tinyos-agent/data/users.db`
- Hardware report JSON at `/opt/tinyos-agent/data/hardware.json`
- All data in `/opt/tinyos-agent/data/` — survives session if persistence enabled

### 3. llama.cpp — Local AI Inference

**Technology:** llama.cpp (b8185), Vulkan backend, GGUF model format

Built from source during ISO creation (chroot hook) with Vulkan GPU acceleration.

**Installed binaries:**
- `/usr/local/bin/llama-cli` — CLI inference (single prompts, batch)
- `/usr/local/bin/llama-server` — HTTP API server (OpenAI-compatible)

**GPU detection (automatic at runtime):**
```
Vulkan ICD loaded → enumerate GPU devices
  → AMD: radv (Mesa) driver
  → NVIDIA: nouveau or proprietary
  → Intel: ANV (Mesa)
  → No GPU: CPU fallback (automatic, --gpu-layers 0)
```

**Key design decisions:**
- **Vulkan** (not CUDA) — works on AMD, NVIDIA, and Intel GPUs
- **Built from source** — pinned version, optimized for target hardware
- **GGUF models** — efficient quantized format, fits various VRAM sizes
- **Server mode** — enables remote inference (critical for ShareMesh)

### 4. ShareMesh — Distributed GPU Sharing (FUTURE)

**Status:** Architecture phase — not yet implemented.

**Core idea:** Pool GPU/VRAM resources across local network nodes so that a better AI model can run on the combined mesh than any single node could handle alone.

#### Planned Architecture

```
Node A (RTX 4090, 24GB VRAM)          Node B (no GPU, 32GB RAM)
┌─────────────────────────┐            ┌──────────────────────┐
│ llama-server             │ ◄──HTTP──► │ Agent TUI (client)   │
│ Model: llama3-70b-Q4    │            │ Routes to Node A     │
│ GPU layers: 40/40       │            │                      │
│ Advertises: _sharemesh   │            │ Discovers via mDNS   │
└─────────────────────────┘            └──────────────────────┘

Node C (RX 7600, 8GB VRAM)
┌──────────────────────────┐
│ llama-server              │
│ Model: llama3-8b-Q8      │
│ GPU layers: 33/33         │
│ Advertises: _sharemesh    │
└──────────────────────────┘
```

#### Discovery Protocol (planned)
- **mDNS/Avahi** (already in package list) for zero-config LAN discovery
- Service type: `_sharemesh._tcp`
- TXT records: GPU model, VRAM total/free, loaded model(s), inference endpoint

#### Resource Negotiation (planned)
- Nodes advertise their hardware capabilities
- Client nodes pick the best available server for their request
- Priority: most VRAM free → fastest GPU → lowest latency
- Model loading: if no node has the requested model loaded, pick the node with most free VRAM and load it

#### Proof of Concept Scope
1. Two nodes on same LAN
2. Node A: has GPU → runs `llama-server` with a small model
3. Node B: no GPU → discovers Node A via mDNS → sends inference requests via HTTP
4. Agent TUI "Chat" menu routes to best available node

## Build System

### live-build Pipeline

```
make deps          → apt install live-build, QEMU, OVMF
sync-agent.sh      → copy agent/ into build/config/includes.chroot/
make base-image    → lb config + lb build → ISO
make test-boot     → QEMU boot verification
```

### Chroot Hook Execution Order

```
0010-locale.hook.chroot         — locale, keyboard, timezone
0020-kernel-modules.hook.chroot — GPU/DRM module loading
0030-agent-user.hook.chroot     — agent user, groups, dirs
0040-autologin.hook.chroot      — agetty autologin on tty1
0050-cleanup.hook.chroot        — apt clean, temp removal
0060-install-agent.hook.chroot  — install agent, enable systemd service
10-llamacpp.hook.chroot         — compile llama.cpp from source (in hooks/ not hooks/chroot/)
```

**Known issue:** Hook ordering needs fix — cleanup (0050) runs before agent install (0060) and llama build. See BACKLOG ISO-001.

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Base OS | Debian bookworm | Stable, broad hardware, large packages |
| Boot method | Live USB (live-build) | No installation needed, instant setup |
| Firmware | Non-free included | Required for AMD/NVIDIA GPU + WiFi |
| GPU backend | Vulkan (not CUDA) | Cross-vendor: AMD + NVIDIA + Intel |
| AI runtime | llama.cpp | Fast, C++, Vulkan support, GGUF models |
| Agent UI | Python curses | Zero dependencies, works on any terminal |
| User DB | SQLite | Zero config, file-based, embedded |
| Auth | bcrypt (fallback: sha256) | bcrypt preferred, sha256 for minimal installs |
| Mesh discovery | mDNS/Avahi (planned) | Zero-config LAN, no central server |
| Model format | GGUF | Efficient, quantized, variable sizes |

## Security Considerations

- Agent runs as unprivileged `agent` user (not root)
- GPU access via `video` and `render` groups
- Passwords hashed with bcrypt (or sha256 fallback)
- No remote access by default (SSH server installed but not exposed)
- ShareMesh: encryption and auth TBD (see BACKLOG MESH-005)
