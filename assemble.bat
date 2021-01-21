@echo off
echo %~dp0
pushd %~dp0
pip3 install -r requirements.txt
pyinstaller jumpcutter.py --onefile

for /f %%i in ('where.exe ffmpeg') do set RESULT=%%i
copy %RESULT% dist\

popd
@echo on
