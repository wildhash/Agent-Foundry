"""
Persistent Agent Worker Pool with Self-Healing
Agents run continuously in separate processes
"""

import asyncio
import multiprocessing
import json
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class AgentWorker:
    """Persistent agent worker that runs in separate process"""
    
    def __init__(self, agent_type: str, agent_id: str):
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.process: Optional[multiprocessing.Process] = None
        self.status = "initializing"
        self.task_count = 0
        self.error_count = 0
        self.last_heartbeat = None
        self.started_at = None
        self.performance_score = 1.0
        
    def start(self):
        """Start the agent worker process"""
        self.process = multiprocessing.Process(
            target=self._run_worker,
            name=f"{self.agent_type}_{self.agent_id}",
            daemon=True
        )
        self.process.start()
        self.status = "running"
        self.started_at = datetime.now()
        self.last_heartbeat = datetime.now()
        logger.info(f"✅ Started {self.agent_type} worker (PID: {self.process.pid})")
        
    def _run_worker(self):
        """Worker process main loop - STAYS ALIVE FOREVER"""
        # Import inside worker to avoid pickling issues
        import redis
        
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            logger.info(f"🤖 {self.agent_type} worker {self.agent_id} started (PID: {multiprocessing.current_process().pid})")
            
            while True:
                try:
                    # Pull tasks from Redis queue (blocking with 5s timeout)
                    task = r.blpop(f"tasks:{self.agent_type}", timeout=5)
                    
                    if task:
                        task_data = json.loads(task[1])
                        logger.info(f"🎯 {self.agent_type} processing task: {task_data.get('task_id', 'unknown')}")
                        
                        result = self._execute_task(task_data)
                        
                        # Push result back
                        r.rpush(f"results:{task_data['task_id']}", json.dumps(result))
                        r.expire(f"results:{task_data['task_id']}", 300)  # 5 min TTL
                        
                        # Update stats
                        r.hincrby(f"worker:{self.agent_id}", "task_count", 1)
                        
                    # Send heartbeat every iteration
                    r.setex(
                        f"heartbeat:{self.agent_id}",
                        30,  # 30 second TTL
                        str(time.time())
                    )
                        
                except Exception as e:
                    logger.error(f"❌ {self.agent_type} worker error: {e}")
                    # Self-heal: increment error counter but keep running
                    try:
                        r.hincrby(f"worker:{self.agent_id}", "error_count", 1)
                    except Exception:
                        # Ignore errors updating error_count in Redis to ensure worker stays alive
                        pass
                    time.sleep(1)  # Brief pause before continuing
                    
        except Exception as e:
            logger.critical(f"💀 {self.agent_type} worker crashed: {e}")
                
    def _execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific task"""
        # Simulated execution - replace with actual agent logic
        time.sleep(0.5)  # Simulate work
        
        return {
            "task_id": task_data.get("task_id"),
            "status": "completed",
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "result": f"Task processed by {self.agent_type}",
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": 500
        }
        
    def is_healthy(self) -> bool:
        """Check if worker is healthy"""
        if not self.process or not self.process.is_alive():
            return False
            
        # Check heartbeat via Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            heartbeat = r.get(f"heartbeat:{self.agent_id}")
            
            if heartbeat:
                heartbeat_age = time.time() - float(heartbeat)
                return heartbeat_age < 60  # Healthy if heartbeat < 60s old
            return False
        except:
            return False
        
    def restart(self):
        """Restart dead worker - SELF HEALING!"""
        logger.warning(f"♻️ Restarting {self.agent_type} worker {self.agent_id}")
        
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()
            
        self.status = "restarting"
        self.start()
        logger.info(f"✅ Self-healed {self.agent_type} worker")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics from Redis"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            stats = r.hgetall(f"worker:{self.agent_id}")
            return {
                "task_count": int(stats.get("task_count", 0)),
                "error_count": int(stats.get("error_count", 0))
            }
        except:
            return {"task_count": 0, "error_count": 0}


class AgentPool:
    """Manages pool of persistent agent workers with self-healing"""
    
    def __init__(self):
        self.workers: Dict[str, AgentWorker] = {}
        self.health_check_task = None
        self.is_initialized = False
        
    async def initialize(self):
        """Spawn initial worker pool"""
        if self.is_initialized:
            logger.warning("Agent pool already initialized")
            return
            
        logger.info("🚀 Initializing Agent Foundry Worker Pool...")
        
        agent_types = ["architect", "coder", "executor", "critic", "deployer"]
        
        for agent_type in agent_types:
            worker_id = f"{agent_type}_001"
            worker = AgentWorker(agent_type, worker_id)
            worker.start()
            self.workers[worker_id] = worker
            
        # Start health monitoring loop
        self.health_check_task = asyncio.create_task(self._monitor_health())
        self.is_initialized = True
        
        logger.info(f"✅ Spawned {len(self.workers)} agent workers")
        
    async def _monitor_health(self):
        """Continuously monitor worker health - SELF HEALING LOOP"""
        logger.info("🏥 Health monitor started")
        
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            for worker_id, worker in list(self.workers.items()):
                if not worker.is_healthy():
                    logger.warning(f"💀 Worker {worker_id} is unhealthy!")
                    worker.restart()  # AUTO-RESTART!
                    
    async def submit_task(self, agent_type: str, task_data: Dict) -> str:
        """Submit task to agent worker pool"""
        import redis
        
        task_id = task_data.get('task_id') or str(uuid.uuid4())
        task_data['task_id'] = task_id
        task_data['submitted_at'] = datetime.now().isoformat()
        
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.rpush(f"tasks:{agent_type}", json.dumps(task_data))
        
        logger.info(f"📤 Submitted task {task_id} to {agent_type}")
        return task_id
        
    async def get_result(self, task_id: str, timeout: int = 30) -> Optional[Dict]:
        """Wait for task result with timeout"""
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        result = r.blpop(f"results:{task_id}", timeout=timeout)
        if result:
            return json.loads(result[1])
        return None
        
    def get_status(self) -> Dict[str, Any]:
        """Get complete cluster status"""
        import psutil
        
        healthy_count = sum(1 for w in self.workers.values() if w.is_healthy())
        
        return {
            "cluster": {
                "total_workers": len(self.workers),
                "healthy_workers": healthy_count,
                "unhealthy_workers": len(self.workers) - healthy_count,
                "initialized": self.is_initialized
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "uptime_seconds": time.time() - psutil.boot_time()
            },
            "workers": {
                worker_id: {
                    "type": worker.agent_type,
                    "status": worker.status,
                    "pid": worker.process.pid if worker.process else None,
                    "healthy": worker.is_healthy(),
                    "started_at": worker.started_at.isoformat() if worker.started_at else None,
                    **worker.get_stats()
                }
                for worker_id, worker in self.workers.items()
            }
        }
        
    async def shutdown(self):
        """Graceful shutdown of all workers"""
        logger.info("🛑 Shutting down agent pool...")
        
        if self.health_check_task:
            self.health_check_task.cancel()
            
        for worker in self.workers.values():
            if worker.process and worker.process.is_alive():
                worker.process.terminate()
                worker.process.join(timeout=3)
                if worker.process.is_alive():
                    worker.process.kill()
                    
        self.workers.clear()
        self.is_initialized = False
        logger.info("✅ All workers terminated")


# Global singleton instance
agent_pool = AgentPool()
