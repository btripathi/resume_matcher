🪟 TalentScout AI: Windows Setup Guide

This guide will help you get the AI Resume Matcher running on Windows 10/11.

🛠️ Step 1: Install System Dependencies (Mandatory)

Unlike Mac, Windows requires manual installation of the OCR and PDF processing tools.

1. Tesseract OCR (For Scanned PDFs)

Download the installer from UB Mannheim's Tesseract page.

Run the .exe (usually tesseract-ocr-w64-setup-v5.x.x.exe).

Crucial: Note the installation path (default is C:\Program Files\Tesseract-OCR).

Add this path to your System Environment Variables (PATH).

2. Poppler (For PDF to Image conversion)

Download the latest Windows binary from Release page.

Extract the ZIP file to a folder (e.g., C:\poppler).

Add the bin folder (e.g., C:\poppler\Library\bin) to your System Environment Variables (PATH).

3. Python 3.9 or newer

Install from python.org. Ensure "Add Python to PATH" is checked during installation.

⚡ Step 2: Automated Environment Setup

We have provided a setup_windows.bat file to automate the Python setup.

Open Command Prompt (cmd) or PowerShell in the project folder.

Run the setup script:

setup_windows.bat


🚀 Step 3: Run the App

Start LM Studio:

Load your model.

Start the Local Server at localhost:1234.

Launch TalentScout:

venv\Scripts\activate
streamlit run resume_matcher_app.py


🔍 Troubleshooting Windows Issues

TesseractNotFoundError: If the app says Tesseract isn't found, ensure you restarted your terminal after adding it to the PATH.

Poppler missing: If you get an error during PDF processing, double-check that the poppler\...\bin folder is in your system PATH.

Execution Policy: If PowerShell blocks the script, run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser.
