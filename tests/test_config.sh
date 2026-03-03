#!/bin/bash
# tests/test_config.sh — Static analysis test suite for TinyOS Agent live-build config
#
# Runs without root, without live-build installed.
# Tests: file presence, syntax, lb_config parameters, package list, security, hooks.
#
# Exit codes: 0 = all tests passed, 1 = one or more tests failed
#
# Usage:
#   bash tests/test_config.sh
#   bash tests/test_config.sh 2>&1 | tee /tmp/test_results.log

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
HOOKS_CHROOT="${BUILD_DIR}/config/hooks/chroot"
HOOKS_LIVE="${BUILD_DIR}/config/hooks/live"
PKG_LIST="${BUILD_DIR}/config/package-lists/tinyos.list.chroot"
LB_CONFIG="${BUILD_DIR}/lb_config"
MAKEFILE="${REPO_ROOT}/Makefile"

PASS=0
FAIL=0
SKIP=0

_pass() { echo "  PASS: $1"; ((PASS++)); }
_fail() { echo "  FAIL: $1"; ((FAIL++)); }
_skip() { echo "  SKIP: $1 (reason: $2)"; ((SKIP++)); }

group() { echo ""; echo "── $1 ──────────────────────────────────────────────────────────"; }

# ── Group 1: File presence ────────────────────────────────────────────────────
group "1. Required file presence"

check_file() {
    local path="$1"
    local label="${2:-$path}"
    if [[ -f "$path" ]]; then _pass "$label exists"; else _fail "$label MISSING: $path"; fi
}

check_file "${LB_CONFIG}"                                          "build/lb_config"
check_file "${BUILD_DIR}/config/package-lists/tinyos.list.chroot" "package list"
check_file "${HOOKS_CHROOT}/0010-locale.hook.chroot"              "chroot hook 0010-locale"
check_file "${HOOKS_CHROOT}/0020-kernel-modules.hook.chroot"      "chroot hook 0020-kernel-modules"
check_file "${HOOKS_CHROOT}/0030-agent-user.hook.chroot"          "chroot hook 0030-agent-user"
check_file "${HOOKS_CHROOT}/0040-autologin.hook.chroot"           "chroot hook 0040-autologin"
check_file "${HOOKS_CHROOT}/0050-cleanup.hook.chroot"             "chroot hook 0050-cleanup"
check_file "${HOOKS_LIVE}/0010-first-boot.hook.live"              "live hook 0010-first-boot"
check_file "${MAKEFILE}"                                           "Makefile"
check_file "${REPO_ROOT}/README.md"                               "README.md"

# ── Group 2: Shell script syntax validation ───────────────────────────────────
group "2. Shell script syntax (bash -n)"

