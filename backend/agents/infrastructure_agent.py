"""
Self-Healing Infrastructure Agent
Monitors system health and autonomously fixes issues
"""

import asyncio
import psutil
import subprocess
import logging
from typing import Dict, Any, List
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class InfrastructureAgent:
    """
    Meta-agent that monitors and heals the runtime environment.
    Can configure Codespace, install dependencies, restart services.
    """
    
    def __init__(self):
        self.healing_actions_taken: List[Dict] = []
        self.is_running = False
        self.monitor_task = None
        
    async def start(self):
        """Start continuous monitoring"""
        if self.is_running:
            return
            
        logger.info("🔧 Infrastructure Agent starting...")
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
    async def stop(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            
    async def _monitor_loop(self):
        """Main self-healing loop"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                issues = await self._detect_issues()
                
                if issues:
                    logger.warning(f"🚨 Detected {len(issues)} issues")
                    for issue in issues:
                        await self._heal_issue(issue)
                        
            except Exception as e:
                logger.error(f"Infrastructure agent error: {e}")
                
    async def _detect_issues(self) -> List[Dict[str, Any]]:
        """Detect infrastructure issues"""
        issues = []
        
        # Check CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            issues.append({
                "type": "high_cpu",
                "severity": "warning",
                "value": cpu_percent,
                "threshold": 90
            })
            
        # Check memory
        mem_percent = psutil.virtual_memory().percent
        if mem_percent > 85:
            issues.append({
                "type": "high_memory",
                "severity": "critical",
                "value": mem_percent,
                "threshold": 85
            })
            
        # Check disk
        disk_percent = psutil.disk_usage('/').percent
        if disk_percent > 90:
            issues.append({
                "type": "high_disk",
                "severity": "critical",
                "value": disk_percent,
                "threshold": 90
            })
            
        # Check if Redis is running
        if not await self._is_redis_running():
            issues.append({
                "type": "redis_down",
                "severity": "critical"
            })
            
        return issues
        
    async def _is_redis_running(self) -> bool:
        """Check if Redis is accessible"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            return True
        except:
            return False
            
    async def _heal_issue(self, issue: Dict[str, Any]):
        """Heal a detected issue"""
        issue_type = issue["type"]
        
        logger.info(f"🔧 Healing: {issue_type}")
        
        healing_action = {
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "action_taken": None,
            "success": False
        }
        
        try:
            if issue_type == "redis_down":
                success = await self._start_redis()
                healing_action["action_taken"] = "start_redis"
                healing_action["success"] = success
                
            elif issue_type == "high_memory":
                success = await self._clear_memory()
                healing_action["action_taken"] = "clear_memory"
                healing_action["success"] = success
                
            elif issue_type == "high_disk":
                success = await self._cleanup_disk()
                healing_action["action_taken"] = "cleanup_disk"
                healing_action["success"] = success
                
            elif issue_type == "high_cpu":
                logger.warning("High CPU detected - monitoring (no action)")
                healing_action["action_taken"] = "monitor_only"
                healing_action["success"] = True
                
        except Exception as e:
            logger.error(f"Healing failed: {e}")
            healing_action["error"] = str(e)
            
        self.healing_actions_taken.append(healing_action)
        
    async def _start_redis(self) -> bool:
        """Attempt to start Redis"""
        try:
            # Try starting Redis
            result = subprocess.run(
                ["sudo", "systemctl", "start", "redis"],
                capture_output=True,
                timeout=10
            )
            
            await asyncio.sleep(2)
            return await self._is_redis_running()
            
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            return False
            
    async def _clear_memory(self) -> bool:
        """Clear memory caches"""
        try:
            # Clear PageCache, dentries, and inodes
            subprocess.run(
                ["sudo", "sync"],
                timeout=5
            )
            subprocess.run(
                ["sudo", "sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"],
                timeout=5
            )
            logger.info("✅ Cleared memory caches")
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
            
    async def _cleanup_disk(self) -> bool:
        """Clean up disk space"""
        try:
            # Remove old logs
            subprocess.run(
                ["find", "/tmp", "-type", "f", "-mtime", "+1", "-delete"],
                timeout=10
            )
            
            # Clean apt cache if available
            subprocess.run(
                ["sudo", "apt-get", "clean"],
                capture_output=True,
                timeout=10
            )
            
            logger.info("✅ Cleaned up disk space")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup disk: {e}")
            return False
            
    def get_healing_history(self) -> List[Dict[str, Any]]:
        """Get history of healing actions"""
        return self.healing_actions_taken[-50:]  # Last 50 actions
        
    def can_configure_host(self) -> Dict[str, bool]:
        """Check what we have permissions to do"""
        permissions = {
            "sudo": False,
            "systemctl": False,
            "apt": False,
            "disk_cleanup": False
        }
        
        try:
            result = subprocess.run(
                ["sudo", "-n", "echo", "test"],
                capture_output=True,
                timeout=2
            )
            permissions["sudo"] = result.returncode == 0
        except:
            pass
            
        try:
            subprocess.run(["systemctl", "--version"], capture_output=True, timeout=2)
            permissions["systemctl"] = True
        except:
            pass
            
        try:
            subprocess.run(["apt-get", "--version"], capture_output=True, timeout=2)
            permissions["apt"] = True
        except:
            pass
            
        permissions["disk_cleanup"] = shutil.which("find") is not None
        
        return permissions


# Global infrastructure agent
infra_agent = InfrastructureAgent()
