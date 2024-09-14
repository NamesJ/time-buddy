@echo off
REM Default PyInstaller options
set OPTIONS=--onefile ^
--name="TimeBuddy" ^
--clean

REM First to this script determins whether `--noconsole`
if "%1"=="--noconsole" (
    REM Include `--noconsole` option in PyInstaller options if provided to this script
    set OPTIONS=%OPTIONS% --noconsole
    echo Build with --noconsole option...
) else (
    REM Don't include the `--noconsole` option if no passed
    echo Building without the --noconsole option...
)

pyinstaller %OPTIONS% timebuddy.py