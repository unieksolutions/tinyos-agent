<!--
ts: 2026-03-04T10:00:00Z | git: a8ee2e2 | path: /opt/projects/tinyos-agent
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

- [ ] **ISO-001** — Fix live-build ISO end-to-end build
  - Fix hook ordering: 0060-install-agent runs after 0050-cleanup
  - Fix or move 10-llamacpp.hook.chroot into correct hooks/chroot/ directory
  - Align test_config.sh expectations with lb_config lb 3.0 syntax
  - Run `make base-image` and verify ISO boots in QEMU
  - **Estimate:** 2-4 hours

- [ ] **ISO-002** — Verify QEMU boot + agent TUI launches
  - Boot ISO with `make test-boot`
  - Confirm autologin → agent TUI splash → hardware detect → greeting
  - Test identity flow (new user, returning user, password)
  - **Depends on:** ISO-001

### P1 — High Priority (next milestones)

- [ ] **MESH-001** — Design ShareMesh architecture
  - Define mesh discovery protocol (mDNS/avahi, custom UDP broadcast, or both)
  - Define resource advertisement: what each node publishes (GPU model, VRAM, loaded models)
  - Define model serving: llama-server on GPU node, clients connect via HTTP API
  - Define VRAM negotiation: how nodes request/release GPU capacity
  - Write ARCHITECTURE.md ShareMesh section
  - **Estimate:** 4-6 hours (design only)

- [ ] **MESH-002** — Network discovery proof-of-concept
  - Use avahi (already in package list) for mDNS service advertisement
  - Each TinyOS node advertises: `_sharemesh._tcp` service with TXT records (GPU, VRAM, hostname)
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
  - Scan local network for other TinyOS/ShareMesh nodes
  - Show: hostname, IP, GPU type, VRAM, status
  - **Depends on:** MESH-002

- [ ] **AGENT-002** — Implement "Mesh Status" menu (replace placeholder)
  - Show: connected nodes, active model, VRAM usage, inference throughput
  - **Depends on:** MESH-003

- [ ] **AGENT-003** — Add "Chat" menu item
  - Local or remote inference via llama-cli/llama-server
  - Simple text chat interface in curses TUI
  - Auto-select best available model/node

- [ ] **BUILD-001** — Fix 4 failing config tests
  - Update test_config.sh to match lb 3.0 syntax (--bootloader vs --bootloaders)
  - Fix or acknowledge linux-packages format difference
  - Investigate "hardcoded password" false positive
  - Rename 0060 hook or renumber cleanup to 0099

### P3 — Low Priority / Future

- [ ] **ARCH-001** — ARM64 support (Raspberry Pi 4/5, Jetson)
  - Research: live-build for ARM64, or switch to custom rootfs builder
  - Vulkan on ARM: Mali/Panfrost vs NVIDIA Jetson
  - Cross-compilation of llama.cpp for aarch64

- [ ] **ARCH-002** — RISC-V support
  - Experimental, depends on Vulkan driver availability

- [ ] **AGENT-004** — Web UI alongside TUI
  - Flask/FastAPI dashboard accessible via browser
  - Same functionality as TUI but for remote management

- [ ] **MESH-004** — Model management
  - Download/cache GGUF models on nodes
  - Advertise available models in mesh
  - Auto-distribute models to best-fit nodes based on VRAM

- [ ] **MESH-005** — Security layer
  - Node authentication (shared key, TLS certificates)
  - Encrypt mesh traffic
  - Access control for model serving

## Completed

- [x] **INIT-001** — Project setup: repo, Makefile, live-build config, package lists
- [x] **AGENT-TUI** — Phase 2 Agent TUI: curses splash, hardware detect, identity/auth, main menu
- [x] **BUILD-LLAMA** — llama.cpp Vulkan build hook (chroot hook, standalone script)
- [x] **TEST-001** — 25 Python unit tests for hardware + identity modules
- [x] **TEST-002** — 82-point config validation test suite (test_config.sh)
- [x] **LB-FIX** — Fix lb_config for live-build 3.0 (Ubuntu host compatibility)
