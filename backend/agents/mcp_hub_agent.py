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
    프로덕션 환경: GPT-4o

    Returns:
        str | LiteLlm: 모델 설정
    """
    app_env = os.getenv("APP_ENV", "development")

    if app_env == "production":
        # 프로덕션: OpenAI GPT-4o
        model_name = os.getenv("MODEL_NAME_PROD", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for production environment")

        return LiteLlm(
            model=f"openai/{model_name}",
            api_key=api_key,
        )
    else:
        # 개발: Gemini 2.0 Flash
        model_name = os.getenv("MODEL_NAME_DEV", "gemini-2.0-flash-exp")

        # GOOGLE_API_KEY 환경 변수 설정 (ADK가 인식하도록)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key

        return model_name


# ADK Standard Agent Definition
# Both ADK CLI and FastAPI use this
root_agent = LlmAgent(
    model=_get_model(),
    name="mcp_hub_agent",
    instruction=_load_instructions(),
    tools=[],  # Tools will be added in later phases
)
