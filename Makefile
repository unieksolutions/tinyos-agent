# TinyOS Agent — Makefile
# ============================================================================
# Build system for TinyOS Agent USB live image (Debian bookworm, x86_64).
#
# Prerequisites (install on the build host before running any target):
#   sudo apt-get install -y live-build qemu-system-x86 ovmf
#
# Quick start:
#   make deps          # install build prerequisites
#   make base-image    # configure and build the ISO
#   make test-boot     # boot the ISO in QEMU to verify it reaches a shell
#   make clean         # remove build artefacts (keep config)
#   make clean-all     # remove everything including the generated ISO
# ============================================================================

SHELL           := /bin/bash
.SHELLFLAGS     := -euo pipefail -c

BUILD_DIR       := $(CURDIR)/build
ISO_NAME        := tinyos-agent.iso
ISO_PATH        := $(BUILD_DIR)/$(ISO_NAME)
LB_BINARY       := $(BUILD_DIR)/live-image-amd64.hybrid.iso
QEMU_MEM        := 2G
QEMU_CPUS       := 2

# Auto-detect UEFI firmware across common install locations
OVMF_CANDIDATES := /usr/share/ovmf/OVMF.fd \
                   /usr/share/OVMF/OVMF_CODE.fd \
                   /usr/share/qemu/OVMF.fd \
                   /usr/share/edk2-ovmf/x64/OVMF.fd \
                   /usr/share/edk2/ovmf/OVMF.fd
OVMF_FW         := $(firstword $(wildcard $(OVMF_CANDIDATES)))

# ── Top-level targets ─────────────────────────────────────────────────────────

.PHONY: all
all: base-image

# ── Dependency installation ───────────────────────────────────────────────────

.PHONY: deps
deps:
	@echo "==> Installing build prerequisites..."
	sudo apt-get update -qq
	sudo apt-get install -y \
	    live-build \
	    qemu-system-x86 \
	    ovmf \
	    isolinux \
	    syslinux-common \
	    xorriso \
	    squashfs-tools \
	    debootstrap
	@echo "==> Prerequisites installed."

# ── Base image build ──────────────────────────────────────────────────────────

.PHONY: base-image
base-image: $(BUILD_DIR)/lb_config
	@echo "==> Building TinyOS Agent base image..."
	@echo "    Build dir : $(BUILD_DIR)"
	@echo "    Output ISO: $(ISO_PATH)"
	@# Initialise lb config if not already done
	@# lb 3.0 creates config/common; newer lb creates .build/config
	@if [ ! -f "$(BUILD_DIR)/config/common" ] && [ ! -d "$(BUILD_DIR)/.build" ]; then \
	    echo "==> Running lb_config to initialise build configuration..."; \
	    cd $(BUILD_DIR) && sudo bash lb_config; \
	fi
	@# Run the actual build
	cd $(BUILD_DIR) && sudo lb build 2>&1 | tee build.log
	@# Rename the output ISO to our canonical name
	@if [ -f "$(LB_BINARY)" ]; then \
	    cp "$(LB_BINARY)" "$(ISO_PATH)"; \
	    echo "==> ISO ready: $(ISO_PATH)"; \
	    sha256sum "$(ISO_PATH)" | tee "$(ISO_PATH).sha256"; \
	else \
	    echo "ERROR: Expected ISO not found at $(LB_BINARY)"; \
	    echo "       Check $(BUILD_DIR)/build.log for details."; \
	    exit 1; \
	fi
	@echo "==> base-image target complete."

# ── QEMU boot test ────────────────────────────────────────────────────────────

