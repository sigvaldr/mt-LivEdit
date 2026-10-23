#!/usr/bin/bash
echo "Cleaning up previous build files..."
rm -rf dist build main.spec
echo "Buildling..."
pyinstaller --onefile --noconsole --add-data "assets:assets" --icon=icon.ico main.py
