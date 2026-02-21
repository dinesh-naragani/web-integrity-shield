#!/bin/bash
# Start Level-2 Deep Analysis Service (Linux/Mac)

echo "=========================================="
echo "Level-2 Deep Analysis Service"
echo "Web Integrity Shield – Phase 3"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Start service
echo ""
echo "Starting Level-2 Service on port 8001..."
echo "API Docs: http://localhost:8001/docs"
echo "Health: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

python level2_service.py
