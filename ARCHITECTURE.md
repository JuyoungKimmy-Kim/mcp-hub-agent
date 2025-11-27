# MCP Hub Agent Architecture

## 시스템 아키텍처

```
┌────────────────────────────────────────┐
│ MCP Hub Web (사용자 로그인)           │
│ └─ Embedded Chatbot UI (React)        │
│    └ Calls /api/chat (SSE)            │
│      + Authorization: Bearer <token>   │
└───────────────▲────────────────────────┘
                │
                │ message + JWT token (streaming)
                ▼
┌──────────────────────────────┐
│ Backend (FastAPI)            │
│ ├ /api/chat (SSE)            │
│ ├ /api/health                │
│ ├ Auth Middleware (선택적)   │
│ │  - JWT 검증 & user_id 추출│
│ │  - 토큰 없으면 익명 처리   │
│ ├ Rate Limiting              │
│ └ agent.run_stream()         │
└───────────────▲──────────────┘
                │ metadata {user_id}
                ▼
┌──────────────────────────────┐
│ Google ADK Agent             │
│ ├ LLM: Gemini (dev)          │
│ │      GPT (prod)             │
│ ├ MCPHubTool                 │
│ ├ ChartTool                  │
│ ├ ReportTool                 │
│ └ AnalyticsTool (MCP 기반)  │
└───────────────▲──────────────┘
                │ + user_id (if authenticated)
                ▼
┌──────────────────────────────┐
│ MCP Hub MCP Server (SSE)     │
│ └ Provides all analytics data│
│   - 익명: 공개 정보만        │
│   - 인증: 개인화 정보 포함   │
└──────────────────────────────┘
```

## 디렉토리 구조

```
project-root/
│
├── backend/                     # 실제 챗봇 Agent 서버
│   ├── main.py                  # FastAPI entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py              # /api/chat, /api/chat/stream 엔드포인트
│   │   └── health.py            # /health 헬스체크
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent 생성 및 실행
│   │   └── instructions.md      # System prompt
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseTool 추상 클래스
│   │   ├── mcp_hub_tool.py      # mcp-hub-mcp wrapper (주 데이터 소스)
│   │   ├── analytics_tool.py    # MCP 기반 고급 분석
│   │   ├── chart_tool.py        # 시각화(base64 이미지)
│   │   └── report_tool.py       # PDF/MD 요약 보고서
│   ├── services/
│   │   ├── __init__.py
│   │   ├── mcp_client.py        # MCP 서버 연결 관리 및 connection pooling
│   │   └── cache.py             # Redis/in-memory 캐싱
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py              # Token 검증 미들웨어
│   │   ├── rate_limit.py        # Rate limiting (분당 요청 수 제한)
│   │   └── error_handler.py     # Global error handling
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Pydantic Settings (환경 변수)
│   │   └── mcp_servers.yaml     # MCP 서버 URL 등
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models (Request/Response)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py            # Structured logging (structlog)
│   │   └── validators.py        # Input validation
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                    # MCP Hub Web에 임베드될 Chat UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatWindow.jsx
│   │   │   │   ├── MessageList.jsx
│   │   │   │   ├── MessageItem.jsx
│   │   │   │   ├── InputBox.jsx
│   │   │   │   └── TypingIndicator.jsx
│   │   │   └── Visualizations/
│   │   │       ├── ChartRenderer.jsx     # base64 차트 렌더링
│   │   │       └── ReportViewer.jsx      # PDF/MD 리포트 뷰어
│   │   ├── hooks/
│   │   │   ├── useChat.js                # 채팅 로직 분리
│   │   │   └── useStreamingChat.js       # SSE 스트리밍 처리
│   │   ├── services/
│   │   │   └── api.js                    # Backend API 호출 (JWT 토큰 헤더 포함)
│   │   ├── utils/
│   │   │   └── localStorage.js           # 대화 히스토리 저장
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 핵심 개념

### 기본 원칙
- Tool중 mcp-hub 관련 질의는 **mcp-hub-mcp (SSE) 통해 가져옴**
- **시각화 = ChartTool** (matplotlib/plotly → base64)
- **요약/보고서 = ReportTool** (PDF/Markdown 생성)
- **챗봇은 MCP Hub 웹사이트에 임베드됨** → 별도 로그인 UI 없음
- **인증 처리:**
  - **익명 사용자**: 공개 정보만 조회 (예: "가장 인기있는 MCP는?")
  - **로그인 사용자**: 개인화 정보 조회 (예: "내가 등록한 MCP 중 가장 인기있는 것은?")
  - MCP Hub 웹사이트가 JWT 토큰을 자동으로 전달 (Authorization 헤더)
- **JWT_SECRET_KEY는 MCP Hub 웹사이트와 공유** → 토큰 검증용
- Backend → FastAPI, Frontend → React (Vite) 기반
- Backend 서버 하나만 띄우고, Frontend를 정적 파일로 빌드해서 함께 서빙 (Docker)

### 기술 스택

**Backend:**
- FastAPI (비동기 웹 프레임워크)
- Google ADK (Agent Development Kit)
- LLM:
  - 개발: Gemini 2.0 Flash (google-generativeai)
  - 프로덕션: GPT-4o (openai)
- Pydantic Settings (환경 변수 관리)
- httpx (비동기 HTTP 클라이언트)
- structlog (구조화된 로깅)
- Redis (선택: 캐싱용, 개발 단계에서는 in-memory)

**Frontend:**
- React + Vite
- TanStack Query (React Query) - 서버 상태 관리
- SSE (Server-Sent Events) - 스트리밍
- LocalStorage - 대화 히스토리

**DevOps:**
- Docker + Docker Compose
- Uvicorn (ASGI 서버)

## 주요 기능

### 1. 스트리밍 응답 (SSE)
```python
# backend/api/chat.py
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in agent.run_stream(request.message, request.token):
            yield f"data: {json.dumps(chunk)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 2. 인증 및 보안
