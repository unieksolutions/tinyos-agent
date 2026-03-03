# TinyOS Agent

A bootable USB live image (Debian bookworm) that turns any x86_64 machine into a mesh-connected AI compute node.

**Domain:** [sharemesh.org](https://sharemesh.org)
**Vision:** Share idle GPU/CPU resources across an ad-hoc mesh network.

## Documentation

- [START.md](START.md) — Bootstrap instructions and file index
- [STATUS.md](STATUS.md) — Current project status and progress
- [BACKLOG.md](BACKLOG.md) — Prioritized work items
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and technical decisions
- [VERSIONS.md](VERSIONS.md) — Version history and deployments

## Quick Start

```bash
# 1. Install build prerequisites (requires sudo)
make deps

# 2. Build the ISO
make base-image

# 3. Verify it boots to a shell
make test-boot
```

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Base Image | Debian live-build, GPU drivers, hardware support | Done (v0.1.0) |
| 2. Agent TUI | Interactive agent: greeting, identity, auth | In Progress |
| 3. Network Discovery | WiFi, Bluetooth, mDNS device scanning | Planned |
| 4. ShareMesh | P2P resource sharing (sharemesh.org) | Planned |

## Directory Structure

```
tinyos-agent/
├── Makefile                          # Build targets
├── agent/                            # Python agent application
│   ├── __init__.py
│   ├── main.py                       # TUI entry point
│   ├── hardware.py                   # Hardware detection
│   └── identity.py                   # User identity & auth
├── build/
│   ├── lb_config                     # lb config initialisation
│   └── config/
│       ├── package-lists/
│       │   └── tinyos.list.chroot    # Packages in the live image
│       └── hooks/
│           ├── chroot/               # Build-time hooks
│           └── live/                 # Boot-time hooks
├── scripts/
│   ├── build-llamacpp.sh             # llama.cpp Vulkan build
│   └── test-gpu-detect.sh            # GPU detection test
├── tests/
│   └── test_config.sh                # 78-test static analysis
└── vendor/
    └── llama.cpp/VERSION             # Pinned release tag
```

## Image Specification

| Property | Value |
|----------|-------|
| Base | Debian bookworm (stable) |
| Architecture | x86_64 (amd64) |
| Desktop | None (headless) |
| Kernel | linux-image-amd64 |
| Boot | UEFI (GRUB2) + BIOS fallback |
| Auto-login | `agent` user on tty1 |
| GPU | AMD (amdgpu), NVIDIA (nouveau), Intel (i915), virtio |

## Make Targets

| Target | Description |
|--------|-------------|
| `make deps` | Install live-build, QEMU, OVMF |
| `make base-image` | Build the Debian live ISO |
| `make test-boot` | Boot ISO in QEMU interactively |
| `make test-boot-headless` | CI boot test (exits 0 when shell appears) |
| `make rebuild` | clean + base-image |
| `make clean` | Remove build artefacts, keep config |

## Migration Requirements

**BEFORE making any changes:**
- Create backup of current working state
- Test migration path for existing data/users
- Verify backwards compatibility
- Document rollback procedure if changes break functionality

**Rule: If current functionality works, preserve it. Only extend, don't replace.**

## Standards

- **Language:** English for code and docs
- **Source of truth:** `/opt/projects/tinyos-agent/`
- **Tickets:** Synced with ticket service (BACKLOG.md)
