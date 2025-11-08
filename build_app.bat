@echo off
chcp 65001 > nul
echo Packaging file transfer tool...
echo.

REM Set variables
set APP_NAME=FileTransferTool
set MAIN_SCRIPT=file_transfer_tool.py
set ICON_FILE=icon.ico
set VERSION=1.0.0

REM Check if icon file exists
if not exist %ICON_FILE% (
    echo Warning: Icon file not found %ICON_FILE%, using default icon
    set ICON_OPTION=
) else (
    set ICON_OPTION=--icon=%ICON_FILE%
)

REM Execute packaging command
python -m PyInstaller --onefile --windowed ^
    --name=%APP_NAME% ^
    --version-file=version_info.txt ^
    %ICON_OPTION% ^
    --add-data="README.md;." ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=. ^
    %MAIN_SCRIPT%

echo.
echo Packaging completed!
echo Executable file located at: dist\%APP_NAME%.exe
echo.
pause