<!--
ts: 2026-03-04T10:00:00Z | git: a8ee2e2 | path: /opt/projects/tinyos-agent
-->

# VERSIONS

Multi-environment version tracking for TinyOS Agent.

**Source of Truth:** `/opt/projects/tinyos-agent`

## Environments

### Development (Build Host — SPI Server)
- **Location:** `/opt/projects/tinyos-agent`
- **Git Branch:** main
- **Git Commit:** a8ee2e2
- **Last Updated:** 2026-03-04
- **Status:** Active development (Phase 2 complete, Phase 3 in progress)
- **Access:** Direct filesystem (SPI LAN: 192.168.42.21, Tailscale: 100.123.174.47)
- **Build host OS:** Ubuntu (live-build 3.0~a57-1)
- **No running service** — TinyOS Agent runs on target hardware from USB, not on SPI

### Target (USB Boot — Any x86_64 Machine)
- **Delivery:** Bootable ISO (`tinyos-agent.iso`) flashed to USB
- **ISO Status:** Not yet built (see BACKLOG ISO-001)
- **Base:** Debian bookworm (live image, amd64)
- **Boot:** UEFI via GRUB

## Component Versions

| Component | Version | Source | Notes |
|-----------|---------|--------|-------|
| TinyOS Agent | 0.2.0 | `agent/__init__.py` | Python package version |
| llama.cpp | b8185 | `vendor/llama.cpp/VERSION` | Pinned tag, built with Vulkan |
| Debian base | bookworm | live-build config | Stable release |
| Python | 3.x (system) | Debian package | Exact version depends on bookworm |
| SQLite | system | Debian package | User identity database |

## Build Host Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| live-build | 3.0~a57-1 | ISO builder |
| QEMU | 8.2.2 | Boot testing |
| OVMF | system | UEFI firmware for QEMU |
| KVM | available | Hardware acceleration |

## ISO Package Summary

Key packages included in the live image (see `build/config/package-lists/tinyos.list.chroot` for full list):

| Category | Packages |
|----------|----------|
| GPU/Vulkan | libvulkan1, vulkan-tools, mesa-vulkan-drivers, mesa-utils |
| Firmware | firmware-linux, firmware-amd-graphics, firmware-nvidia-graphics, firmware-iwlwifi |
| Python | python3, python3-pip, python3-venv, python3-requests, python3-yaml |
| Network | iproute2, openssh-server, avahi-daemon, nftables |
| Build tools | git, make, gcc, cmake (for on-device llama.cpp rebuilds) |
| Storage | parted, lvm2, cryptsetup, squashfs-tools |

## Version History

| Version | Date | Commit | Notes |
|---------|------|--------|-------|
| 0.2.0 | 2026-03-03 | a8ee2e2 | Phase 2: Agent TUI, hardware detect, identity, lb_config fix |
| 0.1.0 | 2026-03-03 | 02474cf | Initial commit: project setup, live-build config, Makefile |
