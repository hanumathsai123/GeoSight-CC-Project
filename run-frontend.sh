#!/usr/bin/env bash
cd "$(dirname "$0")/frontend"
[ -f .env ] || cp .env.example .env
npm install
npm run dev
