<!--
ts: 2026-03-04T10:00:00Z | git: a8ee2e2 | path: /opt/projects/tinyos-agent
-->

# STATUS

**Project:** TinyOS Agent | **Version:** 0.2.0 | **Updated:** 2026-03-04

## Overall Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Project Setup | Repo, Makefile, live-build config, package lists | ✅ Complete |
| 2. Agent TUI Core | Hardware detection, identity/auth, curses UI | ✅ Complete |
| 3. ISO Build Pipeline | End-to-end ISO generation and QEMU boot test | 🟡 Partially done |
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
- ✅ live-build configuration: Debian bookworm, amd64, UEFI (grub), non-free firmware
- ✅ Package list: 80+ packages including Vulkan, firmware, Python, build tools
- ✅ Chroot hooks: locale, kernel modules, agent user, autologin, cleanup, agent install
- ✅ llama.cpp Vulkan build hook (compiles from source at tag b8185 during image build)
- ✅ QEMU available with KVM and OVMF firmware
- ✅ **76/80 config tests pass** (4 known mismatches between test expectations and lb_config format)

### Scripts
- ✅ `build-llamacpp.sh` — Standalone llama.cpp Vulkan build from pinned tag
- ✅ `sync-agent.sh` — Copy agent code into live-build includes.chroot
- ✅ `test-gpu-detect.sh` — Verify Vulkan GPU detection with tiny GGUF model

## What's NOT Working

### ISO Build
- ❌ No ISO has been successfully built end-to-end yet
- ❌ `lb_config` was adapted for live-build 3.0 (Ubuntu) but not fully validated
- ❌ 4 config test failures:
  - `--bootloaders grub-efi` — lb_config uses `--bootloader grub` (lb 3.0 syntax)
  - `--linux-packages linux-image-amd64` — lb_config uses `linux-image linux-headers`
  - Possible hardcoded password false positive in build dir
  - Cleanup hook ordering: `0060-install-agent` runs after `0050-cleanup`

### Agent Placeholders
- ❌ "Network Scan" menu item — shows "Coming soon"
- ❌ "Mesh Status" menu item — shows "Coming soon"

### ShareMesh
- ❌ No architecture designed yet
- ❌ No network discovery (mDNS/avahi is in package list but not used)
- ❌ No llama.cpp server mode integration
- ❌ No resource advertisement/negotiation protocol

## Known Issues

1. **Hook ordering:** `0060-install-agent.hook.chroot` runs AFTER `0050-cleanup.hook.chroot`, which means cleanup runs before agent install. The llama.cpp hook (`10-llamacpp.hook.chroot`) is in `config/hooks/` not `config/hooks/chroot/` — may not execute in correct order.
2. **Test expectations mismatch:** `test_config.sh` expects `--bootloaders grub-efi` and `--linux-packages linux-image-amd64` but `lb_config` was updated for live-build 3.0 syntax which uses different flag names.
3. **live-build version:** SPI build host runs live-build 3.0~a57-1 (Ubuntu), which has different CLI flags than Debian's live-build. Configuration adapted but untested.

## Dependencies

| Component | Version | Source |
|-----------|---------|--------|
| Debian base | bookworm | live-build ISO |
| Python | 3.x (system) | Debian package |
| llama.cpp | b8185 | Built from source (Vulkan) |
| live-build | 3.0~a57-1 | Build host (Ubuntu) |
| QEMU | 8.2.2 | Build host |
| OVMF | system | UEFI firmware for QEMU |

## Git History

```
a8ee2e2 Fix lb_config for live-build 3.0 (Ubuntu compatibility)
fb383a6 Update STATUS.md: Phase 2 agent TUI core complete
27f1efc Add Phase 2 Agent TUI: hardware detect, identity, curses UI
02474cf Initial commit: TinyOS Agent v0.1.0 + SPI bootstrap docs
```
