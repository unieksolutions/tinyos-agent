#!/bin/bash
# scripts/sync-agent.sh — Copy agent source into live-build includes.chroot
# Run this before 'make base-image' to ensure the latest agent code is in the image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET="${REPO_ROOT}/build/config/includes.chroot/opt/tinyos-agent"

echo "[sync-agent] Syncing agent source to includes.chroot..."
echo "  Source: ${REPO_ROOT}/agent/"
echo "  Target: ${TARGET}/agent/"

mkdir -p "${TARGET}/agent"

# Copy agent Python package
rsync -av --delete \
    "${REPO_ROOT}/agent/" \
    "${TARGET}/agent/"

# Copy scripts
mkdir -p "${TARGET}/scripts"
rsync -av \
    "${REPO_ROOT}/scripts/build-llamacpp.sh" \
    "${REPO_ROOT}/scripts/test-gpu-detect.sh" \
    "${TARGET}/scripts/" 2>/dev/null || true

# Ensure data dirs exist in the image
mkdir -p "${TARGET}/data" "${TARGET}/models" "${TARGET}/logs" "${TARGET}/tmp"

echo "[sync-agent] Done. Agent source is ready for live-build."
echo ""
echo "Next: cd ${REPO_ROOT} && make base-image"
