# Draft GitHub Issue: Follow Up Model Distribution And LFS Cleanup

## Title

Follow up model distribution strategy and remove broken Git LFS dependency from branch history

## Summary

This fork now defaults to the lightweight `u2netp` model and supports build-time model selection, but the repository still needs a final cleanup pass around model distribution and Git LFS history.

The current intended contract is:

- `u2netp` is the default model and should be easy to build from a plain checkout
- `u2net` remains optional and should not bloat the default artifact
- model packaging should stay explicit through `REMBG_PACKAGE_MODELS`

## Problem

We previously tried to store both `u2net` and `u2netp` through Git LFS. That created two practical problems:

1. GitHub LFS uploads were rejected for this repository, so pushes referencing those objects were blocked.
2. The default lightweight model path should not require LFS operational overhead for a ~4.4 MB file.

## Current direction

- Keep `u2netp.onnx` as a normal tracked file in the repository
- Keep `u2net.onnx` out of the repository until there is a working heavyweight distribution path
- Preserve code support for both models
- Preserve build-time model selection with `REMBG_PACKAGE_MODELS`

## Remaining work

- Audit branch history for commits that still reference unknown Git LFS objects
- Rewrite or replace those commits if GitHub continues rejecting pushes
- Decide whether `u2net.onnx` should be:
  - managed through a working Git LFS setup,
  - supplied by builders through `U2NET_HOME`, or
  - distributed through a separate heavyweight artifact
- Add a fresh-clone smoke test that verifies a consumer can build `REMBG_PACKAGE_MODELS=u2netp` without extra LFS steps
- Add benchmark and image-quality verification for the final published distribution

## Acceptance criteria

- A fresh clone can build and use `u2netp` without Git LFS setup
- `REMBG_PACKAGE_MODELS=u2netp` packages only the light model
- `REMBG_PACKAGE_MODELS=u2net` only works when the heavy model is intentionally supplied
- GitHub pushes succeed without unknown LFS object errors

## Notes

- We already verified locally that a wheel containing the real `u2netp` model can be built and used successfully.
- The remaining blocker is publication/distribution hygiene, not core inference functionality.
