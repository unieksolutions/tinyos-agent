<!--
Session continuation prompt for TinyOS Agent
Updated: 2026-03-06T18:00:00Z
Context window: ~93% used (write NEXT_SESSION and commit)
-->

# Next Session: TinyOS Agent

## Session Context

You are continuing work on the **TinyOS Agent** project at `/opt/projects/tinyos-agent`.

**This session (2026-03-04 to 2026-03-06) focused on ISO build pipeline — 9 build attempts:**

### Build Attempt History (CRITICAL — don't repeat these!)

| # | Date | Error | Fix |
|---|------|-------|-----|
| 1 | Mar 4 | Security repo 404 (`bookworm/updates`) | `LB_SECURITY="false"` in config/chroot |
| 2 | Mar 4 | `Contents-amd64.gz` 404 (firmware auto-detect) | `LB_FIRMWARE_CHROOT="false"` in config/binary |
| 3 | Mar 5 | `firmware-nvidia-graphics` not found | Removed — doesn't exist in Debian, covered by firmware-misc-nonfree |
| 4 | Mar 5 | `nouveau-firmware` not found (stale cache) | `lb clean --purge` needed, not just `lb clean` |
| 5 | Mar 5 | **Hooks not executing at all** | lb 3.0 uses flat `config/hooks/*.chroot`, NOT `config/hooks/chroot/` subdirs |
| 6 | Mar 5 | `visudo: command not found` in chroot | Graceful skip if not available + added `sudo` to package list |
| 7 | Mar 6 | **Vulkan 1.3.239 too old** for llama.cpp b8185 | Upgraded bookworm → **trixie** (Debian 13, Vulkan 1.4.309) |
| 8 | Mar 6 | `grub-mkimage` missing `-p /boot/grub` prefix | Changed `--bootloader grub` → `grub2` + wrapper hook `0055-fix-grub-mkimage` |
| 9 | Mar 6 | **Building now — pending result** | All fixes combined, full --purge rebuild |

### What succeeded in build #8 (before GRUB failure):
- ✅ All 8 chroot hooks executed
- ✅ llama.cpp b8185 compiled with Vulkan in trixie chroot
- ✅ Agent installed, systemd service enabled
- ✅ 615MB ISO generated
- ✅ QEMU booted to `agent@tinyos:~$` shell with autologin
- ❌ GRUB boot image broken (grub-mkimage missing prefix)

---

## Immediate Next Steps

### 1. Check build #9 result
```bash
tail -20 /opt/projects/tinyos-agent/build/build.log
ls -lh /opt/projects/tinyos-agent/build/tinyos-agent.iso
```

If build #9 succeeded:
- Copy ISO: `cp build/chroot/binary.hybrid.iso build/tinyos-agent.iso`
- Boot test: `sg kvm -c "qemu-system-x86_64 -enable-kvm -m 2G -smp 2 -cdrom build/tinyos-agent.iso -boot d -vnc :1 -monitor unix:/tmp/qemu-monitor.sock,server,nowait -daemonize"`
- Take screenshot via Python QEMU monitor (see below)
- Verify: GRUB menu → kernel boot → autologin → agent TUI

If build #9 failed on GRUB again:
- The `0055-fix-grub-mkimage.hook.chroot` wraps grub-mkimage in the chroot
- But `lb_binary_iso` runs `binary.sh` which calls grub-mkimage during binary stage (AFTER chroot hooks)
- The wrapper should persist since it replaces the binary in the chroot
- If it doesn't work: consider patching `/usr/lib/live/build/lb_binary_iso` line 172 to add `-p /boot/grub`

### 2. After successful boot
- **Commit all changes and push** (nothing committed yet this session!)
- Verify agent TUI auto-launches (systemd service)
- Check llama-cli and llama-server are installed: `ls /usr/local/bin/llama-*`
- Run `vulkaninfo` to verify Vulkan driver detection

### 3. Then move to ShareMesh (MESH-001)
- Design the mesh architecture
- mDNS/avahi for node discovery
- llama-server for model serving

---

## QEMU Screenshot Method (no VNC client needed)

```python
# Connect to QEMU monitor and take screenshot
import socket, time
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect('/tmp/qemu-monitor.sock')
time.sleep(0.3); sock.recv(4096)
sock.sendall(b'screendump /tmp/qemu-screen.ppm\n')
time.sleep(2); sock.recv(4096)
sock.close()

# Convert PPM to PNG (requires PIL)
from PIL import Image
Image.open('/tmp/qemu-screen.ppm').save('/tmp/qemu-screen.png')
# Then use Read tool to view the PNG
```

