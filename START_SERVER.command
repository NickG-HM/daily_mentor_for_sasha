#!/bin/bash

cd "$(dirname "$0")"

echo "=================================================="
echo "  Daily Mentor Video Downloader - Starting..."
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3 from: https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Python 3 found"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing required packages..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Packages installed"
echo ""

# Start the server
echo "=================================================="
echo "🚀 Starting server on http://localhost:8888"
echo "=================================================="
echo ""
echo "⚠️  To stop the server, press CTRL+C"
echo ""

python3 app.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Server stopped with error"
    read -p "Press Enter to exit..."
fi

