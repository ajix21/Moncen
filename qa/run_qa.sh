#!/usr/bin/env bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

MODE=$1

echo ""
echo "=== SEMAR WATCH QA ==="
echo ""

if [ "$MODE" = "--structure-only" ]; then
    echo "Mode: structural checks (tidak butuh server)"
    python -m pytest test_01_structure.py -v --timeout=30
    exit $?
fi

if [ "$MODE" = "--security-only" ]; then
    echo "Mode: security checks"
    python -m pytest test_06_security.py -v --timeout=30
    exit $?
fi

echo "Mode: full suite"
echo "Pastikan ./start-all.sh sudah dijalankan"
echo ""

python -m pytest \
    test_01_structure.py \
    test_02_dashboard_api.py \
    test_03_cv_engine_api.py \
    test_04_websocket.py \
    test_05_service_interaction.py \
    test_06_security.py \
    test_07_resource.py \
    -v --timeout=60 \
    --tb=short \
    -p no:warnings
