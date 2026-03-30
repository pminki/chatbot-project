# 🤖 LMS AI 튜터링 및 CS 챗봇 시스템

본 프로젝트는 기존 LMS(학습관리시스템)의 레거시 환경을 수정하지 않고, 최신 AI 기술(LLM, RAG)을 '웹 컴포넌트' 형태로 유연하게 통합하기 위해 구축된 하이브리드 챗봇 시스템입니다.

## 🏗️ 시스템 아키텍처 (Tech Stack)

이 시스템은 인프라 충돌을 방지하기 위해 완전한 Docker 컨테이너 환경에서 독립적으로 구동됩니다.

* **Frontend**: React 18, TypeScript, Vite, Web Components (기존 JSP 화면에 태그 1줄로 삽입)
* **Backend**: Python 3.11, FastAPI, LangGraph, LangChain (의도 라우팅 및 상태 관리)
* **Database**: MariaDB 10.11 (세션 및 튜터링 기록), ChromaDB (사내 문서 RAG 벡터 검색)
* **Infrastructure**: Docker, Docker Compose

---

## 🚀 시작하기 (Getting Started)

팀원 누구나 아래의 절차를 따라 로컬 환경에 챗봇 시스템을 띄울 수 있습니다.

### 1. 사전 요구 사항 (Prerequisites)
* [Docker](https://www.docker.com/products/docker-desktop) 및 Docker Compose가 설치되어 있어야 합니다.
* OpenAI API Key가 필요합니다.


### 2. 환경 변수 설정
프로젝트 최상단에 `.env` 파일을 생성하고 아래 내용을 팀 환경에 맞게 작성합니다.
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=mysql+pymysql://chatbot_user:chatbot_password@db:3306/ai_chatbot_db?charset=utf8mb4


### 3. 컨테이너 실행 (Build & Run)
# 백그라운드에서 전체 시스템(DB, Backend, Frontend) 빌드 및 실행
docker-compose up -d --build


### 4. 사내 문서 학습 (Data Ingestion)
# 최초 실행 시 챗봇의 지식(Vector DB)을 채워주어야 합니다.
# 프로젝트 최상단의 data/ 폴더에 학습시킬 매뉴얼(PDF, TXT)을 넣습니다.
# 아래 명령어를 통해 데이터를 임베딩합니다.
# 백엔드 컨테이너 내부로 진입하여 학습 스크립트 실행
docker exec -it chatbot-backend python scripts/ingest_data.py

---

## 💻 레거시 시스템(JSP/HTML) 연동 방법
# Docker 시스템이 구동 중이라면, 기존 LMS의 화면 소스(예: footer.jsp 또는 index.html) 하단에 아래 두 줄의 코드만 추가하면 챗봇이 즉시 렌더링됩니다.
<script type="module" src="http://localhost:3000/assets/chatbot-bundle.js"></script>
<ai-chatbot user-id="lms-user-001"></ai-chatbot>

---

## 📁 주요 디렉토리 구조
chatbot-project/
├── backend/               # FastAPI 및 LangGraph 백엔드 API
│   ├── main.py            # API 라우터 진입점
│   ├── models/            # SQLAlchemy DB 모델 및 스키마
│   ├── services/          # 의도 분류(Router) 및 RAG 검색 핵심 로직
│   └── scripts/           # 벡터 DB 임베딩 스크립트
├── frontend/              # React 기반 웹 컴포넌트 UI
│   ├── src/pages/         # 챗봇 대화 화면 (타이핑 애니메이션 포함)
│   └── src/main.tsx       # React 앱을 <ai-chatbot> 태그로 변환
├── database/              # MariaDB 초기화 스크립트 (init.sql)
└── docker-compose.yml     # 전체 시스템 오케스트레이션

---

## 🛠️ 유지보수 및 트러블슈팅
### Q. 챗봇이 대답을 안 하거나 에러가 납니다.
  - 백엔드 로그를 확인하여 LLM API 호출 문제인지, DB 연결 문제인지 파악합니다.
    docker logs -f chatbot-backend

### Q. 새로운 기능을 추가하고 싶습니다.
  - 의도(Intent) 추가: backend/models/schemas.py 및 backend/services/agent_service.py의 라우터 프롬프트를 수정합니다.
  - UI 변경: frontend/src/pages/ChatPage.tsx를 수정하고 컨테이너를 재시작합니다.


