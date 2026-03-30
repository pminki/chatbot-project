# Walkthrough: Backend Documentation & Fixes

I have added comprehensive, beginner-friendly Korean comments to the core backend services and fixed several critical errors discovered during the process.

## Changes Made

### 1. [main.py](file:///e:/project/chatbot-project/backend/main.py)
- **Bug Fix**: Added missing imports for `SessionLocal` and `ChatMessage` from `models.database`.
- **Documentation**: Added detailed comments explaining the FastAPI setup, CORS middleware, and the chat endpoint logic including DB logging.

### 2. [agent_service.py](file:///e:/project/chatbot-project/backend/services/agent_service.py)
- **Bug Fix**: Added missing `import os` for environment variable access.
- **Documentation**: Clarified the LangGraph state management, routing logic, and node behaviors (Tutor vs. CS).

### 3. [retrieval_service.py](file:///e:/project/chatbot-project/backend/services/retrieval_service.py)
- **Documentation**: Explained the Retrieval-Augmented Generation (RAG) process, including Vector DB (Chroma) search and SQL DB (SQLAlchemy) session management.

### 4. [llm_factory.py](file:///e:/project/chatbot-project/backend/core/llm_factory.py)
- **Documentation**: Documented the Factory pattern used to dynamically switch between AI providers (OpenAI / Vertex AI) and explained LLM parameters like `temperature`.

## Verification Results

- All missing imports have been resolved.
- Code logic remains intact while being much easier to read for beginners.
- The system is now more robust with proper error handling and logging comments.

---
> [!NOTE]
> The comments are tailored for beginners, using analogies like "Factory", "Map", and "Recipe" to explain complex AI/Backend concepts.