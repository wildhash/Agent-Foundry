# 🚀 Agent Foundry Cluster - Deployment Guide

## Quick Start (3 Steps)

### 1. Run Setup Script
```bash
./setup.sh
```

This will:
- ✅ Install Redis
- ✅ Start Redis server
- ✅ Install Python dependencies (psutil, redis, fastapi, etc.)
- ✅ Install Node/React dependencies

### 2. Start Backend (Terminal 1)
```bash
./start_backend.sh
```

Or manually:
```bash
cd /workspace/backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend (Terminal 2)
```bash
cd /workspace/frontend
npm run dev
```

## 🎯 Access Points

Once both services are running:

- **Frontend Dashboard:** http://localhost:3000/cluster
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Root:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health

## 🧪 Verify Installation

### Test Redis
```bash
redis-cli ping
# Should return: PONG
```

### Test Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","cluster_initialized":true,"infrastructure_agent":true}
```

### Test Cluster Status
```bash
curl http://localhost:8000/api/cluster/status | python3 -m json.tool
```

### Submit Test Task
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=test%20task"
```

## 📊 What You'll See

### Backend Startup Logs
```
🚀 Starting Agent Foundry Cluster...
🚀 Initializing Agent Foundry Worker Pool...
✅ Started architect worker (PID: 12345)
✅ Started coder worker (PID: 12346)
✅ Started executor worker (PID: 12347)
✅ Started critic worker (PID: 12348)
✅ Started deployer worker (PID: 12349)
✅ Spawned 5 agent workers
🏥 Health monitor started
🔧 Infrastructure Agent starting...
✅ Cluster online and self-healing enabled
```

### Frontend Dashboard
You'll see:
- **Summary Cards**: Total agents, healthy count, unhealthy count
- **System Health**: CPU, Memory, Disk usage with color-coded bars
- **Live Agent Table**: Real-time worker status with PIDs, task counts, errors
- **Action Buttons**: Manual self-heal trigger, refresh

## 🔥 Self-Healing Demo

### Simulate Worker Crash
```bash
# Find a worker PID from the dashboard
# Kill it manually
kill -9 <PID>

# Watch the logs - it will auto-restart in ~10 seconds
# The health monitor detects the dead worker and spawns a new one
```

### Test Manual Heal
```bash
curl -X POST http://localhost:8000/api/cluster/heal
```

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                     │
│           http://localhost:3000/cluster                 │
│  • Real-time dashboard (polls every 2s)                │
│  • System health visualization                         │
│  • Worker status monitoring                            │
└────────────────────────────────────────────────────────┘
                           ↓ HTTP REST API
┌────────────────────────────────────────────────────────┐
│              Backend (FastAPI)                          │
│           http://localhost:8000                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Infrastructure Agent                      │ │
│  │  • Monitors CPU/RAM/Disk                         │ │
│  │  • Auto-heals system issues                      │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │         Worker Pool Manager                       │ │
│  │  • Spawns 5 agent workers                        │ │
│  │  • Health checks every 10s                       │ │
│  │  • Auto-restarts dead workers                    │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                           ↓ Task Queues
┌────────────────────────────────────────────────────────┐
│                Redis (localhost:6379)                   │
│  • Task queues: tasks:architect, tasks:coder, ...     │
│  • Result queues: results:{task_id}                   │
│  • Heartbeats: heartbeat:{worker_id}                  │
│  • Worker stats: worker:{worker_id}                   │
└────────────────────────────────────────────────────────┘
                           ↓ Process Pool
┌────────────────────────────────────────────────────────┐
│              Agent Workers (5 Processes)                │
│  • architect_001  (PID: xxxxx)                        │
│  • coder_001      (PID: xxxxx)                        │
│  • executor_001   (PID: xxxxx)                        │
│  • critic_001     (PID: xxxxx)                        │
│  • deployer_001   (PID: xxxxx)                        │
│                                                         │
│  Each worker:                                          │
│  - Runs in separate process (multiprocessing)         │
│  - Polls Redis task queue (5s blocking)               │
│  - Sends heartbeat every loop (30s TTL)               │
│  - Self-heals on errors (increments counter)          │
└────────────────────────────────────────────────────────┘
```

## 🛠️ Troubleshooting

### Issue: Redis Connection Failed

**Symptom:** `redis.exceptions.ConnectionError`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start it
redis-server --daemonize yes

# Verify
redis-cli ping  # Should return PONG
```

### Issue: Workers Not Starting

**Symptom:** Cluster shows 0 healthy workers

**Solution:**
```bash
# Check backend logs for errors
cd /workspace/backend
python3 -m uvicorn main:app --reload

