import os
import pathlib
import sys

sys.path.append(os.path.dirname(__file__))
from setuptools import setup

from build_config import get_packaged_model_files, validate_packaged_model_files
import versioneer

here = pathlib.Path(__file__).parent.resolve()
validate_packaged_model_files(here)

long_description = (here / "README.md").read_text(encoding="utf-8")

requires = [
    "numpy>=1.26,<3",
    "onnxruntime>=1.20.1,<1.26",
    "opencv-python-headless>=4.10,<5",
    "pillow>=10.3,<13",
]

extras_require = {
    "gpu": ["onnxruntime-gpu>=1.20.1,<1.26"],
}

setup(
    name="rembg-aws-lambda-lite",
    description="Remove image background",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anurag-as/rembg-aws-lambda-lite",
    author="Anurag A S",
    author_email="sampathanurag3@gmail.com",
    maintainer="Anurag A S",
    maintainer_email="sampathanurag3@gmail.com",
    project_urls={
        "Source": "https://github.com/anurag-as/rembg-aws-lambda-lite",
        "Issues": "https://github.com/anurag-as/rembg-aws-lambda-lite/issues",
        "Original upstream fork": "https://github.com/rnag/rembg-aws-lambda",
        "Original rembg project": "https://github.com/danielgatis/rembg",
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="remove, background, u2netp",
    packages=["rembg"],
    package_data={"rembg": get_packaged_model_files()},
    include_package_data=False,
    python_requires=">=3.10, <3.13",
    install_requires=requires,
    extras_require=extras_require,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