.PHONY: test-boot
test-boot: $(ISO_PATH)
	@echo "==> Booting $(ISO_NAME) in QEMU..."
	@echo "    QEMU will open in the current terminal."
	@echo "    The image should boot to a shell automatically (autologin on tty1)."
	@echo "    Press Ctrl-A X to exit QEMU when verified."
	@echo ""
	@if [ -z "$(OVMF_FW)" ]; then echo "ERROR: OVMF firmware not found. Run: sudo apt-get install ovmf"; exit 1; fi
	qemu-system-x86_64 \
	    -enable-kvm \
	    -m $(QEMU_MEM) \
	    -smp $(QEMU_CPUS) \
	    -bios "$(OVMF_FW)" \
	    -cdrom "$(ISO_PATH)" \
	    -boot d \
	    -vga virtio \
	    -display curses \
	    -serial mon:stdio \
	    -no-reboot

.PHONY: test-boot-headless
test-boot-headless: $(ISO_PATH)
	@echo "==> Booting $(ISO_NAME) in QEMU (headless serial, timeout 120s)..."
	@echo "    Waiting for 'tinyos login' prompt on serial console..."
	@if [ -z "$(OVMF_FW)" ]; then echo "ERROR: OVMF firmware not found. Run: sudo apt-get install ovmf"; exit 1; fi
	timeout 120 qemu-system-x86_64 \
	    -enable-kvm \
	    -m $(QEMU_MEM) \
	    -smp $(QEMU_CPUS) \
	    -bios "$(OVMF_FW)" \
	    -cdrom "$(ISO_PATH)" \
	    -boot d \
	    -nographic \
	    -serial mon:stdio \
	    -no-reboot 2>&1 | tee /tmp/qemu-boot.log & \
	QPID=$$!; \
	echo "    QEMU PID: $$QPID"; \
	for i in $$(seq 1 60); do \
	    if grep -q "tinyos login\|agent@tinyos" /tmp/qemu-boot.log 2>/dev/null; then \
	        echo "==> BOOT VERIFIED: Shell reached after ~$$((i*2))s"; \
	        kill $$QPID 2>/dev/null; \
	        exit 0; \
	    fi; \
	    sleep 2; \
	done; \
	echo "ERROR: Boot verification timed out. Check /tmp/qemu-boot.log."; \
	kill $$QPID 2>/dev/null; \
	exit 1

# ── Rebuild targets ───────────────────────────────────────────────────────────

.PHONY: rebuild
rebuild: clean base-image

.PHONY: rebuild-chroot
rebuild-chroot:
	@echo "==> Rebuilding chroot stage only..."
	cd $(BUILD_DIR) && sudo lb chroot

# ── Clean targets ─────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	@echo "==> Cleaning build artefacts (keeping config and source)..."
	cd $(BUILD_DIR) && sudo lb clean --purge 2>/dev/null || true
	rm -f $(BUILD_DIR)/build.log
	@echo "==> Clean done."

.PHONY: clean-all
clean-all: clean
	@echo "==> Removing generated ISO..."
	rm -f $(ISO_PATH) $(ISO_PATH).sha256
	@echo "==> Full clean done."

# ── Info / help ───────────────────────────────────────────────────────────────

.PHONY: info
info:
	@echo "TinyOS Agent Build System"
	@echo "========================="
	@echo "  Build dir : $(BUILD_DIR)"
	@echo "  ISO path  : $(ISO_PATH)"
	@echo "  QEMU mem  : $(QEMU_MEM)"
	@echo ""
	@echo "Targets:"
	@echo "  deps              Install build prerequisites"
	@echo "  base-image        Build the Debian live ISO (main target)"
	@echo "  test-boot         Boot ISO in QEMU interactively"
	@echo "  test-boot-headless Boot ISO in QEMU, verify shell appears (CI)"
	@echo "  rebuild           Clean + base-image"
	@echo "  clean             Remove build artefacts, keep config"
	@echo "  clean-all         Remove everything including ISO"

.PHONY: help
help: info

# Guard: make sure build dir exists
$(BUILD_DIR)/lb_config:
	@if [ ! -d "$(BUILD_DIR)" ]; then \
	    echo "ERROR: $(BUILD_DIR) does not exist. Run from the repo root."; \
	    exit 1; \
	fi
