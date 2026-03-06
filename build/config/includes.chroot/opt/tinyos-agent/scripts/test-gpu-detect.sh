#!/usr/bin/env bash
# scripts/test-gpu-detect.sh — Verify llama.cpp Vulkan GPU auto-detection
# ============================================================================
# Downloads a tiny GGUF model (tinyllama Q2_K, ~250 MB) if not already cached
# and runs two tests:
#
#   Test 1 — GPU mode  (--gpu-layers 1):
#     Checks llama-cli output for Vulkan device detection strings.
#     Passes if Vulkan device is enumerated; warns but does NOT fail if no GPU
#     is available (pure-CPU host is valid in CI).
#
#   Test 2 — CPU fallback (--gpu-layers 0):
#     Confirms llama-cli can infer entirely on CPU.  Must succeed on all hosts.
#
# Exit codes:
#   0 — All mandatory tests passed (CPU test always mandatory; GPU advisory)
#   1 — A mandatory test failed
#
# Usage:
#   ./scripts/test-gpu-detect.sh [MODEL_PATH]
#
# Arguments:
#   MODEL_PATH — path to an existing .gguf model file (optional).
#                If omitted the script downloads tinyllama Q2_K (~250 MB).
#
# Environment variables:
#   MODEL_PATH   — same as argument
#   MODEL_CACHE  — directory for downloaded models (default: /tmp/llama-models)
#   LLAMA_CLI    — path to llama-cli binary       (default: auto-detect)
#   GPU_LAYERS   — number of layers to offload for GPU test (default: 1)
#   TIMEOUT      — seconds per test run            (default: 60)
# ============================================================================

set -uo pipefail   # no -e: we handle exit codes manually

# ── Configuration ─────────────────────────────────────────────────────────────

MODEL_CACHE="${MODEL_CACHE:-/tmp/llama-models}"
GPU_LAYERS="${GPU_LAYERS:-1}"
TIMEOUT="${TIMEOUT:-60}"
PREDICT_TOKENS=4    # just enough to confirm inference works; keep test fast

# Default tiny model: TinyLlama 1.1B Q2_K (~250 MB) from Hugging Face
MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q2_K.gguf"
MODEL_FILE="tinyllama-1.1b-chat-v1.0.Q2_K.gguf"

# ── Helpers ───────────────────────────────────────────────────────────────────

PASS=0
FAIL=0
WARN=0

