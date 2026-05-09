#!/usr/bin/env bash
set -e
echo "=== SEMAR WATCH v2 Setup ==="

mkdir -p shared models

# Dashboard backend
echo "-> Setup dashboard backend..."
cd dashboard
python -m venv venv
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
pip install --quiet -r requirements.txt
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from database import init_db
asyncio.run(init_db())
print('Database initialized')
"
deactivate
cd ..

# CV Engine backend
echo "-> Setup cv-engine backend..."
cd cv-engine
python -m venv venv
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
pip install --quiet -r requirements.txt
deactivate
cd ..

# Frontend
echo "-> Setup frontend..."
cd frontend
npm install --silent
cd ..

echo ""
echo "Setup selesai. Gunakan:"
echo "  bash start-dashboard.sh   (monitoring saja, hemat daya)"
echo "  bash start-cv.sh          (aktifkan analisis massa)"
echo "  bash start-all.sh         (semua sekaligus)"
