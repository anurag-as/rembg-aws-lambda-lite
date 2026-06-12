#!/usr/bin/env bash
set -euo pipefail

# Use this script to manually publish to PyPI!

python -m pip install --upgrade build twine
python -m build
python -m twine check --strict dist/*

while true; do
    read -p "Do you want to upload to PyPI (Y/N)? " yn
    case $yn in
        [Yy]* ) python -m twine upload dist/*; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
