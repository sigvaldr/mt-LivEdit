rmdir /s /q dist
rmdir /s /q build
del main.spec
pyinstaller --onefile --noconsole --add-data "assets;assets" --icon=icon.ico main.py
