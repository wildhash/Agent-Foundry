# Agent Foundry Setup Guide

## Prerequisites

### Required Software
- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **Git**: [Download Git](https://git-scm.com/)

### Optional (Recommended for Production)
- **Redis**: For caching and session management
- **PostgreSQL**: For persistent data storage
- **Docker**: For containerized deployment

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/wildhash/Agent-Foundry.git
cd Agent-Foundry
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend
python -m venv venv

# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment

Create `.env` file in `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration (see Environment Variables section below).

#### Start Backend Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment

Create `.env.local` file in `frontend/` directory:

```bash
cp .env.example .env.local
```

#### Start Development Server

```bash
npm run dev
```

Dashboard will be available at: `http://localhost:3000`

#### Build for Production

```bash
npm run build
npm start
```

## Environment Variables

### Backend (`backend/.env`)

```env
# ============================================
# Application Settings
# ============================================
APP_NAME=Agent Foundry
DEBUG=False

# ============================================
# API Keys (Replace with your actual keys)
# ============================================
FASTINO_API_KEY=your_fastino_api_key_here
FREEPIK_API_KEY=your_freepik_api_key_here
FRONTEGG_API_KEY=your_frontegg_api_key_here
AIRIA_API_KEY=your_airia_api_key_here

# ============================================
# CORS Settings
# ============================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ============================================
# Database Configuration
# ============================================
# SQLite (Development)
DATABASE_URL=sqlite:///./agent_foundry.db

# PostgreSQL (Production)
# DATABASE_URL=postgresql://user:password@localhost:5432/agentfoundry

# ============================================
# Redis Configuration
# ============================================
REDIS_URL=redis://localhost:6379

# ============================================
# Agent Configuration
# ============================================
MAX_REFLEXION_LOOPS=5
PERFORMANCE_THRESHOLD=0.75
EVOLUTION_THRESHOLD=0.85

# ============================================
# Fastino TLM Settings
# ============================================
FASTINO_INFERENCE_SPEED_MULTIPLIER=99
FASTINO_BATCH_SIZE=32
FASTINO_MAX_TOKENS=2048

# ============================================
# LiquidMetal Raindrop Settings
# ============================================
RAINDROP_AUTO_HEAL=True
RAINDROP_MAX_ATTEMPTS=3
RAINDROP_HEAL_TIMEOUT=30
```

### Frontend (`frontend/.env.local`)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=Agent Foundry
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Optional Services

### Redis Setup

#### macOS (Homebrew)
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

#### Docker
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### PostgreSQL Setup

#### macOS (Homebrew)
```bash
brew install postgresql
brew services start postgresql
createdb agentfoundry
```

#### Ubuntu/Debian
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb agentfoundry
```

#### Docker
```bash
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_DB=agentfoundry \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  --name postgres \
  postgres:15-alpine
```

## Docker Setup (Recommended for Production)

### 1. Create Dockerfile for Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create Dockerfile for Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

CMD ["npm", "start"]
```

### 3. Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/agentfoundry
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=agentfoundry
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

Access:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Verification

### 1. Test Backend

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

curl http://localhost:8000/
# Expected: {"name":"Agent Foundry","version":"1.0.0","description":"..."}
```

### 2. Test Frontend

Open browser and navigate to `http://localhost:3000`

You should see the Agent Foundry dashboard.

### 3. Run API Tests

```bash
python test_api.py
```

All tests should pass with ✅.

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**Module not found errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
# Reinstall dependencies
pip install -r requirements.txt
```

**Database connection errors:**
- Check DATABASE_URL is correct
- Ensure PostgreSQL/SQLite is accessible
- Verify credentials

### Frontend Issues

**Port 3000 already in use:**
```bash
# Find and kill process
lsof -i :3000
kill -9 <PID>
```

**Module not found:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API connection errors:**
- Verify backend is running
- Check NEXT_PUBLIC_API_URL in .env.local
- Ensure CORS is configured correctly

### Common Issues

**CORS errors:**
- Add frontend URL to CORS_ORIGINS in backend .env
- Restart backend after changes

**Performance issues:**
- Increase uvicorn workers
- Enable Redis caching
- Use production build for frontend

## Next Steps

1. **Read Documentation**
   - [Architecture](./ARCHITECTURE.md)
   - [Examples](./EXAMPLES.md)
   - [API Reference](http://localhost:8000/docs)

2. **Try Examples**
   ```bash
   cd Agent-Foundry
   python test_api.py
   ```

3. **Build Your First Pipeline**
   ```python
   import requests
   
   response = requests.post('http://localhost:8000/api/agents/pipeline', json={
       'description': 'Your task here',
       'requirements': ['Requirement 1', 'Requirement 2']
   })
   ```

4. **Monitor Performance**
   - Open dashboard at http://localhost:3000
   - Check metrics and evolution tree
   - Monitor agent improvements

## Support

- GitHub Issues: https://github.com/wildhash/Agent-Foundry/issues
- Documentation: https://github.com/wildhash/Agent-Foundry/wiki