log()  { echo "[test-gpu-detect] $*"; }
pass() { echo "[PASS] $*"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $*" >&2; FAIL=$((FAIL+1)); }
warn() { echo "[WARN] $*"; WARN=$((WARN+1)); }

# ── Locate llama-cli ──────────────────────────────────────────────────────────

if [[ -n "${LLAMA_CLI:-}" ]]; then
    : # user override
elif command -v llama-cli &>/dev/null; then
    LLAMA_CLI="$(command -v llama-cli)"
elif [[ -x /usr/local/bin/llama-cli ]]; then
    LLAMA_CLI=/usr/local/bin/llama-cli
else
    fail "llama-cli not found in PATH or /usr/local/bin"
    echo ""
    echo "Install llama.cpp first:"
    echo "  sudo ./scripts/build-llamacpp.sh"
    exit 1
fi

log "Using binary: ${LLAMA_CLI}"
log "Version: $("${LLAMA_CLI}" --version 2>&1 | head -1 || echo '(unknown)')"

# ── Resolve model path ────────────────────────────────────────────────────────

if [[ -n "${1:-}" ]]; then
    MODEL_PATH="$1"
elif [[ -n "${MODEL_PATH:-}" ]]; then
    : # env var
else
    MODEL_PATH="${MODEL_CACHE}/${MODEL_FILE}"
fi

if [[ ! -f "${MODEL_PATH}" ]]; then
    log "Model not found at ${MODEL_PATH}."

    if ! command -v wget &>/dev/null && ! command -v curl &>/dev/null; then
        fail "No model file and neither wget nor curl is available. Provide MODEL_PATH."
        exit 1
    fi

    log "Downloading ${MODEL_FILE} (~250 MB) ..."
    mkdir -p "${MODEL_CACHE}"

    if command -v wget &>/dev/null; then
        wget -q --show-progress -O "${MODEL_PATH}" "${MODEL_URL}"
    else
        curl -L --progress-bar -o "${MODEL_PATH}" "${MODEL_URL}"
    fi

    if [[ ! -f "${MODEL_PATH}" ]]; then
        fail "Download failed: ${MODEL_PATH} not created."
        exit 1
    fi
    log "Downloaded to ${MODEL_PATH}."
fi

log "Model: ${MODEL_PATH} ($(du -sh "${MODEL_PATH}" | cut -f1))"

# ── Common llama-cli arguments ────────────────────────────────────────────────

COMMON_ARGS=(
    --model   "${MODEL_PATH}"
    --prompt  "Once"
    --n-predict "${PREDICT_TOKENS}"
    --ctx-size  128
    --log-disable          # reduce noise; we parse stderr for Vulkan strings
    --no-display-prompt    # cleaner output
)

# ── Test 1: GPU mode — Vulkan device detection ────────────────────────────────

echo ""
echo "================================================================"
echo "  Test 1: GPU mode (--gpu-layers ${GPU_LAYERS})"
echo "================================================================"

GPU_LOG="$(mktemp)"
GPU_EXIT=0

# Run with stderr captured; llama.cpp prints Vulkan info to stderr
timeout "${TIMEOUT}" "${LLAMA_CLI}" \
    "${COMMON_ARGS[@]}" \
    --gpu-layers "${GPU_LAYERS}" \
    2>"${GPU_LOG}" 1>/dev/null || GPU_EXIT=$?

log "Exit code: ${GPU_EXIT}"
log "--- stderr ---"
cat "${GPU_LOG}"
log "--- end ---"

# Check for Vulkan device detection in output
# llama.cpp prints lines like:
#   ggml_vulkan: Found 1 Vulkan device(s):
#   ggml_vulkan: Using Vulkan device: AMD Radeon RX 7900 XTX
#   ggml_vulkan: Using Vulkan device: NVIDIA GeForce RTX 4090
if grep -qiE 'vulkan.*(device|found|using)' "${GPU_LOG}"; then
    pass "Vulkan device detection: GPU enumerated successfully"
    grep -iE 'vulkan.*(device|found|using)' "${GPU_LOG}" | while read -r line; do
        log "  => ${line}"
    done
elif grep -qi 'no vulkan\|vulkan.*not\|no gpu\|using cpu' "${GPU_LOG}"; then
    warn "No Vulkan-capable GPU found on this host — CPU fallback active"
    warn "This is expected in headless CI without GPU passthrough."
    warn "Re-run inside QEMU with Vulkan passthrough to verify GPU detection."
else
    # llama completed but no Vulkan strings — possibly fallback silently
    if [[ ${GPU_EXIT} -eq 0 ]]; then
        warn "llama-cli exited 0 but no Vulkan detection strings found."
        warn "May be running in CPU-only mode. Check log above."
    else
        fail "llama-cli exited ${GPU_EXIT} in GPU mode. Check log above."
    fi
fi

rm -f "${GPU_LOG}"

# ── Test 2: CPU fallback ──────────────────────────────────────────────────────

echo ""
echo "================================================================"
echo "  Test 2: CPU fallback (--gpu-layers 0)"
echo "================================================================"

CPU_LOG="$(mktemp)"
CPU_EXIT=0

timeout "${TIMEOUT}" "${LLAMA_CLI}" \
    "${COMMON_ARGS[@]}" \
    --gpu-layers 0 \
    2>"${CPU_LOG}" 1>/dev/null || CPU_EXIT=$?

log "Exit code: ${CPU_EXIT}"

if [[ ${CPU_EXIT} -eq 0 ]]; then
    pass "CPU fallback: llama-cli completed inference on CPU (exit 0)"
else
    fail "CPU fallback: llama-cli exited ${CPU_EXIT}"
    cat "${CPU_LOG}" >&2
fi

rm -f "${CPU_LOG}"

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "================================================================"
echo "  Results"
echo "================================================================"
echo "  Passed  : ${PASS}"
echo "  Warnings: ${WARN}"
echo "  Failed  : ${FAIL}"
echo "================================================================"

if [[ ${FAIL} -gt 0 ]]; then
    echo "STATUS: FAIL — ${FAIL} mandatory test(s) failed."
    exit 1
elif [[ ${WARN} -gt 0 ]]; then
    echo "STATUS: PASS (with warnings) — GPU not detected on this host."
    echo "        Re-run inside QEMU with Vulkan passthrough for full GPU test."
    exit 0
else
    echo "STATUS: PASS — All tests passed, Vulkan GPU detected."
    exit 0
fi