for script in "${LB_CONFIG}" \
              "${HOOKS_CHROOT}"/*.hook.chroot \
              "${HOOKS_LIVE}"/*.hook.live; do
    label="$(basename "$script")"
    if bash -n "$script" 2>/dev/null; then
        _pass "${label}: syntax OK"
    else
        _fail "${label}: SYNTAX ERROR"
        bash -n "$script" 2>&1 | sed 's/^/    /'
    fi
done

# ── Group 3: lb_config parameter correctness ─────────────────────────────────
group "3. lb_config parameter values"

lb_has() {
    local param="$1"
    local val="$2"
    if grep -q "${val}" "${LB_CONFIG}"; then
        _pass "lb_config: ${param} = ${val}"
    else
        _fail "lb_config: ${param} = ${val} NOT FOUND"
    fi
}

lb_has "--distribution"           "bookworm"
lb_has "--architecture"           "amd64"
lb_has "--binary-images"          "iso-hybrid"
lb_has "--bootloaders"            "grub-efi"
lb_has "--linux-flavours"         "amd64"
lb_has "--linux-packages"         "linux-image-amd64"
lb_has "--archive-areas"          "non-free"
lb_has "--hostname"               "tinyos"
lb_has "--username"               "agent"
lb_has "--apt-recommends"         "false"
lb_has "--checksums"              "sha256"
lb_has "--bootappend-live"        "username=agent"

# ── Group 4: Mirror transport security (HTTPS) ────────────────────────────────
group "4. Mirror URLs use HTTPS"

for mirror_param in "--mirror-bootstrap" "--mirror-chroot" "--mirror-chroot-security" \
                    "--mirror-binary" "--mirror-binary-security"; do
    # Use -F for fixed-string and -- to prevent leading -- being parsed as grep options
    line=$(grep -F -- "${mirror_param}" "${LB_CONFIG}" 2>/dev/null || true)
    if echo "$line" | grep -q "https://"; then
        _pass "${mirror_param} uses HTTPS"
    elif [[ -z "$line" ]]; then
        _skip "${mirror_param}" "not set in lb_config, using lb defaults"
    else
        _fail "${mirror_param} does NOT use HTTPS: $line"
    fi
done

# ── Group 5: Package list — required packages ─────────────────────────────────
group "5. Package list — required packages"

pkg_present() {
    local pkg="$1"
    # Strip comment lines, then grep for exact package name
    if grep -v '^#' "${PKG_LIST}" | grep -qxF "${pkg}"; then
        _pass "package: ${pkg}"
    else
        _fail "package: ${pkg} MISSING from tinyos.list.chroot"
    fi
}

pkg_present python3
pkg_present python3-pip
pkg_present systemd
pkg_present sqlite3
pkg_present libvulkan1
pkg_present vulkan-tools
pkg_present mesa-vulkan-drivers
pkg_present firmware-linux
pkg_present firmware-linux-nonfree
pkg_present firmware-amd-graphics
pkg_present firmware-nvidia-graphics
pkg_present live-boot
pkg_present live-config
pkg_present openssh-server

# ── Group 6: Security checks ──────────────────────────────────────────────────
group "6. Security checks"

# No hardcoded secrets / passwords
if grep -rqi 'password\s*=\s*[^$]' "${BUILD_DIR}" 2>/dev/null; then
    _fail "Possible hardcoded passwords found"
else
    _pass "No hardcoded passwords found"
fi

# No eval with untrusted input patterns
if grep -rqP 'eval\s+\$\{?\w*INPUT' "${BUILD_DIR}" 2>/dev/null; then
    _fail "Dangerous eval with input variable found"
else
    _pass "No dangerous eval patterns found"
fi

# No wget/curl piped to shell
if grep -rqP 'curl.*\|\s*(ba)?sh|wget.*\|\s*(ba)?sh' "${BUILD_DIR}" 2>/dev/null; then
    _fail "curl/wget piped to shell found (untrusted remote execution)"
else
    _pass "No curl/wget piped to shell"
fi

# sudoers file should NOT have bare NOPASSWD: ALL anymore
if grep -q 'NOPASSWD: ALL' "${HOOKS_CHROOT}/0030-agent-user.hook.chroot"; then
    # Check it's wrapped in a Cmnd_Alias, not a bare "agent ALL=(ALL) NOPASSWD: ALL"
    if grep -qP '^agent\s+ALL=\(ALL\)\s+NOPASSWD:\s+ALL' "${HOOKS_CHROOT}/0030-agent-user.hook.chroot"; then
        _fail "sudoers: bare 'agent ALL=(ALL) NOPASSWD: ALL' found (over-privileged)"
    else
        _pass "sudoers: NOPASSWD is scoped via Cmnd_Alias (not bare ALL)"
    fi
else
    _pass "sudoers: no bare NOPASSWD: ALL"
fi

# OVMF path is not hardcoded in Makefile (should use auto-detection variable)
if grep -q 'bios.*OVMF_FW' "${MAKEFILE}"; then
    _pass "Makefile: OVMF path uses auto-detected OVMF_FW variable"
else
    _fail "Makefile: OVMF path may be hardcoded"
fi

# Dead QEMU_DISK_SIZE variable should not be present
if grep -q 'QEMU_DISK_SIZE' "${MAKEFILE}"; then
    _fail "Makefile: dead QEMU_DISK_SIZE variable still present"
else
    _pass "Makefile: no dead QEMU_DISK_SIZE variable"
fi

# ── Group 7: Hook ordering ────────────────────────────────────────────────────
group "7. Hook file naming and ordering"

expected_chroot_order=(
    "0010-locale.hook.chroot"
    "0020-kernel-modules.hook.chroot"
    "0030-agent-user.hook.chroot"
    "0040-autologin.hook.chroot"
    "0050-cleanup.hook.chroot"
)

for hook in "${expected_chroot_order[@]}"; do
    if [[ -f "${HOOKS_CHROOT}/${hook}" ]]; then
        _pass "chroot hook in order: ${hook}"
    else
        _fail "chroot hook missing: ${hook}"
    fi
done

# Verify hooks are executable (or have shebang — live-build requires executable hooks)
for hook_file in "${HOOKS_CHROOT}"/*.hook.chroot "${HOOKS_LIVE}"/*.hook.live; do
    label="$(basename "$hook_file")"
    if head -1 "$hook_file" | grep -q '^#!'; then
        _pass "${label}: has shebang"
    else
        _fail "${label}: missing shebang (#!/bin/bash)"
    fi
done

# Cleanup hook should run last (highest number)
last_hook=$(ls "${HOOKS_CHROOT}"/*.hook.chroot 2>/dev/null | sort | tail -1 | xargs basename)
if [[ "${last_hook}" == 0050-cleanup* ]]; then
    _pass "cleanup hook runs last (${last_hook})"
else
    _fail "cleanup hook is NOT last: ${last_hook}"
fi

# ── Group 8: Makefile targets ─────────────────────────────────────────────────
group "8. Makefile targets and variables"

targets_present() {
    local target="$1"
    if grep -q "^.PHONY:.*${target}\|^${target}:" "${MAKEFILE}"; then
        _pass "Makefile: target '${target}' exists"
    else
        _fail "Makefile: target '${target}' MISSING"
    fi
}

targets_present deps
targets_present base-image
targets_present test-boot
targets_present test-boot-headless
targets_present clean
targets_present clean-all
targets_present info

# Makefile: dry-run should not error
if make -n base-image -C "${REPO_ROOT}" >/dev/null 2>&1; then
    _pass "Makefile: dry-run succeeds"
else
    _fail "Makefile: dry-run failed"
fi

# ── Group 9: QEMU infrastructure readiness ────────────────────────────────────
group "9. QEMU infrastructure readiness"

if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    _pass "qemu-system-x86_64 is installed"
    qemu_ver=$(qemu-system-x86_64 --version 2>&1 | head -1)
    _pass "QEMU version: ${qemu_ver}"
else
    _skip "qemu-system-x86_64" "not installed — run: sudo apt-get install qemu-system-x86"
fi

# Check KVM availability
if [[ -e /dev/kvm ]]; then
    _pass "/dev/kvm exists (hardware acceleration available)"
else
    _skip "/dev/kvm" "KVM not available — QEMU will run in software emulation"
fi

# OVMF firmware detection
ovmf_candidates=(
    /usr/share/ovmf/OVMF.fd
    /usr/share/OVMF/OVMF_CODE.fd
    /usr/share/qemu/OVMF.fd
    /usr/share/edk2-ovmf/x64/OVMF.fd
)
ovmf_found=""
for candidate in "${ovmf_candidates[@]}"; do
    if [[ -f "$candidate" ]]; then
        ovmf_found="$candidate"
        break
    fi
done
if [[ -n "$ovmf_found" ]]; then
    _pass "OVMF firmware found: ${ovmf_found}"
else
    _skip "OVMF firmware" "not found — run: sudo apt-get install ovmf"
fi

# live-build check
if command -v lb >/dev/null 2>&1; then
    lb_ver=$(lb --version 2>&1 | head -1)
    _pass "live-build installed: ${lb_ver}"
else
    _skip "live-build" "not installed — run: sudo apt-get install live-build (requires Debian/Ubuntu host)"
fi

# debootstrap check
if command -v debootstrap >/dev/null 2>&1; then
    _pass "debootstrap installed"
else
    _skip "debootstrap" "not installed — run: sudo apt-get install debootstrap"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Results: ${PASS} passed, ${FAIL} failed, ${SKIP} skipped"
echo "══════════════════════════════════════════════════════════"

if [[ $FAIL -gt 0 ]]; then
    echo "  STATUS: FAIL (${FAIL} test(s) failed)"
    exit 1
else
    echo "  STATUS: PASS"
    exit 0
fi
