import os
from pathlib import Path
from typing import Final, Type

import onnxruntime as ort

from .session_base import BaseSession
from .session_simple import SimpleSession

script_dir = Path(__file__).parent
DEFAULT_MODEL: Final = "u2netp"
SUPPORTED_MODELS: Final = frozenset({"u2net", "u2netp"})
PROVIDERS_ENV: Final = "REMBG_ONNX_PROVIDERS"


def _resolve_model_path(model_name: str) -> Path:
    if "U2NET_HOME" in os.environ:
        return Path(os.environ["U2NET_HOME"]).expanduser() / f"{model_name}.onnx"

    return script_dir / f"{model_name}.onnx"


def _resolve_providers() -> list[str]:
    available_providers = ort.get_available_providers()
    configured_providers = os.environ.get(PROVIDERS_ENV)

    if configured_providers:
        requested_providers = [
            provider.strip() for provider in configured_providers.split(",")
        ]
        providers = [provider for provider in requested_providers if provider]
        unsupported = [
            provider for provider in providers if provider not in available_providers
        ]
        if unsupported:
            raise ValueError(
                f"unsupported providers requested via {PROVIDERS_ENV}: {unsupported}"
            )
        if providers:
            return providers

    if "CPUExecutionProvider" in available_providers:
        return ["CPUExecutionProvider"]

    return available_providers


def new_session(model_name: str = DEFAULT_MODEL) -> BaseSession:
    session_class: Type[BaseSession]
    session_class = SimpleSession

    if model_name not in SUPPORTED_MODELS:
        raise NotImplementedError(f"unsupported model: {model_name}")

    full_path = _resolve_model_path(model_name)
    if not full_path.exists():
        raise FileNotFoundError(f"model file not found: {full_path}")

    sess_opts = ort.SessionOptions()

    if "OMP_NUM_THREADS" in os.environ:
        sess_opts.inter_op_num_threads = int(os.environ["OMP_NUM_THREADS"])

    return session_class(
        model_name,
        ort.InferenceSession(
            str(full_path),
            providers=_resolve_providers(),
            sess_options=sess_opts,
        ),
    )
