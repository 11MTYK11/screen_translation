@echo off
pyinstaller setup.py --onefile --icon=Noicon --icon=NONE --add-binary "./bin/7zr.exe;./bin"
pause