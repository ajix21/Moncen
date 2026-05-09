#!/bin/bash
cd "$(dirname "$0")"
bash stop-cv.sh
pkill -f "uvicorn main:app.*8000" 2>/dev/null && echo "Dashboard dihentikan" || true
pkill -f "vite" 2>/dev/null && echo "Frontend dihentikan" || true
echo "Semua service dihentikan."
