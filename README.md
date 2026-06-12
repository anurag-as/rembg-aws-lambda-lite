# rembg-aws-lambda

Minimal `rembg` fork for Lambda-style CPU inference.

This repository is a modified fork of [`rnag/rembg-aws-lambda`](https://github.com/rnag/rembg-aws-lambda). It keeps the original MIT license and copyright notices, but narrows the package to the lightweight `u2netp` model path used by the Visa Photo App whitening container.

## Why this fork exists

This fork is not universally better than [`rnag/rembg-aws-lambda`](https://github.com/rnag/rembg-aws-lambda). It is better for a narrower use case: CPU-only AWS Lambda deployments that want explicit model packaging, lighter default artifacts, and current Python support.

Compared with the upstream fork, this repository adds:

- `u2netp` as the default model instead of `u2net`
- build-time model packaging selection through `REMBG_PACKAGE_MODELS`
- explicit failure when a selected model file is missing or still only a Git LFS pointer
- support for both `u2net` and `u2netp` in code, while keeping `u2netp` as the default packaging target
- a normal tracked default light-model asset, instead of forcing Git LFS for the lightweight path
- Python support through `3.12`
- CPU-first ONNX Runtime provider selection, which fits Lambda inference better than taking every available local provider

Compared with the upstream README and packaging behavior, this fork also documents an important operational constraint more honestly: model selection at runtime and model packaging at build time are separate concerns.

## What changed

- `new_session()` now defaults to `u2netp`.
- `new_session("u2net")` and `new_session("u2netp")` are both supported in code.
- The default build target packages only `u2netp`, not `u2net`.
- Python support is updated for Python through `3.12`.
- The package no longer relies on runtime model downloads.

## Supported runtime

- CPU only
- AWS Lambda base images such as `public.ecr.aws/lambda/python:3.12`
- Local development on Python through `3.12`

## Installation

```bash
pip install rembg-aws-lambda
```

This fork expects the requested model file to be present either:

- inside the installed `rembg` package as `rembg/u2netp.onnx` or `rembg/u2net.onnx`, or
- in the directory pointed to by `U2NET_HOME`

If the requested model file is missing, `new_session()` raises `FileNotFoundError` immediately.

## Build-time model selection

Bundled model selection is controlled at build time with `REMBG_PACKAGE_MODELS`.

Supported values:

- `u2netp` - default, bundles only `u2netp.onnx`
- `u2net` - bundles only `u2net.onnx`
- `both` - bundles both model files
- `none` - bundles no model file; use this only if you will mount models through `U2NET_HOME`

Examples:

```bash
REMBG_PACKAGE_MODELS=u2netp python -m build
REMBG_PACKAGE_MODELS=u2net python -m build
REMBG_PACKAGE_MODELS=both python -m build
REMBG_PACKAGE_MODELS=none python -m build
```

Docker example:

```dockerfile
ARG REMBG_PACKAGE_MODELS=u2netp
ENV REMBG_PACKAGE_MODELS=${REMBG_PACKAGE_MODELS}

RUN python -m pip install --no-cache-dir . --target "${LAMBDA_TASK_ROOT}"
```

Important:

- Runtime model selection does not change packaged contents.
- If you request `u2net` or `u2netp` at build time and the corresponding `.onnx` file is missing, the build fails immediately.
- `u2netp.onnx` is tracked directly in the repository so the default light-model build works from a plain checkout.
- `u2net.onnx` is still a heavyweight optional path. If you select it and the file is only a Git LFS pointer in your checkout, the build fails until you fetch the real object.
- If you care about Lambda cold starts, do not build with `both` unless you actually need a single artifact to contain both models.

## Library usage

```python
from rembg import new_session, remove

session = new_session()
cutout = remove(input_image, session=session)
```

Explicit model selection:

```python
from rembg import new_session

session = new_session("u2netp")
```

If you need the larger model and have supplied the file:

```python
from rembg import new_session

session = new_session("u2net")
```

Supported input types:

- `bytes`
- `PIL.Image.Image`
- `numpy.ndarray`

Supported output behavior:

- `remove(...)` returns bytes for byte input
- `remove(...)` returns a `PIL.Image.Image` for PIL input
- `remove(...)` returns a `numpy.ndarray` for ndarray input
- `remove(..., only_mask=True)` returns the predicted mask

## Provider selection

This fork is intended for CPU-only Lambda use. By default it prefers `CPUExecutionProvider` when ONNX Runtime exposes multiple providers.

If you need to override that behavior, set `REMBG_ONNX_PROVIDERS` to a comma-separated list of ONNX Runtime provider names:

```bash
REMBG_ONNX_PROVIDERS=CPUExecutionProvider python your_script.py
```

## Docker smoke test

```dockerfile
FROM public.ecr.aws/lambda/python:3.10

ENV OMP_NUM_THREADS=1
ENV REMBG_PACKAGE_MODELS=u2netp

RUN python -m pip install --no-cache-dir rembg-aws-lambda --target "${LAMBDA_TASK_ROOT}" \
    && python -c "from rembg import new_session; new_session('u2netp')"
```

The default `u2netp` smoke test works from a plain checkout because the light model is stored directly in the repository. A `u2net` or `both` build still requires the heavyweight model object to be present locally.

## Development notes

- `u2netp.onnx` is committed as a normal repository file so the default light-model path is easy to clone and build.
- `u2net.onnx` remains optional and heavyweight; it should only be supplied intentionally.
- The default build selection is `u2netp`; `u2net` is only packaged when explicitly selected.
- Code support for `u2net` remains available when the file is mounted or included in a custom build.

## References

- Original upstream fork: https://github.com/rnag/rembg-aws-lambda
- Original `rembg`: https://github.com/danielgatis/rembg
- U-2-Net paper: https://arxiv.org/abs/2005.09007
- U-2-Net repository: https://github.com/xuebinqin/U-2-Net

## License

Licensed under the [MIT License](./LICENSE.txt).
