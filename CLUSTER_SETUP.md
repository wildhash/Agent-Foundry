# 🤖 Agent Foundry Self-Healing Cluster

## ✅ Setup Complete!

All files have been created and the system is ready to run.

### 📁 Files Created

**Backend:**
- ✅ `backend/agents/worker_pool.py` - Persistent agent worker pool with self-healing
- ✅ `backend/agents/infrastructure_agent.py` - System health monitoring and auto-healing
- ✅ `backend/routers/cluster.py` - Cluster management API endpoints
- ✅ `backend/main.py` - Updated with cluster lifecycle management
- ✅ `backend/requirements.txt` - Updated with Redis and psutil dependencies

**Frontend:**
- ✅ `frontend/components/ClusterDashboard.tsx` - Real-time cluster monitoring UI
- ✅ `frontend/app/cluster/page.tsx` - Cluster dashboard page route

**Setup:**
- ✅ `setup.sh` - Automated setup script (executable)

### 🚀 Quick Start

#### Option 1: Manual Start

**Terminal 1 - Backend:**
```bash
cd /workspace/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /workspace/frontend
npm run dev
```

#### Option 2: Using Setup Script

```bash
# Run the setup script (installs dependencies)
./setup.sh

# Then start the services in separate terminals
cd backend && python -m uvicorn main:app --reload
cd frontend && npm run dev
```

### 🔍 Access Points

- **Cluster Dashboard:** http://localhost:3000/cluster
- **API Documentation:** http://localhost:8000/docs
- **API Root:** http://localhost:8000/
- **Health Check:** http://localhost:8000/health

### 📊 Features Implemented

#### 1. **Persistent Agent Workers**
- 5 specialized agents running in separate processes:
  - `architect` - System design and planning
  - `coder` - Code generation
  - `executor` - Task execution
  - `critic` - Quality assurance
  - `deployer` - Deployment management

#### 2. **Self-Healing Mechanisms**
- **Worker Health Monitoring:** Checks every 10 seconds
- **Auto-Restart:** Dead workers automatically respawn
- **Heartbeat System:** Redis-based heartbeat tracking (30s TTL)
- **Error Tracking:** Counts and monitors errors per worker

#### 3. **Infrastructure Agent**
- **System Monitoring:** CPU, Memory, Disk usage
- **Auto-Healing:** Detects and fixes issues:
  - High memory → Clear caches
  - High disk → Cleanup temp files
  - Redis down → Restart Redis
- **Healing History:** Tracks all healing actions

#### 4. **Real-Time Dashboard**
- Live agent status (updates every 2 seconds)
- System health metrics with color-coded alerts
- Worker statistics (tasks, errors, uptime)
- Manual self-heal trigger button

### 🧪 Testing the System

#### 1. Check Cluster Status
```bash
curl http://localhost:8000/api/cluster/status
```

#### 2. Submit a Task
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=design%20a%20new%20feature"
```

#### 3. Get Task Result
```bash
# Replace TASK_ID with the task_id from submit response
curl http://localhost:8000/api/cluster/task/TASK_ID
```

#### 4. View Live Agents
```bash
curl http://localhost:8000/api/cluster/agents/live
```

#### 5. Trigger Manual Heal
```bash
curl -X POST http://localhost:8000/api/cluster/heal
```

#### 6. View Healing History
```bash
curl http://localhost:8000/api/cluster/infrastructure/healing-history
```

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Foundry Cluster                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Infrastructure Agent                     │  │
│  │  • Monitors system health (CPU, RAM, Disk)           │  │
│  │  • Auto-heals infrastructure issues                   │  │
│  │  • Restarts failed services (Redis, etc.)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Worker Pool Manager                      │  │
│  │  • Health monitoring loop (every 10s)                │  │
│  │  • Auto-restart dead workers                          │  │
│  │  • Task distribution via Redis queues                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Architect  │ │    Coder    │ │  Executor   │          │
│  │   Worker    │ │   Worker    │ │   Worker    │          │
│  │  (Process)  │ │  (Process)  │ │  (Process)  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                               │
│  ┌─────────────┐ ┌─────────────┐                           │
│  │   Critic    │ │  Deployer   │                           │
│  │   Worker    │ │   Worker    │                           │
│  │  (Process)  │ │  (Process)  │                           │
│  └─────────────┘ └─────────────┘                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Redis Queue                        │  │
│  │  • Task queues: tasks:architect, tasks:coder, ...    │  │
│  │  • Result queues: results:{task_id}                  │  │
│  │  • Heartbeats: heartbeat:{worker_id}                 │  │
│  │  • Stats: worker:{worker_id}                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 Configuration

#### Redis Connection
- Host: `localhost`
- Port: `6379`
- Heartbeat TTL: `30 seconds`
- Result TTL: `5 minutes`

#### Health Thresholds
- **CPU Warning:** > 90%
- **Memory Critical:** > 85%
- **Disk Critical:** > 90%
- **Heartbeat Timeout:** 60 seconds

#### Worker Pool
- **Total Workers:** 5
- **Health Check Interval:** 10 seconds
- **Task Timeout:** 5 seconds (blocking pop)
- **Restart Timeout:** 5 seconds

### 🛠️ Troubleshooting

#### Redis Not Running
```bash
# Check if Redis is running
redis-cli ping

# Start Redis manually
redis-server --daemonize yes

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

#### Workers Not Starting
```bash
# Check backend logs for errors
cd /workspace/backend
python -m uvicorn main:app --reload

# Look for "Started {agent_type} worker" messages
```

#### Frontend Not Connecting
```bash
# Ensure backend is running on port 8000
curl http://localhost:8000/health

# Check CORS settings in backend/main.py
# Default: allow_origins=["*"]
```

### 📈 Monitoring

The system provides comprehensive monitoring through:

1. **Health Endpoint:** `/health`
   - Cluster initialization status
   - Infrastructure agent status

2. **Cluster Status:** `/api/cluster/status`
   - Complete cluster state
   - Worker health
   - System metrics
   - Infrastructure permissions

3. **Live Agents:** `/api/cluster/agents/live`
   - Real-time agent status
   - Task counts and errors
   - Process IDs and uptimes

4. **Metrics:** `/api/cluster/metrics`
   - Detailed system metrics
   - Redis statistics
   - Worker statistics

### 🎯 Next Steps

1. **Deploy to Codespaces:** The system is designed to run in GitHub Codespaces
2. **Add Custom Agents:** Extend `_execute_task()` in worker_pool.py
3. **Integrate with LLMs:** Connect agents to OpenAI, Anthropic, etc.
4. **Add Persistence:** Store task history in database
5. **Scale Workers:** Add more workers per agent type

### 🔥 Self-Healing in Action

The system will automatically:
- ✅ Restart crashed agent workers
- ✅ Clear memory when usage is high
- ✅ Cleanup disk space when low
- ✅ Restart Redis if it goes down
- ✅ Track all healing actions for debugging

**All systems operational and ready to go! 🚀**
