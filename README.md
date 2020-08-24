# RAW to JPG
A simple Python script to convert CR2 photos to JPG and retain timestamps.

## Features

- Recursively walk through folders, convert raws and maintain folder structure
- Copy files that are no raw images along
- Detect already existing jpg files and ignore them
- Archive mode: Recursively copy only CR2-files into an archive folder

## Instructions

1. Clone or download
2. Install required packages with `pip install`
3. Run the script and pass source and destination folders, for example: `./cr2-to-jpg.py ~/Desktop/raw ~/Desktop/converted`

## Requirements
The script runs with python3. It requires the following packages:

- `rawpy` from https://pypi.org/project/rawpy/
- `numpy` from https://pypi.python.org/pypi/numpy
- `PIL` from https://pypi.python.org/pypi/Pillow

For the group enhancement feature you also need:

- `opencv-python` from https://pypi.org/project/opencv-python/
- `opencv` from whereever it is shipped for your os

For the linux gui you need `python-gobject` (https://pypi.org/project/PyGObject/)

These are now set in requirements.txt for easier install.

It also requires `libraw` to be installed.

## Credits

Thank you to [@mateusz-michalik](https://github.com/mateusz-michalik/), who created the original script.
