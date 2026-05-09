#!/usr/bin/env bash
# Setup QA environment — uses its own venv, does not touch dashboard/ or cv-engine/ venvs
set -e
cd "$(dirname "$0")"

echo "=== Setup QA Environment ==="

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "QA venv created"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install --quiet -r requirements.txt
echo "QA dependencies installed"
echo ""
echo "Gunakan: ./qa/run_qa.sh"
