"""
Sponsor integration layer for Agent Foundry
- ClaudeIntegration: REQUIRED - Core thinking engine using Anthropic API  
- Others: OPTIONAL - Graceful degradation if unavailable
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)


# ============================================================================
# REQUIRED INTEGRATION: Claude/Anthropic
# ============================================================================

class ClaudeIntegration:
    """
    Required integration for Claude AI (Anthropic)
    Provides the core thinking capabilities for agents
    """
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude integration
        
        Args:
            api_key: Anthropic API key (required)
            model: Claude model to use
        """
        if not api_key or api_key == "":
            raise ValueError("ANTHROPIC_API_KEY is required for Claude integration")
            
        self.api_key = api_key
        self.model = model
        self.client = None
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"Claude integration initialized with model: {model}")
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Claude client: {e}")
    
    async def think(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system: Optional[str] = None
    ) -> str:
        """
        Core thinking method - sends prompts to Claude and gets responses
        
        Args:
            prompt: The prompt/question for Claude
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 to 1.0)
            system: Optional system prompt
            
        Returns:
            Claude's response text
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system:
                kwargs["system"] = system
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(**kwargs)
            )
            
            # Extract text from response
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def batch_think(
        self,
        prompts: List[str],
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> List[str]:
        """
        Process multiple prompts (sequentially for now)
        
        Args:
            prompts: List of prompts
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature
            
        Returns:
            List of responses
        """
        responses = []
        for prompt in prompts:
            response = await self.think(prompt, max_tokens, temperature)
            responses.append(response)
        return responses


# ============================================================================
# OPTIONAL INTEGRATIONS: Graceful degradation if unavailable
# ============================================================================

class FastinoIntegration:
    """
    Optional integration for Fastino TLM (99x faster inference)
    Falls back to Claude if unavailable
    """
    
    def __init__(self, api_key: Optional[str] = None, fallback: Optional[ClaudeIntegration] = None):
        """
        Initialize Fastino integration
        
        Args:
            api_key: Fastino API key (optional)
            fallback: Claude integration to use as fallback
        """
        self.api_key = api_key
        self.fallback = fallback
        self.available = api_key is not None and api_key != ""
        
        if self.available:
            logger.info("Fastino integration available")
        else:
            logger.warning("Fastino integration unavailable, will use fallback")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using Fastino or fallback to Claude
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        if not self.available:
            if self.fallback:
                logger.debug("Using Claude fallback for Fastino")
                return await self.fallback.think(prompt, max_tokens, temperature)
            else:
                raise RuntimeError("Fastino unavailable and no fallback configured")
        
        # Simulate Fastino response (mock for now)
        # In production, this would call actual Fastino API
        await asyncio.sleep(0.01)  # Simulate 99x faster inference
        return f"[Fastino] Response for: {prompt[:50]}..."


class LiquidMetalIntegration:
    """
    Optional integration for LiquidMetal Raindrop (self-healing code)
    Falls back to basic Docker execution if unavailable
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LiquidMetal integration
        
        Args:
            api_key: LiquidMetal/Raindrop API key (optional)
        """
        self.api_key = api_key
        self.available = api_key is not None and api_key != ""
        
        if self.available:
            logger.info("LiquidMetal integration available")
        else:
            logger.warning("LiquidMetal unavailable, using Docker fallback")
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute code with self-healing or Docker fallback
        
        Args:
            code: Source code to execute
            language: Programming language
            timeout: Execution timeout in seconds
            
        Returns:
            Execution result dictionary
        """
        if not self.available:
            return await self._docker_fallback(code, language, timeout)
        
        # Simulate LiquidMetal execution (mock for now)
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "output": "[LiquidMetal] Execution completed",
            "healed": False,
            "exit_code": 0
        }
    
    async def _docker_fallback(
        self,
        code: str,
        language: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Fallback execution using Docker SDK
        
        Args:
            code: Source code
            language: Programming language
            timeout: Timeout in seconds
            
        Returns:
            Execution result
        """
        try:
            import docker
            client = docker.from_env()
            
            # Determine image based on language
            images = {
                "python": "python:3.11-slim",
                "node": "node:18-alpine",
                "go": "golang:1.21-alpine"
            }
            image = images.get(language, "python:3.11-slim")
            
            # Create temporary file for code
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{language}', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            try:
                # Run in container with resource limits
                logger.info(f"Executing {language} code in Docker container")
                container = client.containers.run(
                    image,
                    f"python {os.path.basename(code_file)}" if language == "python" else code,
                    volumes={os.path.dirname(code_file): {'bind': '/app', 'mode': 'rw'}},
                    working_dir='/app',
                    mem_limit='512m',
                    detach=True,
                    remove=True
                )
                
                # Wait for completion with timeout
                container.wait(timeout=timeout)
                logs = container.logs().decode('utf-8')
                
                return {
                    "success": True,
                    "output": logs,
                    "healed": False,
                    "exit_code": 0,
                    "method": "docker_fallback"
                }
                
            finally:
                # Cleanup
                if os.path.exists(code_file):
                    os.unlink(code_file)
                    
        except ImportError:
            logger.error("Docker SDK not available for fallback execution")
            return {
                "success": False,
                "output": "Docker SDK not available",
                "error": "Missing docker package",
                "exit_code": -1
            }
        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            return {
                "success": False,
                "output": str(e),
                "error": str(e),
                "exit_code": -1
            }


class FreepikIntegration:
    """
    Optional integration for Freepik AI visual generation
    Gracefully degrades if unavailable
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Freepik integration
        
        Args:
            api_key: Freepik API key (optional)
        """
        self.api_key = api_key
        self.available = api_key is not None and api_key != ""
        
        if self.available:
            logger.info("Freepik integration available")
        else:
            logger.debug("Freepik integration unavailable (optional)")
    
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> Optional[str]:
        """
        Generate AI image or return None if unavailable
        
        Args:
            prompt: Image description
            width: Image width
            height: Image height
            
        Returns:
            Image URL or None
        """
        if not self.available:
            logger.debug("Freepik unavailable, skipping image generation")
            return None
        
        # Simulate image generation (mock for now)
        await asyncio.sleep(0.1)
        return f"https://freepik.ai/generated/{prompt[:20]}.png"


class FronteggIntegration:
    """
    Optional integration for Frontegg authentication
    Placeholder for future implementation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Frontegg integration"""
        self.api_key = api_key
        self.available = api_key is not None and api_key != ""
        
        if self.available:
            logger.info("Frontegg integration available")
        else:
            logger.debug("Frontegg integration unavailable (optional)")


class AiriaIntegration:
    """
    Optional integration for Airia enterprise deployment
    Placeholder for future implementation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Airia integration"""
        self.api_key = api_key
        self.available = api_key is not None and api_key != ""
        
        if self.available:
            logger.info("Airia integration available")
        else:
            logger.debug("Airia integration unavailable (optional)")


# ============================================================================
# Integration Factory
# ============================================================================

def create_integrations(config) -> Dict[str, Any]:
    """
    Factory function to create all integrations with graceful degradation
    
    Args:
        config: Settings configuration object
        
    Returns:
        Dictionary of available integrations
    """
    integrations = {}
    
    # REQUIRED: Claude integration
    try:
        claude = ClaudeIntegration(config.ANTHROPIC_API_KEY)
        integrations['claude'] = claude
        logger.info("✓ Claude integration initialized (REQUIRED)")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Claude (REQUIRED): {e}")
        raise  # Claude is required, so we raise
    
    # OPTIONAL: Fastino with Claude fallback
    try:
        fastino = FastinoIntegration(
            api_key=config.FASTINO_API_KEY,
            fallback=claude
        )
        integrations['fastino'] = fastino
        if fastino.available:
            logger.info("✓ Fastino integration initialized (OPTIONAL)")
    except Exception as e:
        logger.warning(f"Fastino initialization failed (optional): {e}")
    
    # OPTIONAL: LiquidMetal/Raindrop
    try:
        raindrop = LiquidMetalIntegration(config.RAINDROP_API_KEY)
        integrations['liquidmetal'] = raindrop
        if raindrop.available:
            logger.info("✓ LiquidMetal integration initialized (OPTIONAL)")
    except Exception as e:
        logger.warning(f"LiquidMetal initialization failed (optional): {e}")
    
    # OPTIONAL: Freepik
    try:
        freepik = FreepikIntegration(config.FREEPIK_API_KEY)
        integrations['freepik'] = freepik
        if freepik.available:
            logger.info("✓ Freepik integration initialized (OPTIONAL)")
    except Exception as e:
        logger.warning(f"Freepik initialization failed (optional): {e}")
    
    # OPTIONAL: Frontegg
    try:
        frontegg = FronteggIntegration(config.FRONTEGG_API_KEY)
        integrations['frontegg'] = frontegg
        if frontegg.available:
            logger.info("✓ Frontegg integration initialized (OPTIONAL)")
    except Exception as e:
        logger.warning(f"Frontegg initialization failed (optional): {e}")
    
    # OPTIONAL: Airia
    try:
        airia = AiriaIntegration(config.AIRIA_API_KEY)
        integrations['airia'] = airia
        if airia.available:
            logger.info("✓ Airia integration initialized (OPTIONAL)")
    except Exception as e:
        logger.warning(f"Airia initialization failed (optional): {e}")
    
    logger.info(f"Initialized {len(integrations)} integrations")
    return integrations
