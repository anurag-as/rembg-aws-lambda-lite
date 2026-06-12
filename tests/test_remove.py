from io import BytesIO
from pathlib import Path

import onnxruntime as ort
import pytest
from PIL import Image

from build_config import (
    DEFAULT_PACKAGE_MODELS,
    LFS_POINTER_PREFIX,
    PACKAGE_MODELS_ENV,
    get_packaged_model_files,
    get_selected_model_variant,
    is_lfs_pointer_file,
    validate_packaged_model_files,
)
from rembg import new_session, remove
from rembg.session_factory import PROVIDERS_ENV, SUPPORTED_MODELS, _resolve_providers


class DummyOrtSession:
    def __init__(self, model_path: str, providers, sess_options):
        self.model_path = model_path
        self.providers = providers
        self.sess_options = sess_options

    def get_inputs(self):
        return []


class FakeMaskSession:
    def predict(self, img: Image.Image):
        return [Image.new("L", img.size, color=255)]


@pytest.fixture
def sample_image() -> Image.Image:
    return Image.new("RGB", (8, 6), color=(10, 20, 30))


def test_build_selector_defaults_to_u2netp(monkeypatch):
    monkeypatch.delenv(PACKAGE_MODELS_ENV, raising=False)

    assert get_selected_model_variant() == DEFAULT_PACKAGE_MODELS
    assert get_packaged_model_files() == ["u2netp.onnx"]


def test_build_selector_supports_single_or_both_variants(monkeypatch):
    monkeypatch.setenv(PACKAGE_MODELS_ENV, "u2net")
    assert get_packaged_model_files() == ["u2net.onnx"]

    monkeypatch.setenv(PACKAGE_MODELS_ENV, "both")
    assert get_packaged_model_files() == ["u2net.onnx", "u2netp.onnx"]

    monkeypatch.setenv(PACKAGE_MODELS_ENV, "none")
    assert get_packaged_model_files() == []


def test_build_selector_rejects_unknown_variant(monkeypatch):
    monkeypatch.setenv(PACKAGE_MODELS_ENV, "all")

    with pytest.raises(ValueError, match=PACKAGE_MODELS_ENV):
        get_selected_model_variant()


def test_build_selector_validates_requested_files(monkeypatch, tmp_path):
    repo_root = tmp_path
    (repo_root / "rembg").mkdir()

    monkeypatch.setenv(PACKAGE_MODELS_ENV, "none")
    validate_packaged_model_files(repo_root)

    monkeypatch.setenv(PACKAGE_MODELS_ENV, "u2netp")
    with pytest.raises(FileNotFoundError, match="u2netp.onnx"):
        validate_packaged_model_files(repo_root)

    (repo_root / "rembg" / "u2netp.onnx").write_bytes(b"fake-model")
    validate_packaged_model_files(repo_root)


def test_build_selector_rejects_lfs_pointer_files(monkeypatch, tmp_path):
    repo_root = tmp_path
    model_dir = repo_root / "rembg"
    model_dir.mkdir()
    pointer_path = model_dir / "u2netp.onnx"
    pointer_path.write_text(
        "\n".join(
            [
                LFS_POINTER_PREFIX,
                "oid sha256:deadbeef",
                "size 123",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert is_lfs_pointer_file(pointer_path) is True

    monkeypatch.setenv(PACKAGE_MODELS_ENV, "u2netp")
    with pytest.raises(FileNotFoundError, match="Git LFS pointer"):
        validate_packaged_model_files(repo_root)


def test_new_session_defaults_to_u2netp(monkeypatch, tmp_path):
    model_path = tmp_path / "u2netp.onnx"
    model_path.write_bytes(b"fake-model")

    monkeypatch.setenv("U2NET_HOME", str(tmp_path))
    monkeypatch.setattr(ort, "get_available_providers", lambda: ["CPUExecutionProvider"])
    monkeypatch.setattr(ort, "InferenceSession", DummyOrtSession)

    session = new_session()

    assert session.model_name == "u2netp"
    assert session.inner_session.model_path == str(model_path)
    assert SUPPORTED_MODELS == frozenset({"u2net", "u2netp"})


def test_new_session_supports_u2net_when_model_file_exists(monkeypatch, tmp_path):
    model_path = tmp_path / "u2net.onnx"
    model_path.write_bytes(b"fake-model")

    monkeypatch.setenv("U2NET_HOME", str(tmp_path))
    monkeypatch.setattr(ort, "get_available_providers", lambda: ["CPUExecutionProvider"])
    monkeypatch.setattr(ort, "InferenceSession", DummyOrtSession)

    session = new_session("u2net")

    assert session.model_name == "u2net"
    assert session.inner_session.model_path == str(model_path)


def test_session_factory_defaults_to_cpu_provider(monkeypatch):
    monkeypatch.delenv(PROVIDERS_ENV, raising=False)
    monkeypatch.setattr(
        ort,
        "get_available_providers",
        lambda: ["CoreMLExecutionProvider", "CPUExecutionProvider"],
    )

    assert _resolve_providers() == ["CPUExecutionProvider"]


def test_session_factory_respects_configured_providers(monkeypatch):
    monkeypatch.setenv(PROVIDERS_ENV, "CPUExecutionProvider")
    monkeypatch.setattr(
        ort,
        "get_available_providers",
        lambda: ["CoreMLExecutionProvider", "CPUExecutionProvider"],
    )

    assert _resolve_providers() == ["CPUExecutionProvider"]


def test_session_factory_rejects_unknown_configured_providers(monkeypatch):
    monkeypatch.setenv(PROVIDERS_ENV, "CudaExecutionProvider")
    monkeypatch.setattr(ort, "get_available_providers", lambda: ["CPUExecutionProvider"])

    with pytest.raises(ValueError, match=PROVIDERS_ENV):
        _resolve_providers()


def test_new_session_rejects_unknown_model():
    with pytest.raises(NotImplementedError, match="unsupported model: silueta"):
        new_session("silueta")


def test_new_session_requires_bundled_or_mounted_model(monkeypatch, tmp_path):
    monkeypatch.setenv("U2NET_HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="u2netp.onnx"):
        new_session("u2netp")


def test_new_session_requires_requested_model_file(monkeypatch, tmp_path):
    monkeypatch.setenv("U2NET_HOME", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="u2net.onnx"):
        new_session("u2net")


def test_remove_with_pil_session_returns_image(sample_image):
    output = remove(sample_image, session=FakeMaskSession())

    assert isinstance(output, Image.Image)
    assert output.mode == "RGBA"
    assert output.size == sample_image.size


def test_remove_only_mask_returns_grayscale_image(sample_image):
    output = remove(sample_image, session=FakeMaskSession(), only_mask=True)

    assert isinstance(output, Image.Image)
    assert output.mode == "L"
    assert output.size == sample_image.size


def test_remove_bytes_returns_png_bytes(sample_image):
    input_buffer = BytesIO()
    sample_image.save(input_buffer, format="PNG")

    output = remove(input_buffer.getvalue(), session=FakeMaskSession())

    assert isinstance(output, bytes)
    assert output.startswith(b"\x89PNG")


def test_default_model_is_not_an_lfs_pointer():
    repo_root = Path(__file__).resolve().parent.parent

    assert is_lfs_pointer_file(repo_root / "rembg" / "u2netp.onnx") is False
