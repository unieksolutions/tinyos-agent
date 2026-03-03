# vendor/llama.cpp

This directory pins the llama.cpp version used in the TinyOS Agent image.

## Pinned Version

See `VERSION` file for the pinned release tag (currently `b8185`, released 2026-03-02).

## Source

- Repository: https://github.com/ggml-org/llama.cpp
- Release page: https://github.com/ggml-org/llama.cpp/releases/tag/b8185

## Why not a git submodule?

The llama.cpp repo is large (~1 GB with history). Rather than embedding it as a
submodule, the live-build hook (`build/config/hooks/10-llamacpp.hook.chroot`) performs
a **shallow clone** (`--depth 1`) of the pinned tag at image-build time inside the
chroot. This keeps the TinyOS Agent repo lean while guaranteeing a reproducible build.

## Updating the pinned version

1. Edit `vendor/llama.cpp/VERSION` to the new tag (e.g. `b8500`).
2. Update `build/config/hooks/10-llamacpp.hook.chroot` — the hook reads this version
   variable at the top of the script.
3. Re-run `make base-image` and execute `scripts/test-gpu-detect.sh` inside QEMU
   to confirm GPU auto-detection still works.

## Build flags used

```
cmake -DGGML_VULKAN=ON \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_TESTS=OFF \
      -DLLAMA_BUILD_EXAMPLES=ON
```

Vulkan is the portable GPU compute backend that works on both AMD (RDNA via Mesa) and
NVIDIA (via open/proprietary Vulkan drivers) without requiring vendor-specific SDKs
(ROCm, CUDA) at build time.
