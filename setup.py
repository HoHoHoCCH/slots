from setuptools import find_packages, setup

setup(
    name="slots",
    version="0.1",
    packages=find_packages(),
    description="Save slots for coding projects.",
    author="hohohocch",
    url="https://slots.hohohocch.com",
    python_requires=">=3.10",
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
