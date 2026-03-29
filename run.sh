#!/bin/bash
# ============================================================
#  SuperMart - Quick Setup Script
# ============================================================

echo "🛒 SuperMart Management System - Setup"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install Flask Werkzeug --quiet

echo ""
echo "🚀 Starting SuperMart..."
echo "📍 URL: http://localhost:5000"
echo "🔑 Login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python3 app.py
