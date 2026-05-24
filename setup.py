from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="demtools",
    version="0.1.0",
    author="aaronchh",
    author_email="aaronhsu219@gmail.com",
    description="A collection of tools for working with DEM (Digital Elevation Model) raster files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AaronOET/demtools",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "demtools=demtools.cli:main",
            "demtools-info=demtools.describe:main",
            "chgnodata=demtools.chgnodata:main",
            "setnodata=demtools.setnodata:main",
            "csv2tif=demtools.csv2tif:main",
        ],
    },
)
