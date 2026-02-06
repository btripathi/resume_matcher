#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   Resume Matcher App - Setup & Run      ${NC}"
echo -e "${GREEN}=========================================${NC}"

# 1. Check for Homebrew (Required for system tools on Mac)
if ! command -v brew &> /dev/null; then
    echo -e "${RED}Error: Homebrew is not installed.${NC}"
    echo "Please install it from https://brew.sh/ and run this script again."
    exit 1
fi

# 2. Install System Dependencies
echo -e "\n${YELLOW}[1/4] Checking System Dependencies (OCR Tools)...${NC}"
if ! brew list tesseract &>/dev/null; then
    echo "Installing Tesseract..."
    brew install tesseract
else
    echo "✅ Tesseract is installed."
fi

if ! brew list poppler &>/dev/null; then
    echo "Installing Poppler..."
    brew install poppler
else
    echo "✅ Poppler is installed."
fi

# 3. Pyenv Auto-Fix (NEW)
# If pyenv is installed but no version is selected, try to set one
if command -v pyenv &> /dev/null; then
    # Check if a python version is currently active
    if ! pyenv version-name &> /dev/null || [[ $(pyenv version-name) == "system" ]]; then
        echo -e "\n${YELLOW}[Pyenv Detected] No local python version set.${NC}"
        # Try to find 3.12.8 or similar
        AVAILABLE_PY=$(pyenv versions --bare | grep "3.12" | tail -1)
        if [ -n "$AVAILABLE_PY" ]; then
            echo "⚡ Automatically setting local python to $AVAILABLE_PY"
            pyenv local "$AVAILABLE_PY"
        else
            echo "⚠️ Could not auto-detect a suitable Python 3.12 version."
        fi
    fi
fi

# 4. Install Python Dependencies
echo -e "\n${YELLOW}[2/4] Installing Python Libraries...${NC}"
# Check if pip exists
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip (Python Package Manager) not found.${NC}"
    echo "Tip: Run 'pyenv local 3.12.8' (or your installed version) to fix this."
    exit 1
fi
pip install -r requirements.txt --quiet
echo -e "✅ Python libraries installed."

# 5. Verify LM Studio Server
echo -e "\n${YELLOW}[3/4] Verifying Local AI Server (LM Studio)...${NC}"
LM_URL="http://localhost:1234/v1/models"

# Function to check server
check_server() {
    curl -s --connect-timeout 2 "$LM_URL" > /dev/null
    return $?
}

if check_server; then
    echo -e "✅ LM Studio Server is UP and responding."
else
    echo -e "${RED}❌ Cannot connect to LM Studio at localhost:1234${NC}"
    echo -e "${YELLOW}Action Required:${NC}"
    echo "  1. Open LM Studio."
    echo "  2. Go to the 'Local Server' tab (double arrow icon)."
    echo "  3. Click 'Start Server'."
    echo "  4. Ensure a model is loaded."

    echo -e "\nWaiting for server to start (Press Ctrl+C to quit)..."

    # Loop to wait for user to start server
    while ! check_server; do
        sleep 2
        echo -n "."
    done
    echo -e "\n${GREEN}✅ Connection established!${NC}"
fi

# 6. Launch App
echo -e "\n${GREEN}[4/4] 🚀 Launching Resume Matcher App...${NC}"
streamlit run resume_matcher_app.py
