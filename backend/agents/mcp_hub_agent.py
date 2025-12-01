"""
MCP Hub Agent - ADK Standard Format

This agent can be run with ADK CLI:
    adk run mcp_hub_agent

Or used in backend services via import.
"""

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams

# Instructions 파일 경로
INSTRUCTIONS_FILE = Path(__file__).parent / "instructions.md"


def _load_instructions() -> str:
    """
    instructions.md 파일을 읽어서 반환

    Returns:
        str: System prompt 내용
    """
    try:
        with open(INSTRUCTIONS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful AI assistant for MCP Hub."


def _get_model():
    """
    환경에 맞는 모델 반환

    개발 환경: Gemini 2.0 Flash (기본)
    프로덕션 환경: GPT-OSS-120B

    Returns:
        str | LiteLlm: 모델 설정
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        # 프로덕션: GPT-OSS-120B 또는 사내 LLM
        model_name = os.getenv("MODEL_NAME_PROD", "gpt-oss-120b")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")  # 사내 LLM 엔드포인트

        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for production environment")

        # LiteLlm 설정
        litellm_config = {
            "model": f"openai/{model_name}",
            "api_key": api_key,
        }

        # base_url이 있으면 추가 (사내 LLM 사용 시)
        if base_url:
            litellm_config["api_base"] = base_url

        return LiteLlm(**litellm_config)
    else:
        # 개발: Gemini 2.0 Flash
        model_name = os.getenv("MODEL_NAME_DEV", "gemini-2.0-flash-exp")

        # GOOGLE_API_KEY 환경 변수 설정 (ADK가 인식하도록)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key

        return model_name


def _get_mcp_tools() -> list:
    """
    여러 MCP 서버에서 도구 가져오기

    SSE transport를 사용하여 원격 MCP 서버들과 연결

    Returns:
        list: MCPToolset 인스턴스 리스트
    """
    app_env = os.getenv("APP_ENV", "development")
    toolsets = []

    # 1. MCP Hub MCP 서버 (SSE)
    # Base URL만 사용 (SseServerTransport가 /messages 경로를 처리)
    mcp_hub_url = os.getenv(
        "MCP_HUB_SERVER_URL_PROD" if app_env == "production" else "MCP_HUB_SERVER_URL_DEV",
        "http://localhost:10004"
    )

    mcp_hub_toolset = MCPToolset(
        connection_params=SseConnectionParams(
            url=mcp_hub_url,
            timeout=float(os.getenv("MCP_SERVER_TIMEOUT", "30")),
            sse_read_timeout=300.0,
        ),
    )
    toolsets.append(mcp_hub_toolset)

    # 2. 추가 MCP 서버들 (향후 추가)
    # 예: Analytics MCP, Chart MCP 등
    # analytics_toolset = MCPToolset(...)
    # toolsets.append(analytics_toolset)

    return toolsets


# ADK Standard Agent Definition
# Both ADK CLI and FastAPI use this
root_agent = LlmAgent(
    model=_get_model(),
    name="mcp_hub_agent",
    instruction=_load_instructions(),
    tools=_get_mcp_tools(),  # MCP Hub MCP 서버의 도구들
)
