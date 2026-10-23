@echo off
color 0a
echo "Cleaning up previous build files..."
rmdir /s /q .\dist
rmdir /s /q .\build
del main.spec
echo "Beginning build..."
pyinstaller --onefile --noconsole --add-data "assets;assets" --icon=icon.ico main.py
