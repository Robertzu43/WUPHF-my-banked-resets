@echo off
setlocal
cd /d "%~dp0"
where codex >nul 2>nul
if errorlevel 1 goto missing
where py >nul 2>nul
if errorlevel 1 (set "WUPHF_PYTHON=python") else (set "WUPHF_PYTHON=py -3")
%WUPHF_PYTHON% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>nul
if errorlevel 1 goto missing
if not exist ".venv\Scripts\python.exe" %WUPHF_PYTHON% -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import keyring" >nul 2>nul
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m wuphf.web
if errorlevel 1 goto failed
exit /b 0
:missing
echo WUPHF needs Python 3.11 or newer and the signed-in Codex CLI. See README.md.
pause
exit /b 1
:failed
echo WUPHF could not start. Check the messages above and README.md.
pause
exit /b 1
