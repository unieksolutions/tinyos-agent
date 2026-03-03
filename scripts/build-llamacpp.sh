#!/usr/bin/env bash
# scripts/build-llamacpp.sh — Build llama.cpp with Vulkan backend
# ============================================================================
# Compiles llama-cli and llama-server from the pinned release tag with the
# Vulkan GPU backend enabled.  Strips the resulting binaries and installs them
# to /usr/local/bin/.
#
# Usage:
#   sudo ./scripts/build-llamacpp.sh [TAG] [INSTALL_PREFIX]
#
# Arguments (all optional):
#   TAG            — llama.cpp release tag (default: read from vendor/llama.cpp/VERSION)
#   INSTALL_PREFIX — installation prefix   (default: /usr/local)
#
# Environment variables (override defaults):
#   LLAMA_TAG        — same as TAG argument
#   INSTALL_PREFIX   — same as second argument
#   BUILD_DIR        — scratch directory for the build (default: /tmp/llama-build)
#   JOBS             — parallel make jobs (default: nproc)
#
# Requirements (must be installed on the build host):
#   build-essential cmake git libvulkan-dev vulkan-tools glslc
#
# After installation the following binaries are available:
#   /usr/local/bin/llama-cli
#   /usr/local/bin/llama-server
# ============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Resolve pinned version: argument > env > VERSION file
if [[ -n "${1:-}" ]]; then
    LLAMA_TAG="${1}"
elif [[ -n "${LLAMA_TAG:-}" ]]; then
    : # already set from environment
elif [[ -f "${REPO_ROOT}/vendor/llama.cpp/VERSION" ]]; then
    LLAMA_TAG="$(tr -d '[:space:]' < "${REPO_ROOT}/vendor/llama.cpp/VERSION")"
else
    echo "ERROR: Cannot determine llama.cpp version." >&2
    echo "       Set LLAMA_TAG env var, pass as argument, or create vendor/llama.cpp/VERSION." >&2
    exit 1
fi

INSTALL_PREFIX="${2:-${INSTALL_PREFIX:-/usr/local}}"
BUILD_DIR="${BUILD_DIR:-/tmp/llama-build}"
JOBS="${JOBS:-$(nproc)}"
LLAMA_REPO="https://github.com/ggml-org/llama.cpp"

echo "========================================================"
echo "  llama.cpp Vulkan build"
echo "========================================================"
echo "  Tag            : ${LLAMA_TAG}"
echo "  Install prefix : ${INSTALL_PREFIX}"
echo "  Build dir      : ${BUILD_DIR}"
echo "  Parallel jobs  : ${JOBS}"
echo "========================================================"

# ── Prerequisite check ────────────────────────────────────────────────────────

check_cmd() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: Required command not found: $1" >&2
        echo "       Install with: apt-get install ${2:-$1}" >&2
        exit 1
    }
}

check_cmd cmake    cmake
check_cmd git      git
check_cmd strip    binutils
check_cmd glslc    glslc   # Vulkan GLSL compiler

# Check Vulkan headers
if ! dpkg -l libvulkan-dev &>/dev/null 2>&1 && ! pkg-config --exists vulkan >/dev/null 2>&1; then
    echo "ERROR: libvulkan-dev not found. Install with: apt-get install libvulkan-dev" >&2
    exit 1
fi

# ── Clone ─────────────────────────────────────────────────────────────────────

echo ""
echo "[1/5] Cloning llama.cpp @ ${LLAMA_TAG} (shallow) ..."

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

git clone \
    --depth 1 \
    --branch "${LLAMA_TAG}" \
    "${LLAMA_REPO}" \
    "${BUILD_DIR}/src"

echo "      Cloned to ${BUILD_DIR}/src"

# ── Configure ─────────────────────────────────────────────────────────────────

echo ""
echo "[2/5] Configuring with CMake (Vulkan + Release) ..."

cmake \
    -S "${BUILD_DIR}/src" \
    -B "${BUILD_DIR}/build" \
    -DGGML_VULKAN=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=ON \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}"

echo "      CMake configuration complete."

# ── Compile ───────────────────────────────────────────────────────────────────

echo ""
echo "[3/5] Compiling llama-cli and llama-server (${JOBS} jobs) ..."

cmake \
    --build "${BUILD_DIR}/build" \
    --config Release \
    --target llama-cli llama-server \
    --parallel "${JOBS}"

echo "      Compilation complete."

# Locate built binaries (CMake may place them in different spots)
find_binary() {
    local name="$1"
    local result
    result="$(find "${BUILD_DIR}/build" -type f -name "${name}" | head -1)"
    if [[ -z "${result}" ]]; then
        echo "ERROR: Binary not found after build: ${name}" >&2
        echo "       Contents of build/bin:" >&2
        find "${BUILD_DIR}/build" -type f -executable | head -20 >&2
        exit 1
    fi
    echo "${result}"
}

BIN_CLI="$(find_binary llama-cli)"
BIN_SERVER="$(find_binary llama-server)"

echo "      llama-cli    : ${BIN_CLI}"
echo "      llama-server : ${BIN_SERVER}"

# ── Strip ─────────────────────────────────────────────────────────────────────

echo ""
echo "[4/5] Stripping binaries ..."

strip --strip-unneeded "${BIN_CLI}" "${BIN_SERVER}"

CLI_SIZE="$(du -sh "${BIN_CLI}" | cut -f1)"
SRV_SIZE="$(du -sh "${BIN_SERVER}" | cut -f1)"
echo "      llama-cli    : ${CLI_SIZE} (stripped)"
echo "      llama-server : ${SRV_SIZE} (stripped)"

# ── Install ───────────────────────────────────────────────────────────────────

echo ""
echo "[5/5] Installing to ${INSTALL_PREFIX}/bin/ ..."

install -Dm 0755 "${BIN_CLI}"    "${INSTALL_PREFIX}/bin/llama-cli"
install -Dm 0755 "${BIN_SERVER}" "${INSTALL_PREFIX}/bin/llama-server"

echo "      Installed: ${INSTALL_PREFIX}/bin/llama-cli"
echo "      Installed: ${INSTALL_PREFIX}/bin/llama-server"

# ── Cleanup ───────────────────────────────────────────────────────────────────

echo ""
echo "Cleaning up build directory ${BUILD_DIR} ..."
rm -rf "${BUILD_DIR}"

# ── Verify ────────────────────────────────────────────────────────────────────

echo ""
echo "========================================================"
echo "  Installation verified"
echo "========================================================"
"${INSTALL_PREFIX}/bin/llama-cli"    --version 2>&1 | head -2 || true
"${INSTALL_PREFIX}/bin/llama-server" --version 2>&1 | head -2 || true

echo ""
echo "Done. llama.cpp ${LLAMA_TAG} installed with Vulkan backend."
echo ""
echo "Quick test (requires a GGUF model at \$MODEL_PATH):"
echo "  GPU: llama-cli --model \$MODEL_PATH --gpu-layers 99 -p 'Hello' -n 16"
echo "  CPU: llama-cli --model \$MODEL_PATH --gpu-layers 0  -p 'Hello' -n 16"
