# TinyOS Agent — BACKLOG

Work items synced with ticket service.

**Ticket API:** `http://192.168.42.21:5401`
**Web UI:** `http://192.168.42.21:5549`

## Priority Queue

### High Priority (Current Sprint)

- [ ] **Agent TUI** — Interactive Python agent: boot greeting, name prompt, password auth for known users
  - Auto-starts on tty1 after boot
  - Friendly introduction ("Hi, I'm TinyOS Agent...")
  - Asks user name, stores in local DB
  - Known users prompted for password
  - Systemd service for auto-start

- [ ] **Hardware Detection** — Auto-detect and report GPU, CPU, RAM, storage on boot
  - GPU: vendor, model, VRAM (via Vulkan/sysfs)
  - CPU: model, cores, frequency
  - RAM: total, available
  - Storage: disks, partitions, free space
  - Output as structured JSON for mesh sharing

### Medium Priority (Next Sprint)

- [ ] **Network Scanner** — Scan WiFi, Bluetooth, mDNS for nearby devices
  - WiFi: available networks, signal strength
  - Bluetooth: discoverable devices
  - mDNS/Avahi: other TinyOS agents on LAN
  - Report connectable hardware

- [ ] **Mesh Protocol** — Define sharemesh.org P2P resource sharing protocol
  - Resource advertisement (what I have)
  - Resource requests (what I need)
  - Job routing and scheduling
  - Trust/identity model

### Low Priority / Future

- [ ] **Voice Interaction** — Upgrade TUI to include voice input/output
- [ ] **Avatar Visualization** — Visual agent representation
- [ ] **GPU Job Queue** — Accept and execute GPU compute jobs from mesh
- [ ] **Web Dashboard** — sharemesh.org status dashboard
- [ ] **Multi-node Orchestration** — Coordinate workloads across mesh

## Completed

- [x] **T000010** — Configure Debian live-build environment and base OS image (v0.1.0)
- [x] **llama.cpp build script** — Vulkan backend compilation
- [x] **GPU detection tests** — Vulkan device auto-detection verification
- [x] **Static test suite** — 78 config tests (all passing)