- JWT Token 기반 인증
- Rate Limiting (사용자당 분당 요청 수 제한)
- CORS 설정
- Input Validation (XSS, Injection 방지)

### 3. 성능 최적화
- MCP 응답 캐싱 (Redis or in-memory)
- Connection Pooling for MCP servers
- 비동기 처리 (FastAPI + httpx)

### 4. 운영 및 모니터링
- 구조화된 로깅 (structlog)
- Health check 엔드포인트
- 에러 핸들링 및 사용자 친화적 에러 메시지
- 대화 히스토리 로컬 저장

### 5. UX 개선
- 실시간 타이핑 효과 (스트리밍)
- 로딩 상태 표시
- 차트/리포트 인라인 렌더링
- 반응형 디자인

---

## 구현 로드맵

각 feature별로 branch를 생성하여 순차적으로 구현합니다.

### Phase 1: 기반 구조 (Backend Core)

#### 1. `feat/backend-setup` - 프로젝트 기본 구조
- [ ] 디렉토리 구조 생성
- [ ] requirements.txt 작성
- [ ] .env.example 생성
- [ ] .gitignore 설정
- [ ] README.md 업데이트

#### 2. `feat/fastapi-basic` - FastAPI 기본 설정
- [ ] main.py 생성 (FastAPI 앱 초기화)
- [ ] CORS 설정
- [ ] /health 헬스체크 엔드포인트
- [ ] Pydantic Settings 구현 (config/settings.py)
- [ ] 로컬 실행 테스트

#### 3. `feat/logger-setup` - 로깅 시스템
- [ ] structlog 설정 (utils/logger.py)
- [ ] 요청/응답 로깅 미들웨어
- [ ] 에러 핸들링 미들웨어 (middleware/error_handler.py)

### Phase 2: Agent 통합

#### 4. `feat/adk-integration` - Google ADK 통합
- [ ] Google ADK 설치 및 설정
- [ ] LLM 설정 (Gemini for dev, GPT for prod)
- [ ] Agent 기본 구조 (agent/agent.py)
- [ ] System prompt 작성 (agent/instructions.md)
- [ ] 기본 대화 테스트 (도구 없이)

#### 5. `feat/mcp-hub-tool` - MCP Hub Tool 구현
- [ ] mcp-hub-mcp 서버 연결 설정
- [ ] MCP Client 구현 (services/mcp_client.py)
- [ ] MCPHubTool 구현 (tools/mcp_hub_tool.py)
- [ ] Tool 테스트 (MCP 서버 조회)

### Phase 3: API 구현

#### 6. `feat/auth-middleware` - 인증 시스템
- [ ] JWT Token 검증 로직 (middleware/auth.py)
- [ ] Pydantic schemas (models/schemas.py)
- [ ] Input validation (utils/validators.py)
- [ ] 인증 테스트

#### 7. `feat/chat-api-basic` - 기본 Chat API
- [ ] /api/chat 엔드포인트 (동기 버전)
- [ ] Request/Response 모델 정의
- [ ] Agent 실행 및 응답 반환
- [ ] 에러 처리

