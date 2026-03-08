<!--
ts: 2026-03-06T18:00:00Z | git: pending | path: /opt/projects/tinyos-agent
-->

# STATUS

**Project:** TinyOS Agent | **Version:** 0.3.0 | **Updated:** 2026-03-06

## Overall Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Project Setup | Repo, Makefile, live-build config, package lists | ✅ Complete |
| 2. Agent TUI Core | Hardware detection, identity/auth, curses UI | ✅ Complete |
| 3. ISO Build Pipeline | End-to-end ISO generation and QEMU boot test | ✅ Complete (build #11) |
| 4. ShareMesh Architecture | Mesh networking, resource discovery, model sharing | ❌ Not started |
| 5. Multi-Architecture | ARM64, RISC-V support | ❌ Not started |

## What's Working (Tested)

### Agent Python Package (`agent/`)
- ✅ **25/25 Python unit tests pass** — hardware detection, identity, serialization
- ✅ Hardware detection: GPU (lspci, sysfs, nvidia-smi), CPU (lscpu), RAM, disks
- ✅ User identity: SQLite DB, bcrypt or sha256-fallback password hashing
- ✅ Curses TUI: splash screen, ASCII art, hardware display, name prompt, auth flow
- ✅ Main menu: hardware info, settings (password change), quit
- ✅ systemd service: auto-start on tty1 with autologin

### Build System
- ✅ Makefile with targets: deps, base-image, test-boot, test-boot-headless, clean
- ✅ live-build configuration: **Debian 13 Trixie**, amd64, GRUB 2, non-free firmware
- ✅ Package list: 88 packages including Vulkan 1.4.309, firmware, Python, build tools
- ✅ 8 chroot hooks: locale, kernel-modules, agent-user, autologin, llamacpp, fix-grub, install-agent, cleanup
- ✅ llama.cpp Vulkan build hook — **compiles successfully** from source (tag b8185) in Trixie chroot
- ✅ Agent install hook — systemd service installed and enabled
- ✅ QEMU available with KVM (user added to kvm group)
- ✅ **87/87 config tests pass**, **25/25 Python tests pass**

### ISO Build (Build #11 — 2026-03-08)
- ✅ ISO generated: 615MB (`tinyos-agent.iso`)
- ✅ All 8 chroot hooks execute successfully
- ✅ llama.cpp b8185 compiles with Vulkan backend inside chroot
- ✅ GRUB 2.12-9 boots → kernel → agent TUI on tty1
- ✅ Agent TUI auto-launches via systemd (tty1), fallback shell on tty2
- ✅ `llama-cli` and `llama-server` installed at `/usr/local/bin/`
- ✅ Vulkan 1.4.305 working (Mesa 25.0.7-2, llvmpipe in QEMU)
- ✅ Hardware detection: GPU, CPU, RAM, disks shown in TUI

### Scripts
- ✅ `build-llamacpp.sh` — Standalone llama.cpp Vulkan build from pinned tag
- ✅ `sync-agent.sh` — Copy agent code into live-build includes.chroot
- ✅ `test-gpu-detect.sh` — Verify Vulkan GPU detection with tiny GGUF model

## ISO Build Attempt History

| # | Date | Error | Fix | Result |
|---|------|-------|-----|--------|
| 1 | Mar 4 | Security repo 404 (`bookworm/updates`) | `LB_SECURITY="false"` | Fixed |
| 2 | Mar 4 | `Contents-amd64.gz` 404 | `LB_FIRMWARE_CHROOT="false"` | Fixed |
| 3 | Mar 5 | `firmware-nvidia-graphics` not found | Removed (firmware-misc-nonfree covers it) | Fixed |
| 4 | Mar 5 | `nouveau-firmware` not found (stale cache) | `lb clean --purge` | Fixed |
| 5 | Mar 5 | Hooks not executing (wrong directory) | Moved hooks from `config/hooks/chroot/` → `config/hooks/` | Fixed |
| 6 | Mar 5 | `visudo: command not found` in chroot | Graceful skip + added `sudo` to package list | Fixed |
| 7 | Mar 6 | Vulkan 1.3.239 too old for llama.cpp b8185 | **Upgraded bookworm → trixie** (Vulkan 1.4.309) | Fixed |
| 8 | Mar 6 | `grub-mkimage` missing `-p /boot/grub` | `grub2` bootloader + grub-mkimage wrapper hook | Fixed |
| 9 | Mar 7 | grub-mkimage wrapper in chroot, not host | Patch host `/usr/lib/live/build/lb_binary_iso` | Fixed |
| 10 | Mar 7 | `normal.mod` not found (modules not in core.img) | Add `normal configfile linux search` to grub-mkimage | Fixed |
| 11 | Mar 8 | getty@tty1 competing with agent service | Mask getty@tty1, agent owns tty1 directly | Fixed ✅ |

## Key Learnings (live-build 3.0 on Ubuntu)

1. **Hooks go in `config/hooks/*.chroot`** (flat), NOT `config/hooks/chroot/` (subdirs are for newer lb)
2. **`--security false`** flag is ignored by lb 3.0 — must edit `config/chroot` directly
3. **`LB_FIRMWARE_CHROOT`** auto-detection downloads `Contents-amd64.gz` which doesn't exist in modern repos
4. **`--bootloader grub`** = GRUB Legacy (stage2_eltorito), **`--bootloader grub2`** = GRUB 2
5. **GRUB 2.12+ requires `-p /boot/grub`** in grub-mkimage — lb 3.0 doesn't pass it
6. **Debian bookworm (2023) is too old** for modern LLM tooling — Vulkan 1.3.239 vs llama.cpp needing 1.3.275+
7. **Always check dependency versions** before choosing a base OS — would have saved 3+ build attempts
8. **`lb clean` without `--purge`** keeps stale chroot state — use `--purge` when config changes

## Dependencies

| Component | Version | Source |
|-----------|---------|--------|
| Debian base | **trixie (13)** | live-build ISO |
| Python | 3.x (system) | Debian package |
| llama.cpp | b8185 | Built from source (Vulkan) |
| Vulkan SDK | **1.4.309** | Debian trixie |
| Kernel | **6.12.63** | Debian trixie |
| live-build | 3.0~a57-1 | Build host (Ubuntu) |
| QEMU | 8.2.2 | Build host |
