#!/usr/bin/env bash
if [ -f /tmp/semar-cv.pid ]; then
    PID=$(cat /tmp/semar-cv.pid)
    kill "$PID" 2>/dev/null && echo "CV Engine dihentikan (PID: $PID)" || echo "Proses tidak ditemukan"
    rm /tmp/semar-cv.pid
else
    pkill -f "uvicorn main:app.*8001" 2>/dev/null && echo "CV Engine dihentikan" || echo "CV Engine tidak sedang berjalan"
fi
