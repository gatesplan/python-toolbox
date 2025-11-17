"""
Window strategy implementations
"""

from .WindowBase import WindowBase
from .FixedWindow import FixedWindow
from .SlidingWindow import SlidingWindow

__all__ = ["WindowBase", "FixedWindow", "SlidingWindow"]
