"""Agent Service

FastAPI backend에서 사용하는 Agent 실행 로직을 제공합니다.
실제 Agent 정의는 backend/agents/mcp_hub_agent.py를 사용합니다.
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
    """
    Agent 인스턴스 반환

    backend/agents/mcp_hub_agent.py에 정의된 표준 Agent를 사용합니다.
    이렇게 하면 ADK CLI와 FastAPI backend가 동일한 Agent를 사용합니다.

    Returns:
        LlmAgent: Agent 인스턴스
    """
    # ADK 표준 Agent import
    from backend.agents.mcp_hub_agent import root_agent

    logger.info("Using ADK standard agent from backend/agents/mcp_hub_agent.py")
    return root_agent


# 전역 Runner 및 세션 서비스 인스턴스 (싱글톤 패턴)
_runner_instance: Runner | None = None
_session_service: InMemorySessionService | None = None


def get_runner() -> Runner:
    """
    Runner 인스턴스 반환 (싱글톤)

    Returns:
        Runner: Runner 인스턴스
    """
    global _runner_instance, _session_service

    if _runner_instance is None:
        agent = get_agent()

        # 세션 서비스 생성 (in-memory)
        if _session_service is None:
            _session_service = InMemorySessionService()

        # Runner 생성
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

    logger.info(
        f"Running agent",
        extra={
            "user_id": uid,
            "session_id": session_id,
            "message_length": len(message),
        },
    )

    try:
        # 세션이 없으면 생성 (존재 여부 확인 후)
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

        # 사용자 메시지 생성
        content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Agent 실행 (비동기 이터레이터)
        final_response = ""
        async for event in runner.run_async(
            user_id=uid,
            session_id=session_id,
            new_message=content,
        ):
            # 최종 응답 추출
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text"):
                        final_response += part.text

        logger.info(
            f"Agent response generated",
            extra={
                "user_id": uid,
                "session_id": session_id,
                "response_length": len(final_response),
            },
        )

        return final_response

    except Exception as e:
        logger.error(
            f"Agent execution failed: {str(e)}",
            extra={
                "user_id": uid,
                "session_id": session_id,
                "error": str(e),
            },
            exc_info=True,
        )
        raise


async def run_agent_stream(
    message: str,
    user_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Agent 실행 (스트리밍 응답)

    Args:
        message: 사용자 메시지
        user_id: 사용자 ID (인증된 경우)

    Yields:
        str: Agent 응답 청크
    """
    global _session_service
    runner = get_runner()

    # 사용자 ID 및 세션 ID 설정
    uid = user_id or "anonymous"
    session_id = f"{uid}_session"

    logger.info(
        f"Running agent (streaming)",
        extra={
            "user_id": uid,
            "session_id": session_id,
            "message_length": len(message),
        },
    )

    try:
        # 세션이 없으면 생성 (존재 여부 확인 후)
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

        # 사용자 메시지 생성
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
            # 텍스트 청크 추출
            if event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield part.text

        logger.info(
            f"Agent streaming completed",
            extra={
                "user_id": uid,
                "session_id": session_id,
            },
        )

    except Exception as e:
        logger.error(
            f"Agent streaming failed: {str(e)}",
            extra={
                "user_id": uid,
                "session_id": session_id,
                "error": str(e),
            },
            exc_info=True,
        )
        raise
