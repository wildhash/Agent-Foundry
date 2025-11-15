# 🤖 Agent Foundry Self-Healing Cluster

## 🎯 What is This?

A **production-ready, self-healing agent system** where:
- ✅ **5 specialized agents** run as persistent workers in separate processes
- ✅ **Automatic health monitoring** checks workers every 10 seconds
- ✅ **Self-healing** automatically restarts crashed workers
- ✅ **Infrastructure monitoring** detects and fixes system issues (memory, disk, Redis)
- ✅ **Real-time dashboard** shows live cluster status
- ✅ **Task queue system** powered by Redis for reliable job distribution

## 🚀 Quick Start (2 Commands)

### Start Backend
```bash
./start_backend.sh
```

### Start Frontend (in another terminal)
```bash
cd frontend && npm run dev
```

**Dashboard:** http://localhost:3000/cluster  
**API Docs:** http://localhost:8000/docs

## 📦 Installation

If this is your first time:

```bash
# Run setup (installs dependencies)
./setup.sh

# Run system tests
./TEST_SYSTEM.sh
```

## 🏗️ What's Included

### Backend (`/backend`)
- **`agents/worker_pool.py`** - Persistent worker pool with multiprocessing
- **`agents/infrastructure_agent.py`** - System health monitoring & auto-healing
- **`routers/cluster.py`** - REST API endpoints for cluster management
- **`main.py`** - FastAPI app with lifecycle management

### Frontend (`/frontend`)
- **`components/ClusterDashboard.tsx`** - Real-time monitoring dashboard
- **`app/cluster/page.tsx`** - Cluster page route

### Scripts
- **`setup.sh`** - One-time setup (Redis, dependencies)
- **`start_backend.sh`** - Start backend server
- **`TEST_SYSTEM.sh`** - Verify installation

## 🔥 Key Features

### 1. Self-Healing Workers
Workers automatically restart when they:
- Crash or exit unexpectedly
- Stop sending heartbeats (>60s)
- Become unresponsive

### 2. Infrastructure Auto-Healing
Automatically fixes:
- **High Memory (>85%)** → Clears system caches
- **High Disk (>90%)** → Cleans temp files
- **Redis Down** → Restarts Redis service

### 3. Real-Time Monitoring
Dashboard shows:
- Live worker status (green/red indicators)
- System health (CPU, Memory, Disk)
- Task completion counts
- Error tracking
- Worker PIDs and uptimes

### 4. Task Distribution
Submit tasks to specialized agents:
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=design%20auth%20system"
```

Agents:
- `architect` - System design
- `coder` - Code generation
- `executor` - Task execution
- `critic` - Quality assurance
- `deployer` - Deployment

## 📊 API Endpoints

### Cluster Management
- `GET /api/cluster/status` - Complete cluster state
- `GET /api/cluster/agents/live` - Real-time agent status
- `GET /api/cluster/metrics` - Detailed metrics
- `POST /api/cluster/heal` - Manual self-heal trigger

### Task Management
- `POST /api/cluster/task/submit` - Submit task to agent
- `GET /api/cluster/task/{task_id}` - Get task result

### Infrastructure
- `GET /api/cluster/infrastructure/healing-history` - View healing actions

### Health
- `GET /health` - Basic health check
- `GET /` - Cluster overview

## 🧪 Testing

### Run System Tests
```bash
./TEST_SYSTEM.sh
```

Tests verify:
- ✅ Redis installation and connectivity
- ✅ Python dependencies
- ✅ Module imports
- ✅ File structure
- ✅ Permissions

### Manual Testing

#### 1. Check Cluster Status
```bash
curl http://localhost:8000/api/cluster/status | python3 -m json.tool
```

#### 2. Submit Test Task
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=test"
```

#### 3. Check Redis
```bash
redis-cli ping  # Should return PONG
redis-cli LLEN tasks:architect  # Check queue length
```

#### 4. Simulate Worker Failure
```bash
# Get PID from dashboard
kill -9 <PID>

# Watch it auto-restart in ~10 seconds
# Check logs or dashboard
```

## 🛠️ Architecture

```
┌─────────────────────────────────────────────────┐
│          FastAPI Backend (Port 8000)            │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │    Infrastructure Agent (Self-Healing)    │ │
│  │  • CPU/Memory/Disk monitoring            │ │
│  │  • Auto-heal system issues               │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │    Worker Pool Manager                    │ │
│  │  • Health checks every 10s               │ │
│  │  • Auto-restart dead workers             │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
                     ↕ Redis Queues
┌─────────────────────────────────────────────────┐
│            Redis (Port 6379)                    │
│  • Task queues                                  │
│  • Result queues                                │
│  • Heartbeats                                   │
│  • Worker stats                                 │
└─────────────────────────────────────────────────┘
                     ↕ Process Pool
┌─────────────────────────────────────────────────┐
│        5 Agent Workers (Separate Processes)     │
│  • architect_001  → PID xxxxx                  │
│  • coder_001      → PID xxxxx                  │
│  • executor_001   → PID xxxxx                  │
│  • critic_001     → PID xxxxx                  │
│  • deployer_001   → PID xxxxx                  │
└─────────────────────────────────────────────────┘
                     ↕ Real-time Updates
┌─────────────────────────────────────────────────┐
│          Next.js Frontend (Port 3000)           │
│  • Live dashboard (polls every 2s)             │
│  • System health visualization                 │
│  • Manual heal trigger                         │
└─────────────────────────────────────────────────┘
```

