#!/usr/bin/env bash
if [ -f /tmp/semar-cv.pid ]; then
    PID=$(cat /tmp/semar-cv.pid)
    kill "$PID" 2>/dev/null && echo "CV Engine dihentikan (PID: $PID)" || echo "Proses tidak ditemukan"
    rm -f /tmp/semar-cv.pid
else
    echo "CV Engine tidak berjalan (PID file tidak ditemukan)"
fi
