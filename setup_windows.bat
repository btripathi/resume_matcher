@echo off
SETLOCAL EnableDelayedExpansion

echo =========================================
echo    TalentScout AI - Windows Setup
echo =========================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from python.org and try again.
    pause
    exit /b
)

:: 2. Create Virtual Environment
echo [1/3] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created.
) else (
    echo ✅ Virtual environment already exists.
)

:: 3. Install Requirements
echo [2/3] Installing Python dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install streamlit openai pypdf python-docx pytesseract pillow pandas pdf2image matplotlib --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)
echo ✅ Dependencies installed.

:: 4. Dependency Verification
echo [3/3] Verifying System Tools...

where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Tesseract OCR not found in PATH. 
    echo Please install it and add to PATH to process scanned PDFs.
) else (
    echo ✅ Tesseract OCR detected.
)

:: Note: Poppler check is harder via command line, we rely on the user guide for that.

echo.
echo =========================================
echo ✅ Setup Complete!
echo.
echo To start the app:
echo 1. Ensure LM Studio Server is running at localhost:1234
echo 2. Run the following command:
echo    streamlit run resume_matcher_app.py
echo =========================================
pause