# Look for import errors or permission issues
# Ensure all dependencies are installed:
pip3 install -r requirements.txt
```

### Issue: Frontend Can't Connect to Backend

**Symptom:** Network error in browser console

**Solution:**
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check CORS settings in backend/main.py
# Should have: allow_origins=["*"] for development

# 3. Ensure backend is on correct port
# Should be: 0.0.0.0:8000
```

### Issue: Permission Denied Errors

**Symptom:** `sudo: command not found` or permission errors

**Solution:**
```bash
# Infrastructure agent requires sudo for some operations
# If running without sudo, some healing features will be disabled
# Check permissions:
curl http://localhost:8000/api/cluster/status | grep permissions

# The system will still work, but with limited healing capabilities
```

## 📈 Monitoring & Observability

### API Endpoints

#### Cluster Status
```bash
curl http://localhost:8000/api/cluster/status
```
Returns: Complete cluster state, worker health, system metrics

#### Live Agents
```bash
curl http://localhost:8000/api/cluster/agents/live
```
Returns: Real-time agent status optimized for frontend

#### Metrics
```bash
curl http://localhost:8000/api/cluster/metrics
```
Returns: Detailed system and Redis metrics

#### Healing History
```bash
curl http://localhost:8000/api/cluster/infrastructure/healing-history
```
Returns: Last 50 infrastructure healing actions

### Task Submission & Results

#### Submit Task
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=design%20auth%20system"
```
Returns: `{"task_id": "uuid", "agent_type": "architect", "status": "submitted"}`

#### Get Result
```bash
curl http://localhost:8000/api/cluster/task/<TASK_ID>
```
Returns: Task result or pending status

## 🔧 Configuration

### Environment Variables

Create `.env` file in backend directory (optional):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
HEALTH_CHECK_INTERVAL=10
HEARTBEAT_TTL=30
```

### Redis Configuration

Default settings in `/etc/redis/redis.conf`:
- Port: 6379
- Bind: 127.0.0.1
- Max Memory: Auto
- Persistence: RDB (optional)

### Worker Pool Settings

Edit `backend/agents/worker_pool.py`:
```python
agent_types = ["architect", "coder", "executor", "critic", "deployer"]
# Add more types or increase count per type
```

## 🚀 Production Deployment

### Docker Deployment (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install Redis
RUN apt-get update && apt-get install -y redis-server

# Copy application
WORKDIR /app
COPY backend /app/backend
COPY frontend /app/frontend

# Install dependencies
RUN pip install -r backend/requirements.txt
RUN cd frontend && npm install && npm run build

# Start services
CMD redis-server --daemonize yes && \
    cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 & \
    cd frontend && npm start
```

### Kubernetes Deployment

Create separate deployments for:
1. Redis (StatefulSet)
2. Backend (Deployment with 1+ replicas)
3. Frontend (Deployment with 1+ replicas)

### Health Checks

Configure liveness and readiness probes:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## 📦 File Structure

```
/workspace/
├── backend/
│   ├── agents/
│   │   ├── worker_pool.py          # ✅ Worker pool + self-healing
│   │   └── infrastructure_agent.py # ✅ System monitoring
│   ├── routers/
│   │   └── cluster.py              # ✅ API endpoints
│   ├── main.py                     # ✅ FastAPI app with lifecycle
│   └── requirements.txt            # ✅ Updated dependencies
├── frontend/
│   ├── app/
│   │   └── cluster/
│   │       └── page.tsx            # ✅ Cluster page route
│   └── components/
│       └── ClusterDashboard.tsx    # ✅ Real-time dashboard
├── setup.sh                        # ✅ Automated setup
├── start_backend.sh                # ✅ Backend startup helper
├── CLUSTER_SETUP.md               # ✅ Setup documentation
└── DEPLOYMENT.md                  # ✅ This file
```

## ✅ Verification Checklist

- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] Python dependencies installed
- [ ] Backend starts without errors
- [ ] All 5 workers spawn successfully
- [ ] Health monitor logs appear
- [ ] Infrastructure agent starts
- [ ] Frontend builds/runs without errors
- [ ] Dashboard loads at http://localhost:3000/cluster
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Can submit tasks via API
- [ ] Workers process tasks (check Redis: `redis-cli LLEN tasks:architect`)
- [ ] Manual heal button works
- [ ] System metrics display correctly

## 🎓 Next Steps

1. **Integrate LLMs:** Connect agents to OpenAI/Anthropic/etc.
2. **Add Persistence:** Store task history in PostgreSQL/MongoDB
3. **Scale Workers:** Add more workers per agent type
4. **Add Authentication:** Secure API endpoints
5. **Custom Agents:** Extend `_execute_task()` with real logic
6. **Metrics Export:** Add Prometheus/Grafana integration
7. **Load Testing:** Test with concurrent task submissions

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in terminal output
3. Verify all dependencies are installed
4. Check Redis is running
5. Ensure ports 3000 and 8000 are available

---

**System is ready! Start building! 🚀**
