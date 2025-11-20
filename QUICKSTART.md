# ⚡ QUICKSTART - Agent Foundry Cluster

## 🚀 Start in 60 Seconds

### Prerequisites Check
```bash
# Verify you have these installed
python3 --version  # Should be 3.8+
node --version     # Should be 18+
npm --version      # Should be 8+
```

### 1️⃣ Setup (One Time Only)
```bash
./setup.sh
```

### 2️⃣ Start Backend (Terminal 1)
```bash
./start_backend.sh
```

Wait for:
```
✅ Cluster online and self-healing enabled
```

### 3️⃣ Start Frontend (Terminal 2)
```bash
cd frontend && npm run dev
```

### 4️⃣ Open Dashboard
```
http://localhost:3000/cluster
```

You should see **5 green workers** 🟢 running!

---

## 🧪 Quick Test

### Verify System
```bash
./TEST_SYSTEM.sh
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Cluster status
curl http://localhost:8000/api/cluster/status

# Submit task
curl -X POST "http://localhost:8000/api/cluster/task/submit?agent_type=architect&description=test"
```

---

## 🔥 Self-Healing Demo

### Kill a worker and watch it restart:
```bash
# Get PID from dashboard
kill -9 <PID>

# Watch logs - it auto-restarts in ~10 seconds!
```

---

## 📚 Full Documentation

- **Quick Reference:** `README_CLUSTER.md`
- **Setup Guide:** `CLUSTER_SETUP.md`
- **Deployment:** `DEPLOYMENT.md`
- **Implementation Details:** `IMPLEMENTATION_COMPLETE.md`

---

## 🆘 Problems?

### Redis not running?
```bash
redis-server --daemonize yes
redis-cli ping  # Should return PONG
```

### Backend errors?
```bash
cd backend
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload
```

### Frontend errors?
```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 What You Get

✅ **5 Self-Healing Agent Workers**  
✅ **Real-Time Monitoring Dashboard**  
✅ **REST API with Swagger Docs**  
✅ **Task Queue System (Redis)**  
✅ **Infrastructure Auto-Healing**  
✅ **Automatic Worker Restart**  

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000/cluster | Live monitoring UI |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI |
| **API Root** | http://localhost:8000/ | Cluster info |
| **Health** | http://localhost:8000/health | Health check |

---

**That's it! Your cluster is running! 🎉**

Start submitting tasks and watch your agents work! 🤖
