<!--
ts: 2026-03-06T18:00:00Z | git: pending | path: /opt/projects/tinyos-agent
-->

# BACKLOG

Work items and priorities for TinyOS Agent.

**⚠️ IMPORTANT:** All items in this BACKLOG.md should be synchronized with the ticket service.
**Ticket service is leading** - use the API to create, update, and manage work items:

- **API Base:** `http://192.168.42.21:5401`
- **Web UI:** `http://192.168.42.21:5549`
- **List tickets:** `GET /tickets?project=tinyos-agent&state=todo,doing`
- **Create ticket:** `POST /tickets` with JSON body
- **Update ticket:** `PATCH /tickets/{ticket_id}` with JSON body

## Priority Queue

### P0 — Critical (blocking progress)

- [ ] **ISO-003** — Verify GRUB 2 boot + agent TUI auto-launch
  - Build #9 is running with grub-mkimage `-p /boot/grub` wrapper fix
  - Boot ISO in QEMU, verify: GRUB menu → kernel boot → autologin → agent TUI
  - If TUI doesn't auto-launch, check systemd service status
  - **Estimate:** 1-2 hours (mostly build wait time)

### P1 — High Priority (next milestones)

- [ ] **ISO-004** — Add serial console support for headless testing
  - Add `console=ttyS0,115200` to GRUB boot params for serial output
  - Enables automated QEMU boot verification without VNC
  - **Estimate:** 1 hour

- [ ] **MESH-001** — Design ShareMesh architecture
  - Define mesh discovery protocol (mDNS/avahi, custom UDP broadcast, or both)
  - Define resource advertisement: what each node publishes (GPU model, VRAM, loaded models)
  - Define model serving: llama-server on GPU node, clients connect via HTTP API
  - Define VRAM negotiation: how nodes request/release GPU capacity
  - Write ARCHITECTURE.md ShareMesh section
  - **Estimate:** 4-6 hours (design only)

- [ ] **MESH-002** — Network discovery proof-of-concept
  - Use avahi (already in package list) for mDNS service advertisement
  - Each TinyOS node advertises: `_sharemesh._tcp` service with TXT records
  - Agent discovers nearby nodes and shows them in "Network Scan" menu
  - **Depends on:** MESH-001
  - **Estimate:** 4-6 hours

- [ ] **MESH-003** — Distributed inference proof-of-concept
  - Best-GPU node runs `llama-server` with a GGUF model loaded
  - Other nodes connect as clients via HTTP API
  - Agent menu: "Chat" option that routes to local or remote llama-server
  - **Depends on:** MESH-002
  - **Estimate:** 6-8 hours

### P2 — Medium Priority

- [ ] **AGENT-001** — Implement "Network Scan" menu (replace placeholder)
  - **Depends on:** MESH-002

- [ ] **AGENT-002** — Implement "Mesh Status" menu (replace placeholder)
  - **Depends on:** MESH-003

- [ ] **AGENT-003** — Add "Chat" menu item
  - Local or remote inference via llama-cli/llama-server
  - Simple text chat interface in curses TUI

- [ ] **BUILD-002** — Add UEFI boot support to ISO
  - Current ISO is BIOS-only (GRUB 2 i386-pc)
  - Need EFI System Partition with grub-efi-amd64 for modern hardware
  - May need xorriso instead of genisoimage for dual BIOS+UEFI

### P3 — Low Priority / Future

- [ ] **ARCH-001** — ARM64 support (Raspberry Pi 4/5, Jetson)
- [ ] **ARCH-002** — RISC-V support
- [ ] **AGENT-004** — Web UI alongside TUI
- [ ] **MESH-004** — Model management (download, cache, distribute GGUF models)
- [ ] **MESH-005** — Security layer (node auth, TLS, access control)

## Completed

- [x] **INIT-001** — Project setup: repo, Makefile, live-build config, package lists
- [x] **AGENT-TUI** — Phase 2 Agent TUI: curses splash, hardware detect, identity/auth, main menu
- [x] **BUILD-LLAMA** — llama.cpp Vulkan build hook (compiles b8185 in trixie chroot)
- [x] **TEST-001** — 25 Python unit tests for hardware + identity modules
- [x] **TEST-002** — 87-point config validation test suite (test_config.sh)
- [x] **LB-FIX** — Fix lb_config for live-build 3.0 (Ubuntu host compatibility)
- [x] **ISO-001** — Fix hook ordering (cleanup last), move hooks to flat `config/hooks/`
- [x] **ISO-002** — Fix lb 3.0 incompatibilities (security repo, firmware auto-detect, package names)
- [x] **BUILD-001** — Fix all config tests for lb 3.0 syntax (87/87 pass)
- [x] **DISTRO-001** — Upgrade base OS from Debian 12 bookworm → Debian 13 trixie (Vulkan 1.4.309)
