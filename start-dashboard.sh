#!/bin/bash
cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

cd "$(dirname "$0")"
mkdir -p shared

cd dashboard
source venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/semar-dashboard.log 2>&1 &
BACKEND_PID=$!
deactivate
cd ..

cd frontend
npm run dev > /tmp/semar-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2
echo ""
echo "SEMAR WATCH — Dashboard aktif"
echo "  URL     : http://localhost:5173"
echo "  API     : http://localhost:8000"
echo "  CV      : NONAKTIF (hemat daya)"
echo "  Log     : /tmp/semar-dashboard.log"
echo "  Ctrl+C  : stop semua"
echo ""
wait
