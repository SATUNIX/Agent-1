"""
Compatibility shim: forward all DevAgent references to the single
implementation inside agents.py so we don't maintain two copies.
"""
from agents import DevAgent  # re-export for legacy imports

__all__ = ["DevAgent"]
