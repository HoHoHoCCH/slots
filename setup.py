from pathlib import Path

from setuptools import find_packages, setup

readme = Path("README.md").read_text(encoding="utf-8")

setup(
    name="slots-cli",
    version="0.1.1",
    packages=find_packages(),
    description="Save slots for coding projects.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="hohohocch",
    url="https://slots.hohohocch.com",
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Software Development :: Version Control",
    ],
    install_requires=["colorama"],
    entry_points={
        "console_scripts": [
            "slots = slots.__main__:main",
            "slots-mcp = slots.slots_mcp:main",
        ],
    },
    extras_require={
        "dev": ["pytest"],
        "mcp": ["mcp[cli]"],
    },
)