## 📈 Monitoring

### Dashboard Metrics
- **Cluster Summary**: Total/Healthy/Unhealthy workers
- **System Health**: CPU, Memory, Disk with color-coded bars
- **Worker Table**: Status, PID, Tasks, Errors, Uptime

### Log Monitoring
Backend logs show:
```
✅ Started architect worker (PID: 12345)
🎯 architect processing task: abc-123
🏥 Health monitor started
♻️ Restarting coder worker coder_001
✅ Self-healed coder worker
```

## 🔧 Configuration

### Redis Settings
- Host: `localhost`
- Port: `6379`
- Heartbeat TTL: `30 seconds`
- Result TTL: `5 minutes`

### Health Thresholds
- CPU Warning: `> 90%`
- Memory Critical: `> 85%`
- Disk Critical: `> 90%`
- Heartbeat Timeout: `60 seconds`

### Worker Pool
- Total Workers: `5`
- Health Check Interval: `10 seconds`
- Task Poll Timeout: `5 seconds`

## 🚨 Troubleshooting

### Backend Won't Start
```bash
# Check Python dependencies
cd backend
pip3 install -r requirements.txt

# Verify imports work
python3 -c "from agents.worker_pool import agent_pool"
```

### Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Start Redis if needed
redis-server --daemonize yes
```

### Workers Not Appearing
```bash
# Check backend logs for errors
# Ensure Redis is running
# Verify no port conflicts
```

### Frontend Can't Connect
```bash
# Ensure backend is running on port 8000
curl http://localhost:8000/health

# Check for CORS issues (should be allowed in development)
```

## 📚 Documentation

- **`CLUSTER_SETUP.md`** - Detailed setup and architecture
- **`DEPLOYMENT.md`** - Production deployment guide
- **`README_CLUSTER.md`** - This file (quick reference)

## 🎓 Next Steps

1. **Customize Agents**: Edit `_execute_task()` in `worker_pool.py`
2. **Add LLM Integration**: Connect to OpenAI/Anthropic/etc.
3. **Scale Workers**: Increase worker count per agent type
4. **Add Persistence**: Store task history in database
5. **Deploy to Production**: Use Docker/Kubernetes

## 🎯 Example Use Cases

### Automated Code Generation
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=coder&description=create%20REST%20API%20for%20user%20management"
```

### System Design
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=design%20microservices%20architecture"
```

### Quality Review
```bash
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=critic&description=review%20code%20quality"
```

## 🆘 Support

If you encounter issues:
1. Run `./TEST_SYSTEM.sh` to verify setup
2. Check logs in terminal output
3. Verify Redis is running: `redis-cli ping`
4. Ensure ports 3000 and 8000 are available
5. Review `DEPLOYMENT.md` for detailed troubleshooting

## 📦 Files Created

```
/workspace/
├── backend/
│   ├── agents/
│   │   ├── worker_pool.py          ✅ Worker pool + self-healing
│   │   └── infrastructure_agent.py ✅ System monitoring
│   ├── routers/
│   │   └── cluster.py              ✅ API endpoints
│   ├── main.py                     ✅ FastAPI app (updated)
│   └── requirements.txt            ✅ Dependencies (updated)
├── frontend/
│   ├── app/cluster/
│   │   └── page.tsx                ✅ Cluster page
│   └── components/
│       └── ClusterDashboard.tsx    ✅ Dashboard UI
├── setup.sh                        ✅ One-time setup
├── start_backend.sh                ✅ Backend launcher
├── TEST_SYSTEM.sh                  ✅ System verification
├── CLUSTER_SETUP.md               ✅ Detailed docs
├── DEPLOYMENT.md                  ✅ Deployment guide
└── README_CLUSTER.md              ✅ This file
```

## ✅ Verification

Run this checklist:
- [ ] Redis is running (`redis-cli ping`)
- [ ] Backend starts without errors
- [ ] All 5 workers spawn (check logs)
- [ ] Dashboard loads at http://localhost:3000/cluster
- [ ] API docs work at http://localhost:8000/docs
- [ ] Can submit tasks via API
- [ ] Workers show as healthy (green indicators)
- [ ] Manual heal button works

---

**🎉 System Ready! Your self-healing agent cluster is operational.**

Start building with:
```bash
./start_backend.sh
cd frontend && npm run dev
```

Then open: http://localhost:3000/cluster