#### 8. `feat/streaming-api` - 스트리밍 API
- [ ] /api/chat/stream 엔드포인트 (SSE)
- [ ] Agent 스트리밍 실행
- [ ] SSE 형식 응답
- [ ] 스트리밍 테스트 (curl/Postman)

### Phase 4: Frontend 기본

#### 9. `feat/frontend-setup` - React 프로젝트 설정
- [ ] Vite + React 프로젝트 생성
- [ ] 디렉토리 구조 설정
- [ ] TailwindCSS 설정 (선택)
- [ ] .env.example 작성

#### 10. `feat/chat-ui-basic` - 기본 Chat UI
- [ ] ChatWindow 컴포넌트
- [ ] MessageList 컴포넌트
- [ ] MessageItem 컴포넌트
- [ ] InputBox 컴포넌트
- [ ] API 서비스 (services/api.js)
  - MCP Hub 웹사이트로부터 JWT 토큰 받기
  - Authorization 헤더에 토큰 포함
- [ ] 기본 채팅 기능 (동기)

#### 11. `feat/streaming-ui` - 스트리밍 UI 연동
- [ ] useStreamingChat 훅 (SSE 처리)
- [ ] TypingIndicator 컴포넌트
- [ ] 실시간 메시지 스트리밍
- [ ] 로딩 상태 표시

### Phase 5: 고급 기능

#### 13. `feat/chart-tool` - 차트 생성 Tool
- [ ] ChartTool 구현 (matplotlib/plotly)
- [ ] Base64 이미지 변환
- [ ] ChartRenderer 컴포넌트 (frontend)
- [ ] 차트 렌더링 테스트

#### 14. `feat/report-tool` - 리포트 생성 Tool
- [ ] ReportTool 구현 (PDF/Markdown)
- [ ] ReportViewer 컴포넌트 (frontend)
- [ ] 다운로드 기능

#### 15. `feat/analytics-tool` - Analytics Tool
- [ ] AnalyticsTool 구현 (MCP 기반 분석)
- [ ] 고급 쿼리 기능
- [ ] UI 통합

### Phase 6: 성능 & 보안

#### 16. `feat/caching` - 캐싱 레이어
- [ ] In-memory 캐시 구현 (services/cache.py)
- [ ] MCP 응답 캐싱
- [ ] TTL 설정
- [ ] (선택) Redis 통합

#### 17. `feat/rate-limiting` - Rate Limiting
- [ ] Rate limit 미들웨어 (middleware/rate_limit.py)
- [ ] 사용자별 요청 제한
- [ ] 에러 응답 처리

#### 18. `feat/conversation-history` - 대화 히스토리
- [ ] LocalStorage 저장 (frontend)
- [ ] 대화 불러오기/삭제
- [ ] UI 구현

### Phase 7: 배포

#### 19. `feat/docker-setup` - Docker 설정
- [ ] Backend Dockerfile
- [ ] Frontend 빌드 스크립트
- [ ] docker-compose.yml
- [ ] 정적 파일 서빙 설정 (FastAPI)
- [ ] 로컬 Docker 테스트

#### 20. `feat/production-ready` - 프로덕션 준비
- [ ] 환경 변수 최종 정리
- [ ] 보안 설정 검토
- [ ] 에러 로깅 개선
- [ ] 성능 테스트
- [ ] 문서화 (README 업데이트)

---

## 개발 가이드

### Branch 네이밍 규칙
```
feat/{feature-name}    # 새 기능
fix/{bug-name}         # 버그 수정
refactor/{scope}       # 리팩토링
docs/{scope}           # 문서 작업
```

### 개발 프로세스
```bash
# 1. 새 feature branch 생성
git checkout -b feat/backend-setup

# 2. 작업 수행

# 3. 커밋
git add .
git commit -m "feat: 백엔드 기본 구조 설정"

# 4. main에 머지
git checkout main
git merge feat/backend-setup

# 5. branch 삭제 (선택)
git branch -d feat/backend-setup
```

### 우선순위
- **필수 (MVP)**: Phase 1-4, Phase 5의 13-14, Phase 7
- **권장**: Phase 6 (성능/보안)
- **선택**: Phase 5의 15 (고급 분석)

### 각 Phase별 예상 작업량
- Phase 1-2: 기반 구축 (5 features)
- Phase 3: API 핵심 (3 features)
- Phase 4: UI 기본 (3 features) - 로그인 UI 제거됨
- Phase 5: 고급 기능 (3 features, 선택적)
- Phase 6: 최적화 (3 features)
- Phase 7: 배포 (2 features)

**총 19개 features** (기존 20개에서 auth-ui 제거)

