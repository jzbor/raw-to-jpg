# CR2 to JPG
A simple Python script to convert CR2 photos to JPG and retain timestamps.

## Features

- Recursively walk through folders, convert and maintain folder structure
- Copy files that are no raw images
- Detect existing files and ignore them

## Instructions

1. Clone or download
2. Install required packages with `pip install`
2. Set permissions to execute `chmod +x cr2-to-jpg.py`
3. Run the script and pass source and destination folders, for example: `./cr2-to-jpg.py ~/Desktop/raw ~/Desktop/converted`

## Requirements
This script runs best on `python3.5+` although it may work on `python3.x` as well.

Script requires the following packages:

- `rawkit` from https://pypi.python.org/pypi/rawkit/0.5.0
- `numpy` from https://pypi.python.org/pypi/numpy
- `PIL` from https://pypi.python.org/pypi/Pillow

These are now set in requirements.txt for easier install.

It also requiers `libraw` to be installed. In order for rawkit to work properly you may have to downgrade to `libraw16`.

## Credits

Thank you to [@mateusz-michalik](https://github.com/mateusz-michalik/), who created the original script I forked.
