# TinyOS Agent — ARCHITECTURE

## System Overview

TinyOS Agent is a bootable USB live system that turns any x86_64 machine into a mesh-connected compute node. The system is built in 4 phases:

```
┌─────────────────────────────────────────────────────────┐
│  USB Boot (Debian bookworm live)                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Phase 1: Hardware Detection                       │ │
│  │  GPU • CPU • RAM • Storage • Network adapters      │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         ▼                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Phase 2: Agent TUI                                │ │
│  │  Greeting • User identity • Auth • Local config    │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         ▼                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Phase 3: Network Discovery                        │ │
│  │  WiFi • Bluetooth • mDNS • Peer detection          │ │
│  └──────────────────────┬─────────────────────────────┘ │
│                         ▼                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Phase 4: ShareMesh (sharemesh.org)                │ │
│  │  Resource ads • Job routing • P2P mesh network     │ │
│  │  "I have 2 GPUs idle, who needs compute?"          │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Boot Sequence

```
BIOS/UEFI → GRUB2 → Linux kernel → live-boot overlay
  → systemd → agetty autologin (agent@tty1)
    → tinyos-agent.service → agent TUI
      → hardware detect → network scan → mesh join
```

## Directory Layout (on live image)

```
/opt/tinyos-agent/
├── agent/                  # Python agent application
│   ├── __init__.py
│   ├── main.py             # Entry point (TUI)
│   ├── hardware.py         # Hardware detection
│   ├── identity.py         # User identity & auth
│   ├── network.py          # Network scanning
│   └── mesh.py             # ShareMesh protocol
├── data/                   # Runtime data (overlay, ephemeral)
│   ├── users.db            # SQLite user database
│   └── hardware.json       # Detected hardware report
├── models/                 # GGUF models for local LLM
├── logs/                   # Agent logs
└── tmp/                    # Scratch space (1777)
```

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Base OS | Debian bookworm (live) | Stable, broad hardware support |
| Boot | UEFI + BIOS fallback | Maximum hardware compatibility |
| GPU | Vulkan (mesa) | Cross-vendor GPU compute |
| LLM | llama.cpp (Vulkan) | Local inference, no cloud dependency |
| Agent | Python 3.11 | Available in bookworm, rich ecosystem |
| TUI | curses / rich | Terminal UI, no X11 needed |
| Auth | SQLite + bcrypt | Simple, zero-config, secure |
| Network | avahi (mDNS) + nftables | Zero-conf discovery + firewall |
| Mesh | Custom P2P (future) | sharemesh.org protocol |

## Agent TUI Design (Phase 2)

```
┌─────────────────────────────────────────┐
│          TinyOS Agent v0.2.0            │
│─────────────────────────────────────────│
│                                         │
│  Hi! I'm your TinyOS Agent.            │
│                                         │
│  I detected:                            │
│    GPU: AMD Radeon RX 7900 XTX (24GB)  │
│    CPU: AMD Ryzen 9 7950X (16 cores)   │
│    RAM: 64 GB                           │
│    Disk: 1 TB NVMe (free: 800 GB)      │
│                                         │
│  What's your name? _                    │
│                                         │
│─────────────────────────────────────────│
│  [Tab] Menu  [Ctrl-C] Shutdown         │
└─────────────────────────────────────────┘
```

### Identity Flow

1. Agent boots → hardware detection → display summary
2. "What's your name?" → user types name
3. **New user:** Welcome message, optional password setup
4. **Known user:** "Welcome back, {name}! Password?" → bcrypt verify
5. After auth → main menu (hardware info, network scan, mesh status)

## Network Architecture (Phase 3-4)

```
  Node A (2x GPU)          Node B (CPU-only)         Node C (1x GPU)
  ┌──────────────┐         ┌──────────────┐          ┌──────────────┐
  │ TinyOS Agent │◄──mDNS──►│ TinyOS Agent │◄──mDNS──►│ TinyOS Agent │
  │              │         │              │          │              │
  │ Advertise:   │         │ Advertise:   │          │ Advertise:   │
  │  2x GPU 16GB │         │  32-core CPU │          │  1x GPU 8GB  │
  │  Idle        │         │  Idle        │          │  Busy (70%)  │
  └──────┬───────┘         └──────┬───────┘          └──────┬───────┘
         │                        │                         │
         └────────────┬───────────┘─────────────────────────┘
                      │
              ShareMesh Protocol
              (sharemesh.org)
```

### Resource Sharing Model

- **Advertisement:** Each node broadcasts capabilities (GPU count, VRAM, CPU cores, RAM)
- **Request:** "I need 16GB VRAM for 2 hours" → mesh routes to available node
- **Execution:** Job runs on target node, results returned
- **Trust:** Node identity via public key, reputation scoring

## Security Considerations

- Live image is read-only (squashfs) — tamper-resistant
- Overlay filesystem for runtime writes (ephemeral)
- Scoped sudoers (only specific commands)
- nftables firewall for mesh traffic
- bcrypt password hashing for user auth
- Future: TLS for mesh communication, node identity certificates
