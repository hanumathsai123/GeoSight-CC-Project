#!/usr/bin/env bash
cd "$(dirname "$0")/backend"
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
uvicorn main:app --reload --port 8000
