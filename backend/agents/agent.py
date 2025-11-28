"""
ADK CLI Entry Point

This file is required by ADK CLI when running:
    adk run agents
    adk web agents

ADK CLI specifically looks for the 'root_agent' variable.
"""

from .mcp_hub_agent import root_agent

__all__ = ["root_agent"]
