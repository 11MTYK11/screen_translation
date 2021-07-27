import subprocess
import shutil
import os,sys

targetname = "Screen_OCR.py"
subprocess.run(["pyinstaller",targetname,"-y","--upx-dir=upx-3.96-win64","--onedir","--noconsole","--icon=Noicon","--icon=NONE","--exclude","matplotlib"])

try:
    shutil.copytree("adddata","dist\\" + os.path.splitext(os.path.basename(targetname))[0] + "\\adddata")
except:
    import traceback
    traceback.print_exc()
try:
    shutil.copytree("easyocr","dist\\" + os.path.splitext(os.path.basename(targetname))[0] + "\\easyocr")
except:
    import traceback
    traceback.print_exc()

input("終了しました")

