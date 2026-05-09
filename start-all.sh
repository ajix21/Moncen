#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "Menjalankan semua service..."
bash start-dashboard.sh &
sleep 2
bash start-cv.sh
echo "Semua service aktif."
