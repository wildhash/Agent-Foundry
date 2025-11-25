#!/bin/bash

echo "🧪 Agent Foundry Cluster - System Test"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# Test 1: Redis Installation
echo "Test 1: Redis Installation"
which redis-server > /dev/null 2>&1
test_result $? "Redis is installed"
echo ""

# Test 2: Redis Running
echo "Test 2: Redis Service"
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi
redis-cli ping > /dev/null 2>&1
test_result $? "Redis is running and responding"
echo ""

# Test 3: Python Dependencies
echo "Test 3: Python Dependencies"
cd /workspace/backend
python3 -c "import fastapi, uvicorn, redis, psutil, pydantic" 2>/dev/null
test_result $? "All Python dependencies available"
echo ""

# Test 4: Module Imports
echo "Test 4: Module Imports"
python3 -c "from agents.worker_pool import agent_pool; from agents.infrastructure_agent import infra_agent; from routers.cluster import router" 2>/dev/null
test_result $? "All custom modules import successfully"
echo ""

# Test 5: Redis Connectivity
echo "Test 5: Redis Connectivity from Python"
python3 -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping()" 2>/dev/null
test_result $? "Python can connect to Redis"
echo ""

# Test 6: File Permissions
echo "Test 6: File Permissions"
[ -x /workspace/setup.sh ] && [ -x /workspace/start_backend.sh ]
test_result $? "Setup scripts are executable"
echo ""

# Test 7: Frontend Files
echo "Test 7: Frontend Files"
[ -f /workspace/frontend/components/ClusterDashboard.tsx ] && [ -f /workspace/frontend/app/cluster/page.tsx ]
test_result $? "Frontend files exist"
echo ""

# Test 8: Backend Structure
echo "Test 8: Backend Structure"
[ -f /workspace/backend/agents/worker_pool.py ] && \
[ -f /workspace/backend/agents/infrastructure_agent.py ] && \
[ -f /workspace/backend/routers/cluster.py ] && \
[ -f /workspace/backend/main.py ]
test_result $? "All backend files exist"
echo ""

# Summary
echo "========================================"
echo "Test Results:"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! System is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start backend: ./start_backend.sh"
    echo "  2. Start frontend: cd frontend && npm run dev"
    echo "  3. Open dashboard: http://localhost:3000/cluster"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please fix issues before starting.${NC}"
    exit 1
fi
