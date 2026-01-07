"""
Sandboxed code execution using Docker
"""

import asyncio
import hashlib
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    memory_used_bytes: Optional[int] = None


class SandboxService:
    """Execute code safely in Docker containers"""

    def __init__(self):
        self.timeout = int(os.getenv("EXECUTION_TIMEOUT", "30"))
        self.memory_limit = os.getenv("EXECUTION_MEMORY", "256m")
        self.cpu_quota = int(
            os.getenv("EXECUTION_CPU_QUOTA", "50000")
        )  # 50% of one CPU

        try:
            import docker

            self.client = docker.from_env()
            self.available = True
            logger.info("Docker sandbox initialized")
        except Exception as e:
            self.client = None
            self.available = False
            logger.warning(f"Docker not available, using mock execution: {e}")

    async def execute_python(self, code: str) -> ExecutionResult:
        """Execute Python code in sandboxed container"""
        if not self.available:
            return await self._mock_execute(code)

        start_time = time.time()

        # Write code to temp file
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:8]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, prefix=f"exec_{code_hash}_"
        ) as f:
            f.write(code)
            code_path = f.name

        try:
            # Run in container
            container = self.client.containers.run(
                image="python:3.11-slim",
                command=["python", "/code/script.py"],
                volumes={code_path: {"bind": "/code/script.py", "mode": "ro"}},
                mem_limit=self.memory_limit,
                cpu_period=100000,
                cpu_quota=self.cpu_quota,
                network_disabled=True,  # No network access
                detach=True,
                remove=False,
            )

            try:
                # Wait for completion with timeout
                result = container.wait(timeout=self.timeout)
                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )
                exit_code = result["StatusCode"]
            except Exception as e:
                # Timeout or other error
                container.kill()
                stdout = ""
                stderr = f"Execution timeout after {self.timeout}s or error: {str(e)}"
                exit_code = -1
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

            execution_time = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                success=(exit_code == 0),
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=execution_time,
            )

        finally:
            # Clean up temp file
            try:
                os.unlink(code_path)
            except Exception:
                pass

    async def _mock_execute(self, code: str) -> ExecutionResult:
        """Mock execution when Docker is not available"""
        await asyncio.sleep(0.1)  # Simulate execution time

        # Basic syntax check
        try:
            compile(code, "<string>", "exec")
            return ExecutionResult(
                success=True,
                stdout=f"[MOCK] Code compiled successfully ({len(code)} chars)",
                stderr="",
                exit_code=0,
                execution_time_ms=100,
            )
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"[MOCK] SyntaxError: {e}",
                exit_code=1,
                execution_time_ms=100,
            )


# Singleton
sandbox_service = SandboxService()
