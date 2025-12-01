# Google ADK(Agent Development Kit) 개발 가이드

> 실전 프로젝트로 배우는 ADK 기반 AI Agent 개발

## 📋 목차

1. [ADK란 무엇인가?](#adk란-무엇인가)
2. [프로젝트 설정](#프로젝트-설정)
3. [Agent 정의하기](#agent-정의하기)
4. [Agent 실행 인프라 구축](#agent-실행-인프라-구축)
5. [작동 원리 이해하기](#작동-원리-이해하기)
6. [테스트하기](#테스트하기)
7. [다음 단계: Tool 추가](#다음-단계-tool-추가)

---

## ADK란 무엇인가?

**Agent Development Kit (ADK)**는 Google이 만든 AI Agent 개발 프레임워크입니다.

### 🎯 핵심 특징

- **Code-First**: Python 코드로 Agent 로직 정의
- **Model-Agnostic**: Gemini, GPT-OSS-120B 등 다양한 LLM 지원
- **Tool Ecosystem**: 함수, OpenAPI, MCP 등 다양한 도구 통합
- **Multi-Agent System**: 여러 Agent를 조합한 복잡한 워크플로우 구축

### 🤔 왜 ADK를 사용하나?

직접 LLM API를 호출하는 것과 비교:

```python
# ❌ 직접 LLM API 호출
if app_env == "production":
    response = openai.chat.completions.create(
        model="gpt-oss-120b",
        messages=[...],
        # 세션 관리, 도구 호출, 스트리밍 등 직접 구현...
    )
else:
    response = genai.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[...],
        # 다른 API 구조로 또 구현...
    )

# ✅ ADK 사용
runner.run_async(new_message=content)  # 끝!
```

ADK가 제공하는 것:
- ✅ LLM API 추상화 (여러 LLM을 동일한 인터페이스로)
- ✅ 세션 관리 (대화 히스토리 자동 저장/관리)
- ✅ 스트리밍 처리 (실시간 응답)
- ✅ Tool 오케스트레이션 (LLM이 자율적으로 도구 사용)

---

## 프로젝트 설정

### 1. 설치

```bash
# ADK 및 관련 패키지 설치
pip install google-adk==1.19.0
pip install google-generativeai>=0.8.0  # Gemini용
pip install openai>=1.50.0              # GPT용 (선택)
pip install litellm>=1.50.0             # 멀티 LLM 지원
```

### 2. 환경 변수 설정

`.env` 파일:
```bash
# Application
APP_ENV=development
APP_NAME=MCP Hub Agent
APP_VERSION=0.1.0

# LLM API Keys
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # 프로덕션용

# Model Selection
MODEL_NAME_DEV=gemini-2.0-flash-exp
MODEL_NAME_PROD=gpt-oss-120b
```

### 3. 프로젝트 구조

```
backend/
├── agents/
│   ├── __init__.py
│   ├── agent.py              # ADK CLI entry point
│   ├── mcp_hub_agent.py       # Agent 정의
│   └── instructions.md        # System prompt
├── services/
│   └── agent_service.py       # Agent 실행 서비스
├── adk.yaml                   # ADK 설정 파일
└── requirements.txt
```

---

## Agent 정의하기

### 1. System Prompt 작성 (`agents/instructions.md`)

Agent의 역할과 행동 지침을 정의합니다:

```markdown
# MCP Hub Agent Instructions

You are a helpful AI assistant for MCP Hub, a platform that helps developers
discover, share, and manage Model Context Protocol (MCP) servers.

## Your Role

You help users:
- Discover MCP servers and tools
- Understand MCP server features and capabilities
- Get analytics and insights about MCP servers

## Behavior Guidelines

1. **Be Helpful**: Provide clear, concise, and accurate information
2. **Be Proactive**: Suggest relevant MCP servers based on user needs
3. **Be Friendly**: Use a conversational and approachable tone
```

### 2. Agent 정의 (`agents/mcp_hub_agent.py`)

```python
"""
MCP Hub Agent - ADK Standard Format
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Instructions 파일 경로
INSTRUCTIONS_FILE = Path(__file__).parent / "instructions.md"


def _load_instructions() -> str:
    """System prompt 로드"""
    try:
        with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful AI assistant."


def _get_model():
    """
    환경에 맞는 모델 반환

    - 개발: Gemini 2.0 Flash
    - 프로덕션: GPT-OSS-120B
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        # 프로덕션: OpenAI GPT-OSS-120B
        model_name = os.getenv("MODEL_NAME_PROD", "gpt-oss-120b")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for production")

        return LiteLlm(
            model=f"openai/{model_name}",
            api_key=api_key,
        )
    else:
        # 개발: Gemini 2.0 Flash
        model_name = os.getenv("MODEL_NAME_DEV", "gemini-2.0-flash-exp")

        # GOOGLE_API_KEY 환경 변수 설정
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key

        return model_name


# ⭐ ADK Standard Agent Definition
# ADK CLI와 FastAPI 모두 이 Agent를 사용
root_agent = LlmAgent(
    model=_get_model(),                # LLM 선택
    name="mcp_hub_agent",              # Agent 식별자
    instruction=_load_instructions(),   # System prompt
    tools=[],                          # Tools (나중에 추가)
)
```

### 3. ADK CLI Entry Point (`agents/agent.py`)

```python
"""
ADK CLI Entry Point

ADK CLI는 'root_agent' 변수를 찾습니다.
"""

from .mcp_hub_agent import root_agent

__all__ = ["root_agent"]
```

### 4. ADK 설정 파일 (`adk.yaml`)

```yaml
# ADK Configuration File
agents:
  - name: mcp_hub_agent
    path: agents/mcp_hub_agent.py
    description: "MCP Hub chatbot agent"

environment:
  APP_ENV: development
  MODEL_NAME_DEV: gemini-2.0-flash-exp
  MODEL_NAME_PROD: gpt-oss-120b
```

---

## Agent 실행 인프라 구축

### 핵심 개념

ADK에서 Agent를 실행하려면:
1. **Agent** - 설정 정의 (위에서 만듦)
2. **SessionService** - 대화 히스토리 관리
3. **Runner** - Agent 실행 런타임

### Agent Service 구현 (`services/agent_service.py`)

```python
"""
Agent Service - FastAPI에서 사용할 Agent 실행 로직
"""

from typing import AsyncGenerator

from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.config.settings import settings
from backend.utils.logging import LogManager

logger = LogManager.get_logger(__name__)


def get_agent() -> LlmAgent:
    """Agent 인스턴스 반환"""
    from backend.agents.mcp_hub_agent import root_agent
    return root_agent


# 전역 인스턴스 (싱글톤 패턴)
_runner_instance: Runner | None = None
_session_service: InMemorySessionService | None = None


def get_runner() -> Runner:
    """
    Runner 인스턴스 반환 (싱글톤)

    Runner는 Agent를 실행하는 런타임입니다.
    """
    global _runner_instance, _session_service

    if _runner_instance is None:
        agent = get_agent()

        # 1. 세션 서비스 생성 (in-memory)
        if _session_service is None:
            _session_service = InMemorySessionService()

        # 2. Runner 생성
        _runner_instance = Runner(
            agent=agent,
            app_name=settings.APP_NAME,
            session_service=_session_service,
        )

    return _runner_instance


async def run_agent(message: str, user_id: str | None = None) -> str:
    """
    Agent 실행 (동기 응답)

    Args:
        message: 사용자 메시지
        user_id: 사용자 ID (인증된 경우)

    Returns:
        str: Agent 응답
    """
    global _session_service
    runner = get_runner()

    # 사용자 ID 및 세션 ID 설정
    uid = user_id or "anonymous"
    session_id = f"{uid}_session"

    logger.info(f"Running agent for user {uid}")

    try:
        # 1. 세션 생성/가져오기
        session_exists = False
        try:
            session = await _session_service.get_session(
                app_name=settings.APP_NAME,
                user_id=uid,
                session_id=session_id,
            )
            session_exists = session is not None
        except Exception:
            session_exists = False

        if not session_exists:
            logger.info(f"Creating new session for user {uid}")
            await _session_service.create_session(
                app_name=settings.APP_NAME,
                user_id=uid,
                session_id=session_id,
            )

        # 2. 사용자 메시지를 ADK 형식으로 변환
        content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # 3. Agent 실행 (비동기 이터레이터)
        final_response = ""
        async for event in runner.run_async(
            user_id=uid,
            session_id=session_id,
            new_message=content,
        ):
            # 4. 최종 응답 추출
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text"):
                        final_response += part.text

        logger.info(f"Agent response generated ({len(final_response)} chars)")
        return final_response

    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        raise


async def run_agent_stream(
    message: str,
    user_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Agent 실행 (스트리밍 응답)

    실시간으로 응답을 생성하며 yield합니다.
    """
    global _session_service
    runner = get_runner()

    uid = user_id or "anonymous"
    session_id = f"{uid}_session"

    logger.info(f"Running agent (streaming) for user {uid}")

    try:
        # 세션 생성/가져오기 (위와 동일)
        session_exists = False
        try:
            session = await _session_service.get_session(
                app_name=settings.APP_NAME,
                user_id=uid,
                session_id=session_id,
            )
            session_exists = session is not None
        except Exception:
            session_exists = False

        if not session_exists:
            await _session_service.create_session(
                app_name=settings.APP_NAME,
                user_id=uid,
                session_id=session_id,
            )

        # 메시지 변환
        content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Agent 실행 (스트리밍)
        async for event in runner.run_async(
            user_id=uid,
            session_id=session_id,
            new_message=content,
        ):
            # 텍스트 청크 추출 및 yield
            if event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield part.text  # ← 실시간 스트리밍

        logger.info(f"Agent streaming completed for user {uid}")

    except Exception as e:
        logger.error(f"Agent streaming failed: {str(e)}", exc_info=True)
        raise
```

---

## 작동 원리 이해하기

### 전체 실행 흐름

```
┌─────────────────────────────────────────────────────────┐
│ 사용자 요청: "Hello, what is MCP Hub?"                  │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ agent_service.run_agent(message, user_id)               │
│                                                           │
│ 1. Runner 가져오기 (싱글톤)                             │
│    └─> Runner(agent, session_service)                   │
│                                                           │
│ 2. 세션 생성/가져오기                                    │
│    └─> session_id = "user123_session"                   │
│    └─> SessionService에 세션 생성                       │
│                                                           │
│ 3. 메시지를 ADK 형식으로 변환                           │
│    └─> Content(role="user", parts=[Part(text=...)])     │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Runner.run_async(user_id, session_id, new_message)      │
│                                                           │
│ Runner가 하는 일:                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 1. 세션에서 대화 히스토리 가져오기                 │ │
│ │    [이전 메시지들...]                               │ │
│ │                                                      │ │
│ │ 2. System prompt + 히스토리 + 새 메시지 조합       │ │
│ │    System: "You are a helpful AI assistant..."     │ │
│ │    User (과거): "이전 질문"                        │ │
│ │    Assistant (과거): "이전 답변"                   │ │
│ │    User (새): "Hello, what is MCP Hub?"            │ │
│ │                                                      │ │
│ │ 3. LLM API 호출 (Gemini or GPT-OSS-120B)                 │ │
│ │    ├─> google.generativeai.generate_content()     │ │
│ │    └─> 또는 openai.chat.completions.create()      │ │
│ │                                                      │ │
│ │ 4. 응답을 Event 스트림으로 변환                    │ │
│ │    Event { content: Part(text="MCP Hub is...") }  │ │
│ └─────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ agent_service.run_agent()에서 응답 수집                 │
│                                                           │
│ async for event in runner.run_async(...):                │
│     if event.is_final_response():                        │
│         final_response += event.content.parts[0].text    │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 세션에 대화 저장 (자동)                                 │
│ User: "Hello, what is MCP Hub?"                          │
│ Assistant: "MCP Hub is a platform that..."              │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 사용자에게 응답 반환                                     │
│ "MCP Hub is a platform that helps developers..."        │
└─────────────────────────────────────────────────────────┘
```

### 핵심 컴포넌트 역할

#### 1. **Agent** (LlmAgent)
```python
root_agent = LlmAgent(
    model=_get_model(),           # ← 어떤 LLM 사용?
    name="mcp_hub_agent",         # ← Agent 이름
    instruction=_load_instructions(),  # ← 어떻게 행동?
    tools=[],                     # ← 어떤 도구 사용? (나중에)
)
```
- **역할**: Agent의 설정 정의
- **단독으로는 실행 불가** - Runner가 필요!

#### 2. **SessionService** (InMemorySessionService)
```python
_session_service = InMemorySessionService()
```
- **역할**: 대화 히스토리 관리
- **기능**:
  - 세션 생성/조회
  - 메시지 히스토리 저장
  - 사용자별 세션 격리

#### 3. **Runner**
```python
runner = Runner(
    agent=agent,
    app_name=settings.APP_NAME,
    session_service=_session_service,
)
```
- **역할**: Agent 실행 런타임
- **기능**:
  - 세션 히스토리 + 새 메시지 조합
  - LLM API 호출
  - Tool 실행 오케스트레이션 (나중에)
  - 응답을 Event 스트림으로 변환

---

## 테스트하기

### 1. 초기화 테스트

Agent가 제대로 로드되는지 확인:

```python
# test_agent_init.py
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_path)

print("Testing Agent Initialization...")

# Test 1: Import
from backend.agents.mcp_hub_agent import root_agent
print(f"✅ Agent imported: {root_agent.name}")

# Test 2: Configuration
print(f"  - Model: {root_agent.model}")
print(f"  - Tools: {len(root_agent.tools)} configured")
print(f"  - Instruction: {len(root_agent.instruction)} chars")

# Test 3: Agent Service
from backend.services.agent_service import get_agent, get_runner
agent = get_agent()
print(f"✅ Agent service working: {agent.name}")

print("\n✅ All initialization tests passed!")
```

실행:
```bash
python test_agent_init.py
```

### 2. 대화 테스트

실제 LLM 호출 테스트 (API key 필요):

```python
# test_agent_chat.py
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_path)

async def test_conversation():
    # Check API key
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key or google_api_key == "your-google-api-key-here":
        print("⚠️  GOOGLE_API_KEY not configured")
        print("   Set a valid key in backend/.env to test")
        return

    from backend.services.agent_service import run_agent

    # Test conversation
    message = "Hello! What is MCP Hub?"
    print(f"[User]: {message}")
    print("-" * 60)

    response = await run_agent(message)
    print(f"[Agent]: {response}")
    print("-" * 60)
    print("✅ Conversation test successful!")

asyncio.run(test_conversation())
```

실행:
```bash
python test_agent_chat.py
```

### 3. ADK CLI로 테스트

```bash
# 대화형 CLI 실행
cd backend
adk run agents

# 또는 Web UI로 실행
adk web agents
```

---

## 다음 단계: Tool 추가

현재는 **단순 LLM 래핑**입니다. Tool을 추가하면 **진짜 Agent**가 됩니다!

### Tool이 없을 때 vs 있을 때

```python
# 현재 (Tool 없음)
사용자: "가장 인기있는 MCP 서버는?"
Agent: "죄송하지만, 실시간 데이터에 접근할 수 없습니다..."

# Tool 추가 후
사용자: "가장 인기있는 MCP 서버는?"
Agent: [mcp_hub_tool.get_popular_servers() 실행]
      "현재 가장 인기있는 MCP 서버는 filesystem-server입니다.
       1,234개의 다운로드와 4.8점의 평점을 받았습니다..."
```

### Tool 추가 방법

```python
# tools/mcp_hub_tool.py
from google.adk.tools import Tool

class MCPHubTool(Tool):
    """MCP Hub 데이터 조회 도구"""

    def get_popular_servers(self, limit: int = 10) -> list:
        """인기 MCP 서버 조회"""
        # MCP Hub API 호출
        ...

# agents/mcp_hub_agent.py
from backend.tools.mcp_hub_tool import MCPHubTool

mcp_hub_tool = MCPHubTool()

root_agent = LlmAgent(
    model=_get_model(),
    name="mcp_hub_agent",
    instruction=_load_instructions(),
    tools=[mcp_hub_tool],  # ← Tool 추가!
)
```

이제 Agent가:
1. 사용자 질문 분석
2. 필요한 도구 선택 (자율적)
3. 도구 실행
4. 결과를 바탕으로 답변 생성

---

## 🎯 요약

### ADK 개발 핵심 단계

1. **Agent 정의** - LlmAgent(model, instruction, tools)
2. **SessionService** - 대화 히스토리 관리
3. **Runner** - Agent 실행 런타임
4. **run_async()** - 메시지 전달 및 응답 수신

### ADK가 제공하는 가치

- ✅ LLM API 추상화 (Gemini, GPT-OSS-120B 등)
- ✅ 세션 관리 (대화 컨텍스트 유지)
- ✅ 스트리밍 처리 (실시간 응답)
- ✅ Tool 오케스트레이션 (자율 Agent)

### 현재 상태

- ✅ **Phase 1 완료**: 기본 Agent 구조 (LLM 래핑)
- 🔄 **Phase 2 진행 중**: Tool 추가 (진짜 Agent로 진화)

---

## 📚 참고 자료

- [ADK 공식 문서](https://google.github.io/adk-docs/)
- [ADK Python GitHub](https://github.com/google/adk-python)
- [ADK 샘플 코드](https://github.com/google/adk-samples)

---

**작성일**: 2025-12-01
**ADK 버전**: 1.19.0
**프로젝트**: MCP Hub Agent
