# TinyOS Agent — Version History

## v0.1.0 — 2026-03-03

**Ticket:** T000010 — Configure Debian live-build environment and base OS image
**Stage:** Initial configuration (developer → tester → reviewer → deployer pipeline)

### Deployed Configuration

| Property | Value |
|----------|-------|
| Base OS | Debian bookworm (stable) |
| Architecture | x86_64 (amd64) |
| Desktop | None (headless) |
| Kernel | `linux-image-amd64` + `linux-headers-amd64` |
| Boot | UEFI (GRUB2) + BIOS fallback |
| Auto-login | `agent` user on tty1 (agetty) |
| Timezone | UTC |
| Locale | `en_US.UTF-8` |
| ISO type | iso-hybrid (USB bootable) |

### Deliverables

- `build/lb_config` — `lb config` initialisation script (HTTPS mirrors, bookworm)
- `build/config/package-lists/tinyos.list.chroot` — 80+ packages (Python, Vulkan, firmware)
- `build/config/hooks/chroot/0010-locale.hook.chroot` — locale/keyboard/timezone
- `build/config/hooks/chroot/0020-kernel-modules.hook.chroot` — GPU/DRM kernel modules
- `build/config/hooks/chroot/0030-agent-user.hook.chroot` — agent user + scoped sudoers
- `build/config/hooks/chroot/0040-autologin.hook.chroot` — agetty autologin on tty1
- `build/config/hooks/chroot/0050-cleanup.hook.chroot` — apt cache + doc cleanup
- `build/config/hooks/live/0010-first-boot.hook.live` — first-boot service setup
- `Makefile` — `deps`, `base-image`, `test-boot`, `test-boot-headless`, `clean`, `info`
- `tests/test_config.sh` — 78-test static analysis suite (0 failures)
- `README.md` — build and usage documentation

### Changes Applied in Deployment

| Issue | Fix Applied |
|-------|-------------|
| Hardcoded OVMF path `/usr/share/ovmf/OVMF.fd` | Auto-detection via `OVMF_FW=$(firstword $(wildcard ...))` across 5 candidate paths |
| Dead `QEMU_DISK_SIZE` Makefile variable | Removed; QEMU boot tests are CD-ROM only (no emulated disk needed) |
| HTTP mirrors in `lb_config` | Upgraded all 5 mirror URLs to `https://` |
| Bare `NOPASSWD: ALL` sudoers | Scoped to `Cmnd_Alias TINYOS_CMDS` for required commands only |
| Missing in-repo test suite | Added `tests/test_config.sh` — 78 static tests, 9 groups |

### Test Results (Deployment Validation)

```
Results: 78 passed, 0 failed, 2 skipped
STATUS: PASS

Skipped (require root/install):
  - live-build not installed (requires: sudo apt-get install live-build)
  - debootstrap not installed (requires: sudo apt-get install debootstrap)

Infrastructure confirmed present:
  - qemu-system-x86_64: QEMU 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1.12)
  - /dev/kvm: present (KVM hardware acceleration available)
  - OVMF firmware: /usr/share/ovmf/OVMF.fd
```

### Remaining Work

- **QEMU boot verification** (`make test-boot-headless`): Blocked on installing
  `live-build` + `debootstrap` (requires passwordless `sudo` or root access on
  build host). Run the following on a host with root access:

  ```bash
  sudo apt-get install -y live-build debootstrap qemu-system-x86 ovmf
  cd /opt/projects/tinyos-agent
  make base-image
  make test-boot-headless
  ```

### Backup Location

`/opt/backups/tinyos-agent_2026-03-03T10-45-43/`

---

## Planned Future Versions

- **v0.2.0** — Agent runtime installation (Python packages, systemd services)
- **v0.3.0** — GPU compute stack (ROCm / CUDA / Vulkan compute)
- **v1.0.0** — First bootable, verified USB image with full TinyOS Agent stack
