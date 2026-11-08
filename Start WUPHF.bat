@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0" || exit /b 1
rem Discovery must never acquire a runtime through Python's install manager.
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"
set "PYLAUNCHER_ALLOW_INSTALL="
set "PYLAUNCHER_ALWAYS_INSTALL="
set "WUPHF_RUNTIME="
set "WUPHF_RUNTIME_ARG="
if not defined WUPHF_PYTHON goto environment
"%WUPHF_PYTHON%" -c "import sys; sys.exit(sys.version_info < (3,11))" >nul 2>nul
if errorlevel 1 goto invalid_override
set "WUPHF_RUNTIME=%WUPHF_PYTHON%"
:environment
if exist ".venv" goto existing_environment
if defined WUPHF_RUNTIME goto create_environment
for %%V in (-3 -3.13 -3.11 -3.14 -3.12 -3.15) do call :try_python py %%V
for %%P in (python python3 python3.13 python3.11 python3.14 python3.12 python3.15) do call :try_python %%P
if not defined WUPHF_RUNTIME goto missing_python
:create_environment
where codex >nul 2>nul
if errorlevel 1 goto missing_codex
"%WUPHF_RUNTIME%" %WUPHF_RUNTIME_ARG% -m venv .venv
if errorlevel 1 goto failed_venv
:existing_environment
".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3,11))" >nul 2>nul
if errorlevel 1 goto invalid_environment
where codex >nul 2>nul
if errorlevel 1 goto missing_codex
".venv\Scripts\python.exe" -c "import keyring" >nul 2>nul
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed_pip
".venv\Scripts\python.exe" -m wuphf.web
if errorlevel 1 goto failed
exit /b 0
:try_python
if defined WUPHF_RUNTIME exit /b 0
"%~1" %~2 -c "import sys; sys.exit(sys.version_info < (3,11))" >nul 2>nul
if errorlevel 1 exit /b 0
set "WUPHF_RUNTIME=%~1"
set "WUPHF_RUNTIME_ARG=%~2"
exit /b 0
:invalid_override
echo WUPHF_PYTHON must name one working Python 3.11+ executable. Correct or unset it, then reopen. See README.md.
goto stop
:missing_python
echo WUPHF source needs an existing Python 3.11+ runtime. Use a compatible WUPHF bundle, or install Python separately and set WUPHF_PYTHON to its executable. See README.md.
goto stop
:missing_codex
echo WUPHF needs the Codex CLI. Install it and sign in, then reopen WUPHF. See README.md.
goto stop
:invalid_environment
echo The existing .venv is old, broken, or moved. Keep this source folder in its final location; rename .venv to preserve it, then reopen with Python 3.11+. No files were removed. See README.md.
goto stop
:failed_venv
echo Could not create .venv in this source folder. Check folder permissions and Python venv support; preserve/rename any partial .venv before retrying. See README.md.
goto stop
:failed_pip
echo Could not install requirements with .venv pip. Check the error above, network access, and Python pip/venv support; then reopen. See README.md.
goto stop
:failed
echo WUPHF could not start. Check the messages above and README.md.
:stop
pause
exit /b 1
