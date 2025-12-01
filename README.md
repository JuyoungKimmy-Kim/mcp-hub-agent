# MCP Hub Agent

AI chatbot agent for MCP Hub platform, built with Google ADK (Agent Development Kit).

## Overview

This agent helps users discover and interact with MCP (Model Context Protocol) servers through natural language conversations. It integrates with MCP Hub's data sources via MCP protocol and supports multiple LLM providers.

## Features

- **Multi-LLM Support**: Gemini 2.0 Flash (dev) / GPT-OSS-120B (prod)
- **MCP Integration**: Connects to MCP servers via SSE transport
- **Extensible Tools**: Modular architecture for multiple MCP toolsets
- **Session Management**: Built-in conversation history tracking
- **Streaming Responses**: Real-time response generation

## Requirements

- Python 3.10+
- Google ADK 1.19.0+
- API Keys:
  - `GOOGLE_API_KEY` (for Gemini)
  - `OPENAI_API_KEY` (for GPT-OSS-120B, optional)

## Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and set your API keys
```

## Configuration

Key environment variables in `backend/.env`:

```bash
# LLM Configuration
APP_ENV=development                    # development | production
GOOGLE_API_KEY=your-google-api-key     # For Gemini (dev)
OPENAI_API_KEY=your-openai-api-key     # For GPT-OSS-120B (prod)
OPENAI_BASE_URL=https://your-llm-endpoint/v1  # Optional: Custom LLM endpoint

# MCP Servers
MCP_HUB_SERVER_URL_DEV=http://localhost:10004
```

## Usage

### Run with ADK CLI

```bash
cd backend
adk run agents
```

### Run with FastAPI

```bash
cd backend
python main.py
```

### Run Tests

```bash
python test_mcp_connection.py
```

## Architecture

```
Agent (LlmAgent)
├── Model: Gemini 2.0 Flash / GPT-OSS-120B
├── Instructions: backend/agents/instructions.md
└── Tools: MCPToolset[]
    └── MCP Hub MCP Server (SSE)
```

### Agent Components

- **backend/agents/mcp_hub_agent.py**: Root agent definition
- **backend/services/agent_service.py**: Agent execution runtime
- **backend/config/settings.py**: Environment configuration

### Adding MCP Tools

Edit `backend/agents/mcp_hub_agent.py`:

```python
def _get_mcp_tools() -> list:
    toolsets = []

    # MCP Hub
    toolsets.append(MCPToolset(
        connection_params=SseConnectionParams(url="http://localhost:10004")
    ))

    # Add more MCP servers here
    # toolsets.append(MCPToolset(...))

    return toolsets
```