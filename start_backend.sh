#!/bin/bash

echo "🚀 Starting Agent Foundry Backend..."
echo ""

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Verify Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis failed to start"
    exit 1
fi

echo ""
echo "🤖 Starting Agent Cluster..."
cd /workspace/backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
