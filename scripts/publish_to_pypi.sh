#!/usr/bin/env bash
set -euo pipefail

# Use this script to manually publish to PyPI!

export REMBG_PACKAGE_MODELS="${REMBG_PACKAGE_MODELS:-u2netp}"
python -m pip install --upgrade build twine
python - <<'PY'
from pathlib import Path

dist = Path("dist")
if dist.exists():
    for path in dist.iterdir():
        if path.is_file():
            path.unlink()
PY
python -m build
python - <<'PY'
import zipfile
from pathlib import Path

wheels = sorted(Path("dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"expected exactly one wheel, found: {wheels}")

with zipfile.ZipFile(wheels[0]) as wheel:
    names = set(wheel.namelist())

if "rembg/u2netp.onnx" not in names:
    raise SystemExit("lite wheel is missing rembg/u2netp.onnx")
if "rembg/u2net.onnx" in names:
    raise SystemExit("lite wheel unexpectedly contains rembg/u2net.onnx")
PY
python -m twine check --strict dist/*

while true; do
    read -p "Do you want to upload to PyPI (Y/N)? " yn
    case $yn in
        [Yy]* ) python -m twine upload dist/*; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
