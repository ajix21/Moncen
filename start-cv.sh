#!/usr/bin/env bash
cd "$(dirname "$0")"
mkdir -p shared models

if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "CV Engine sudah berjalan (port 8001)"
    exit 0
fi

cd cv-engine
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/semar-cv.log 2>&1 &
CV_PID=$!
echo $CV_PID > /tmp/semar-cv.pid
deactivate
cd ..

sleep 3
echo "CV Engine aktif (PID: $CV_PID)"
echo "  Port    : 8001"
echo "  Model   : YOLOv8n (nano)"
echo "  Log     : /tmp/semar-cv.log"
echo "  Matikan : ./stop-cv.sh"
