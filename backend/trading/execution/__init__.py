"""
Execution Layer

Handles order generation and execution with:
- Smart order routing
- TWAP/VWAP algorithms
- Slippage modeling
- Fill tracking
"""

from .engine import ExecutionEngine
from .algorithms import TWAPAlgorithm, VWAPAlgorithm
from .slippage import SlippageModel

__all__ = [
    "ExecutionEngine",
    "TWAPAlgorithm",
    "VWAPAlgorithm", 
    "SlippageModel",
]
