# TinyOS Agent — STATUS

## Current State: Phase 1 Complete (Base Image)

**Last updated:** 2026-03-03
**Current version:** v0.1.0
**Active ticket:** T000010 (complete), next: Phase 2 Agent TUI

## What Works

- [x] Debian bookworm live-build configuration (UEFI + BIOS)
- [x] Package list: 80+ packages (Python, Vulkan, firmware, networking)
- [x] GPU driver support: AMD (amdgpu), NVIDIA (nouveau), Intel (i915), virtio
- [x] Auto-login as `agent` user on tty1
- [x] Scoped sudoers for system commands
- [x] llama.cpp build script with Vulkan backend
- [x] GPU detection test script
- [x] 78 static config tests (all passing)
- [x] QEMU boot test targets (interactive + headless CI)
- [x] Makefile with full build pipeline

## What's Next

- [ ] **Phase 2: Agent TUI** — Python interactive agent (introduce, ask name, auth)
- [ ] **Phase 3: Network Scanner** — WiFi, Bluetooth, mDNS device discovery
- [ ] **Phase 4: Mesh Sharing** — Resource advertisement and job routing (sharemesh.org)

## Blockers

- `make base-image` requires `sudo` + `live-build` on build host (not available in SSH agent)
- ISO not yet built — needs manual build on host with root access

## Environment

| Environment | Location | Status |
|------------|----------|--------|
| Development | `/opt/projects/tinyos-agent/` | Active |
| Build output | `build/tinyos-agent.iso` | Not yet built |
| Acceptance | N/A (USB image) | — |
| Production | USB boot media | — |

## Recent Sessions

### 2026-03-03 (Session 2) — Bootstrap + Agent TUI
- Set up SPI bootstrap documentation
- Initialized git repo, pushed to GitHub
- Started Phase 2: Interactive agent TUI

### 2026-03-03 (Session 1) — Base Image Setup
- Created Debian live-build configuration (v0.1.0)
- Makefile, chroot hooks, package lists, GPU support
- llama.cpp build script + GPU detection tests
- 78 static tests passing
