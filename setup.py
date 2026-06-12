from setuptools import find_packages, setup

setup(
    name="slots",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["slots = slots.__main__:main"],
    },
    description="Save slots for coding projects.",
    author="hohohocch",
    url="https://slots.hohohocch.com",
    python_requires=">=3.10",
    install_requires=["colorama"],
    extras_require={
        "dev": ["pytest"],
    },
)
