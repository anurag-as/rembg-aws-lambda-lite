import os
from pathlib import Path
from typing import Final


PACKAGE_MODELS_ENV: Final = "REMBG_PACKAGE_MODELS"
DEFAULT_PACKAGE_MODELS: Final = "u2netp"
MODEL_VARIANTS: Final = {
    "none": (),
    "u2net": ("u2net.onnx",),
    "u2netp": ("u2netp.onnx",),
    "both": ("u2net.onnx", "u2netp.onnx"),
}
LFS_POINTER_PREFIX: Final = "version https://git-lfs.github.com/spec/v1"


def get_selected_model_variant() -> str:
    variant = os.environ.get(PACKAGE_MODELS_ENV, DEFAULT_PACKAGE_MODELS).strip().lower()
    if variant not in MODEL_VARIANTS:
        supported = ", ".join(sorted(MODEL_VARIANTS))
        raise ValueError(
            f"unsupported {PACKAGE_MODELS_ENV} value: {variant!r}. "
            f"expected one of: {supported}"
        )

    return variant


def get_packaged_model_files() -> list[str]:
    return list(MODEL_VARIANTS[get_selected_model_variant()])


def is_lfs_pointer_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        first_line = handle.readline().strip()

    return first_line == LFS_POINTER_PREFIX


def validate_packaged_model_files(repo_root: Path) -> None:
    for model_name in get_packaged_model_files():
        full_path = repo_root / "rembg" / model_name
        if not full_path.exists():
            raise FileNotFoundError(
                f"requested packaged model is missing: {full_path}. "
                f"Set {PACKAGE_MODELS_ENV}=none to build without bundled models."
            )
        if is_lfs_pointer_file(full_path):
            raise FileNotFoundError(
                f"requested packaged model is still a Git LFS pointer: {full_path}. "
                f"Fetch the real LFS object before building, or set "
                f"{PACKAGE_MODELS_ENV}=none to build without bundled models."
            )