To send keystrokes:
```python
# Special keys: space='spc', hyphen='minus', slash='slash', enter='ret'
sock.sendall(b'sendkey ret\n')  # Enter key
```

---

## Project Structure

```
/opt/projects/tinyos-agent/
├── agent/          # Python agent: TUI, hardware, identity
├── build/          # Debian live-build tree
│   ├── lb_config               # live-build configuration script
│   ├── config/binary           # Binary stage config (LB_BOOTLOADER="grub2")
│   ├── config/bootstrap        # Bootstrap config (LB_DISTRIBUTION="trixie")
│   ├── config/chroot           # Chroot config (LB_SECURITY="false")
│   ├── config/common           # Common config
│   ├── config/hooks/           # FLAT directory (lb 3.0!) — all *.hook.chroot here
│   │   ├── 0010-locale.hook.chroot
│   │   ├── 0020-kernel-modules.hook.chroot
│   │   ├── 0030-agent-user.hook.chroot
│   │   ├── 0040-autologin.hook.chroot
│   │   ├── 0050-llamacpp.hook.chroot        # Heavy: clones + compiles llama.cpp
│   │   ├── 0055-fix-grub-mkimage.hook.chroot # Wraps grub-mkimage to add -p
│   │   ├── 0060-install-agent.hook.chroot
│   │   ├── 0090-cleanup.hook.chroot          # MUST be last
│   │   └── 0010-first-boot.hook.live
│   ├── config/includes.chroot/ # Files copied into chroot (agent source)
│   └── config/package-lists/tinyos.list.chroot  # 88 packages
├── scripts/        # Build scripts (llama.cpp, sync-agent, test-gpu)
├── tests/          # Python tests + config validation (87/87 pass)
├── vendor/         # Pinned dependency versions (llama.cpp b8185)
└── Makefile        # Build system entry point
```

---

## Key Technical Details

- **Base OS:** Debian 13 Trixie (stable, released Aug 2025)
- **Vulkan:** 1.4.309 (mesa-vulkan-drivers: RADV/ANV/lavapipe)
- **Kernel:** 6.12.63
- **llama.cpp:** b8185 with GGML_VULKAN=ON
- **live-build:** 3.0~a57-1 (Ubuntu host) — many quirks, see build history
- **Bootloader:** GRUB 2 (BIOS only, no UEFI yet)
- **Build command:** `cd build && sudo lb clean --purge && sudo lb build 2>&1 | tee build.log`
- **Build time:** ~30-40 min (llama.cpp compile is longest)
- **KVM access:** user `uniek` added to `kvm` group, use `sg kvm -c "..."` for QEMU

---

## Important Constraints

- **sudo required** for `lb build` — cannot run in Claude agent directly
- **live-build 3.0 quirks** — see build history, many flags/paths differ from docs
- **Always use `--purge`** when config changes — `lb clean` alone keeps stale state
- **Commit AND push** after completing work (nothing committed this session yet!)
- **No VNC client** on user's devices — use QEMU monitor screendump method

---

## Uncommitted Changes (MUST commit next session)

All work from this session is uncommitted:
- Hook ordering fix (flat directory)
- Config test updates (87/87)
- Trixie upgrade (bookworm → trixie)
- Package list fixes (firmware, sudo)
- grub2 bootloader config
- grub-mkimage wrapper hook
- STATUS.md, BACKLOG.md, NEXT_SESSION.md updates

```bash
cd /opt/projects/tinyos-agent
git add -A
git commit -m "Phase 3: ISO build pipeline - Trixie, all hooks, grub2 fix

- Upgrade base OS: bookworm → trixie (Vulkan 1.4.309, kernel 6.12)
- Fix lb 3.0 hook discovery: flat config/hooks/ directory
- Fix 8 build issues across 9 attempts (see STATUS.md)
- All 8 chroot hooks execute: locale, kernel-modules, agent-user,
  autologin, llamacpp (Vulkan), grub-mkimage fix, install-agent, cleanup
- llama.cpp b8185 compiles successfully with Vulkan backend
- 87/87 config tests pass, 25/25 Python tests pass
- 615MB ISO generated, boots in QEMU with autologin

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push
```
