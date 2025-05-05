from setuptools import setup, find_packages

try:
    with open("readme.md.md", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A modern, feature-rich music player built with Python."

setup(
    name="BeatRoot",
    version="0.1.0",
    author="dontknow492",
    author_email="your.email@example.com",  # Replace with your actual email
    description="A modern, feature-rich music player built with Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dontknow492/BeatRoot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "PySide6",
        "PySide6-Fluent-Widgets",
        "ytmusicapi",
        "loguru",
        "mutagen",
        "python-vlc",
        "yt-dlp",
        "qasync",
        "xxhash",
        "cachetools",
        "aiosqlite",
        "aiofiles",
        "pillow",
        "pyyaml",
        "setuptools"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
