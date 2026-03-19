#!/usr/bin/env bash

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} Resume Matcher Web App - Setup and Run     ${NC}"
echo -e "${GREEN}============================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WRITE_MODE=0
SMOKE_TEST=0
for arg in "$@"; do
  case "$arg" in
    -write|--write)
      WRITE_MODE=1
      ;;
    --smoke-test)
      SMOKE_TEST=1
      ;;
    *)
      echo -e "${RED}Unknown argument: ${arg}${NC}"
      echo "Usage: ./install_and_run.sh [--write] [--smoke-test]"
      exit 1
      ;;
  esac
done

echo -e "\n${YELLOW}[1/4] Checking Homebrew...${NC}"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Installing Homebrew..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # Ensure brew is available in this shell after install.
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi

  if ! command -v brew >/dev/null 2>&1; then
    echo -e "${RED}Error: Homebrew installation did not complete successfully.${NC}"
    exit 1
  fi
  echo "Homebrew installed."
else
  echo "Homebrew already installed."
fi

echo -e "\n${YELLOW}[2/4] Installing system dependencies...${NC}"
if ! brew list tesseract >/dev/null 2>&1; then
  brew install tesseract
else
  echo "tesseract already installed."
fi
if ! brew list poppler >/dev/null 2>&1; then
  brew install poppler
else
  echo "poppler already installed."
fi

echo -e "\n${YELLOW}[3/4] Installing Python dependencies...${NC}"
if command -v pip >/dev/null 2>&1; then
  PIP_CMD="pip"
elif command -v pip3 >/dev/null 2>&1; then
  PIP_CMD="pip3"
else
  echo -e "${RED}Error: pip is not installed.${NC}"
  exit 1
fi
"$PIP_CMD" install -r requirements.txt

echo -e "\n${YELLOW}[4/4] Starting web app on http://localhost:8000 ...${NC}"
if [[ "$WRITE_MODE" -eq 1 ]]; then
  echo -e "${GREEN}Write mode enabled (DB sync active from start).${NC}"
  export RESUME_MATCHER_WRITE_MODE=1
else
  echo -e "${YELLOW}Write mode off. Enable from Settings with username/password.${NC}"
fi

if [[ "$SMOKE_TEST" -eq 1 ]]; then
  echo "Smoke test mode: starting server, checking /health, then exiting."
  uvicorn backend.app:app --host 127.0.0.1 --port 8000 >/tmp/resume_matcher_uvicorn.log 2>&1 &
  UVICORN_PID=$!
  cleanup() {
    if kill -0 "$UVICORN_PID" >/dev/null 2>&1; then
      kill "$UVICORN_PID" >/dev/null 2>&1 || true
      wait "$UVICORN_PID" 2>/dev/null || true
    fi
  }
  trap cleanup EXIT

  for i in {1..30}; do
    if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
      echo -e "${GREEN}Smoke test passed: /health is reachable.${NC}"
      exit 0
    fi
    sleep 1
  done

  echo -e "${RED}Smoke test failed: /health did not become reachable in time.${NC}"
  echo "Check /tmp/resume_matcher_uvicorn.log for details."
  exit 1
fi

exec uvicorn backend.app:app --reload --port 8000
