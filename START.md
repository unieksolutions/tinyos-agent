# TinyOS Agent — START

Single entrypoint for this project. Read this first.

## Project Summary

**TinyOS Agent** is a bootable USB live image (Debian bookworm) that runs a lightweight AI agent capable of:
1. Booting and detecting available hardware (GPU, CPU, RAM, storage)
2. Running an interactive agent that greets users and manages identity
3. Scanning network/WiFi/Bluetooth for connectable devices
4. Sharing compute resources across an ad-hoc mesh network (sharemesh.org)

**Domain:** sharemesh.org
**Vision:** "I have 2 GPUs with 16GB VRAM not doing anything, anyone that has a job for me?"

## File Index

### Core Documentation
- **[README.md](README.md)** — Project overview, build instructions, directory structure
- **[START.md](START.md)** — This file, bootstrap entrypoint
- **[STATUS.md](STATUS.md)** — Current project status and progress
- **[BACKLOG.md](BACKLOG.md)** — Prioritized work items (synced with ticket service)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — System design and technical decisions
- **[VERSIONS.md](VERSIONS.md)** — Version history and deployment tracking

### Build System
- **[Makefile](Makefile)** — Build targets (make base-image, test-boot, clean)
- **[build/lb_config](build/lb_config)** — live-build configuration script
- **[build/config/](build/config/)** — Package lists, chroot hooks, live hooks

### Scripts
- **[scripts/build-llamacpp.sh](scripts/build-llamacpp.sh)** — Build llama.cpp with Vulkan backend
- **[scripts/test-gpu-detect.sh](scripts/test-gpu-detect.sh)** — Verify GPU auto-detection

### Tests
- **[tests/test_config.sh](tests/test_config.sh)** — 78-test static analysis suite

### Vendor
- **[vendor/llama.cpp/VERSION](vendor/llama.cpp/VERSION)** — Pinned llama.cpp release tag (b8185)

## Quick Start

```bash
# On a host with sudo access:
sudo apt-get install -y live-build debootstrap qemu-system-x86 ovmf
cd /opt/projects/tinyos-agent
make base-image      # Build the Debian live ISO
make test-boot       # Boot in QEMU to verify
```

## Working Rules

- Source of truth: `/opt/projects/tinyos-agent/`
- Commit AND push after every change
- Update STATUS.md after completing work
- Sync BACKLOG.md with ticket service
- No sudo in SSH sessions — write command, ask user to run it
