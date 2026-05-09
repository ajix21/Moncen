#!/usr/bin/env bash
cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  rm -f /tmp/semar-dashboard.pid /tmp/semar-frontend.pid
  exit 0
}
trap cleanup SIGINT SIGTERM

cd "$(dirname "$0")"
mkdir -p shared

cd dashboard
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/semar-dashboard.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/semar-dashboard.pid
deactivate
cd ..

cd frontend
npm run dev > /tmp/semar-frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/semar-frontend.pid
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
