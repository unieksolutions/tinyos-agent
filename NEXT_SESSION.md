<!--
Session continuation prompt for TinyOS Agent
Updated: 2026-03-04T10:00:00Z
Context window: ~30% used
-->

# Next Session: TinyOS Agent

## Session Context

You are continuing work on the **TinyOS Agent** project at `/opt/projects/tinyos-agent`.

**Recent Progress (2026-03-03 to 2026-03-04):**
- ✅ Phase 1: Project setup — repo, Makefile, live-build config, package lists
- ✅ Phase 2: Agent TUI — curses splash, hardware detection, identity/auth, main menu
- ✅ llama.cpp Vulkan build hook (compiles b8185 from source during ISO build)
- ✅ 25 Python unit tests pass, 76/80 config tests pass
- ✅ lb_config adapted for live-build 3.0 (Ubuntu build host)
- ✅ All documentation updated (README, STATUS, BACKLOG, ARCHITECTURE, VERSIONS)
- 🚧 ISO not yet built end-to-end (hook ordering issues)
- ❌ ShareMesh mesh networking not started

**Current Status:**
- Git: a8ee2e2 (main branch)
- No ISO built yet, no deployments
- Agent v0.2.0

---

## Priority Tasks

**P0 - CRITICAL (do immediately):**
1. **ISO-001** — Fix live-build ISO end-to-end
   - Fix hook ordering (0060-install-agent after 0050-cleanup, 10-llamacpp misplaced)
   - Run `make base-image` — needs sudo
   - Verify with `make test-boot` in QEMU
   - Estimate: 2-4 hours
   - Blockers: needs sudo for lb build

**P1 - HIGH (do soon):**
1. **MESH-001** — Design ShareMesh architecture
   - Mesh discovery (mDNS/avahi), resource advertisement, model serving via llama-server
   - Proof of concept: 2 nodes, GPU node serves model, client node connects
   - Estimate: 4-6 hours

**P2 - MEDIUM:**
1. **BUILD-001** — Fix 4 failing config tests (test expectations vs lb 3.0 syntax)
2. **AGENT-001** — Implement "Network Scan" menu (after mesh design)

See BACKLOG.md for complete list.

---

## Key Learnings from Previous Sessions

**What worked well:**
1. Modular agent design (hardware.py, identity.py, main.py) — clean separation
2. Comprehensive test suites (25 Python tests, 82 config tests)
3. Pinned llama.cpp version via vendor/llama.cpp/VERSION

**Issues discovered:**
1. live-build 3.0 (Ubuntu) has different CLI flags than Debian's version — `--bootloader` vs `--bootloaders`, no `--hostname`/`--username` flags
2. Hook ordering: 0060-install-agent runs after 0050-cleanup (needs fix)
3. 10-llamacpp.hook.chroot is in `config/hooks/` instead of `config/hooks/chroot/` — may not execute

**Design decisions:**
- Vulkan (not CUDA): Cross-vendor GPU support (AMD, NVIDIA, Intel)
- llama.cpp (not Ollama): Direct control, Vulkan backend, lean binary
- SQLite for user DB: Zero-config, embedded, works on live USB
- bcrypt with sha256 fallback: bcrypt not in Debian base, fallback for minimal installs

---

## Current Implementation State

**What's working (tested):**
- ✅ Agent TUI: splash, hardware display, identity flow, main menu
- ✅ Hardware detection: GPU (lspci/sysfs/nvidia-smi), CPU, RAM, disks
- ✅ User identity: SQLite DB with bcrypt/sha256 auth
- ✅ Build system: Makefile, live-build config, package lists, chroot hooks
- ✅ llama.cpp build script and chroot hook (Vulkan)

**What's not working yet:**
- ❌ ISO build (never completed successfully)
- ❌ Network Scan (placeholder)
- ❌ Mesh Status (placeholder)
- ❌ ShareMesh (not started)

**What's partially done:**
- 🚧 live-build config: adapted for lb 3.0 but not validated with actual build
- 🚧 Config tests: 76/80 pass, 4 failures from lb 3.0 syntax mismatch

---

## Project Structure Reminder

```
/opt/projects/tinyos-agent/
├── agent/          # Python agent: TUI, hardware, identity
├── build/          # Debian live-build tree (lb_config, hooks, packages)
├── scripts/        # Build scripts (llama.cpp, sync-agent, test-gpu)
├── tests/          # Python tests + config validation
├── vendor/         # Pinned dependency versions (llama.cpp b8185)
└── Makefile        # Build system entry point
```

**Critical files:**
- `agent/main.py` — TUI entry point (AgentTUI class)
- `build/lb_config` — live-build configuration
- `build/config/package-lists/tinyos.list.chroot` — ISO packages
- `build/config/hooks/chroot/*.hook.chroot` — Build hooks
- `vendor/llama.cpp/VERSION` — Pinned llama.cpp version

---

## Important Constraints

**Technical:**
- live-build needs sudo for `lb build` — ask user to run
- Build host is Ubuntu with live-build 3.0 (different flags than Debian)
- QEMU with KVM available for boot testing
- Agent must run on any x86_64 hardware (GPUs: AMD, NVIDIA, Intel, none)

**Process:**
- Always backup before changes (`/opt/backups/tinyos-agent_{timestamp}/`)
- Commit AND push regularly (git push after every commit)
- Update STATUS.md after completing work

---

## Commands to Get Started

```bash
cd /opt/projects/tinyos-agent
git status
git log --oneline -5
python3 -m pytest tests/test_agent.py -v    # Run Python tests
bash tests/test_config.sh                    # Run config tests
python3 -c "from agent.hardware import detect_all; print(detect_all().to_json())"
```

---

## Open Questions

1. Should we attempt the ISO build now or focus on ShareMesh architecture first?
2. For ShareMesh PoC: what model should we target? (small like TinyLlama 1B, or ambitious like Llama3 8B?)
3. Multi-arch: when to start ARM64 support?

---

**What would you like to work on first?**
