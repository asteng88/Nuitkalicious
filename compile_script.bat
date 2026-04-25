@echo off
echo Nuitkalicious Direct Compiler
echo ==========================
echo.

REM Check if a script path is provided
if "%~1"=="" (
    echo Error: No Python script specified.
    echo Usage: compile_script.bat script.py [options]
    goto :end
)

set SCRIPT_PATH=%~f1
set SCRIPT_DIR=%~dp1
set OPTIONS=%*
set OPTIONS=%OPTIONS:~2%

echo Script path: %SCRIPT_PATH%
echo Output directory: %SCRIPT_DIR%
echo.

REM Check if Nuitka is installed and install it if needed
echo Checking Nuitka installation...
python -c "import importlib.util; print('INSTALLED' if importlib.util.find_spec('nuitka') else 'NOT_INSTALLED')" > nuitka_check.tmp
set /p NUITKA_CHECK=<nuitka_check.tmp
del nuitka_check.tmp

if "%NUITKA_CHECK%"=="NOT_INSTALLED" (
    echo Nuitka is not installed. Installing now...
    python -m pip install --upgrade pip
    python -m pip install nuitka ordered-set
    
    REM Check if installation was successful
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install Nuitka.
        goto :end
    )
    echo Nuitka installed successfully
)

REM Ensure cffi and cryptography are correctly installed
echo Checking dependencies...
python -m pip install --upgrade cffi cryptography

REM Clean Nuitka cache before compilation
echo Cleaning Nuitka cache...
python -m nuitka --clean-cache=all

REM Add default options for safety and performance
set DEFAULT_OPTIONS=--assume-yes-for-downloads --remove-output --clean-cache=all --nofollow-import-to=nuitka --nofollow-import-to=ordered_set --nofollow-import-to=pip --nofollow-import-to=wheel --nofollow-import-to=setuptools --nofollow-import-to=distutils --nofollow-import-to=pkg_resources --nofollow-import-to=cffi --nofollow-import-to=cryptography --nofollow-import-to=pycparser

REM Run Nuitka with the provided script and options
echo Running Nuitka compilation...
echo Command: python -m nuitka %DEFAULT_OPTIONS% %OPTIONS% "%SCRIPT_PATH%"
echo.

python -m nuitka %DEFAULT_OPTIONS% %OPTIONS% "%SCRIPT_PATH%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Compilation successful!
    
    REM Clean up build artifacts
    echo Cleaning up build artifacts...
    if exist %SCRIPT_DIR%build rmdir /s /q %SCRIPT_DIR%build
    if exist %SCRIPT_DIR%*.build rmdir /s /q %SCRIPT_DIR%*.build
    if exist %SCRIPT_DIR%__pycache__ rmdir /s /q %SCRIPT_DIR%__pycache__
    
    echo All done!
) else (
    echo.
    echo Compilation failed with error code %ERRORLEVEL%
)

:end
pause
