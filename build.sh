#!/usr/bin/bash
rm -rf dist build main.spec
pyinstaller --onefile --noconsole --add-data "assets:assets" --icon=icon.ico main.py
