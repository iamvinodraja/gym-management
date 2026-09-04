#!/bin/bash
# =========================================================
# Pakistani Gym Management System - Launcher Script
# =========================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================="
echo "   PAKISTANI GYM MANAGEMENT SYSTEM (PKR / Rs.)         "
echo "======================================================="

# Run seed script to ensure database and default records exist
echo "Checking database & seeding sample Pakistani gym data..."
python3 backend/seed_data.py

echo ""
echo "Starting FastAPI server on http://127.0.0.1:8000"
echo "Admin Login: admin / admin123"
echo "Receptionist: reception / rec123"
echo ""

exec python3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
