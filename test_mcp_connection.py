"""
MCP 서버 연결 및 Agent 테스트

MCP Hub MCP 서버가 localhost:10004에서 실행 중이어야 합니다.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_mcp_server_connection():
    """MCP 서버 연결 테스트"""
    print("=" * 70)
    print("MCP Hub Agent - MCP 서버 연결 테스트")
    print("=" * 70)

    # Test 1: MCP 서버 응답 확인
    print("\n[Test 1] MCP 서버 연결 확인...")
    print("  - URL: http://localhost:10004")

    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:10004", timeout=5.0)
            print(f"  - Status: {response.status_code}")
            print(f"  - Response: {response.text[:100]}...")
            print("  ✅ MCP 서버 응답 확인")
    except Exception as e:
        print(f"  ❌ MCP 서버 연결 실패: {e}")
        print("\n⚠️  MCP 서버를 먼저 실행해주세요:")
        print("    cd ~/code/mcp-hub-mcp")
        print("    python src/mcp_main.py")
        return

    # Test 2: Agent import
    print("\n[Test 2] Agent 모듈 import...")
    try:
        from backend.agents.mcp_hub_agent import root_agent
        print(f"  - Agent name: {root_agent.name}")
        print(f"  - Tools: {len(root_agent.tools)} tool(s)")
        print("  ✅ Agent 모듈 import 성공")
    except Exception as e:
        print(f"  ❌ Agent import 실패: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Agent Service
    print("\n[Test 3] Agent Service 테스트...")
    try:
        from backend.services.agent_service import run_agent

        # Google API key 확인
        google_api_key = os.getenv("GOOGLE_API_KEY", "")
        if not google_api_key or google_api_key == "your-google-api-key-here":
            print("  ⚠️  GOOGLE_API_KEY가 설정되지 않았습니다.")
            print("     backend/.env에 실제 API key를 설정해주세요.")
            print("  ℹ️  MCP 서버 연결은 확인되었으므로 구조는 정상입니다.")
            return

        # 간단한 질문 테스트
        test_message = "Hello! Can you help me with MCP Hub?"
        print(f"\n  [User]: {test_message}")
        print("  " + "-" * 66)

        response = await run_agent(test_message)
        print(f"  [Agent]: {response[:200]}...")
        print("  " + "-" * 66)
        print("\n  ✅ Agent 실행 성공!")

    except Exception as e:
        print(f"  ❌ Agent 실행 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    print("\nℹ️  주의사항:")
    print("  1. MCP Hub MCP 서버가 localhost:10004에서 실행 중이어야 합니다.")
    print("  2. backend/.env에 GOOGLE_API_KEY가 설정되어 있어야 합니다.\n")

    try:
        asyncio.run(test_mcp_server_connection())
    except KeyboardInterrupt:
        print("\n\n테스트 중단됨")
    except Exception as e:
        print(f"\n\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
