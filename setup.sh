#!/bin/bash

echo "🚀 Agent Foundry - Quick Setup"
echo "================================"

# Install Redis
echo "📦 Installing Redis..."
sudo apt-get update -qq
sudo apt-get install -y redis-server

# Start Redis (use manual start since systemd might not be available)
echo "🔧 Starting Redis..."
redis-server --daemonize yes
sleep 2

# Verify Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis failed to start"
    exit 1
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt

# Install Node dependencies
echo "📦 Installing Node dependencies..."
cd ../frontend
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the cluster:"
echo "  Terminal 1: ./start_backend.sh"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
echo "Or manually:"
echo "  Terminal 1: cd backend && python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
echo "Dashboard: http://localhost:3000/cluster"
echo "API: http://localhost:8000/docs"
