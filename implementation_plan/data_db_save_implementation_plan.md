# DB Storage and Context Memory Fix Plan

This plan aims to resolve the issues where chat data is not being persisted to the database and the chatbot fails to remember previous conversation context.

## User Review Required

> [!IMPORTANT]
> To enable context memory, we will use LangGraph's built-in `MemorySaver`. This will keep the conversation state in the server's memory for each `thread_id` (matched with `session_id`). 
> 
> For database storage, we will ensure that `chat_sessions` and `learning_tutor_records` are correctly populated upon every successful reply.

## Proposed Changes

### Database Layer

#### [MODIFY] [database.py](file:///e:/project/chatbot-project/backend/models/database.py)
- **[NEW] ChatSession Table**: Add a table to track active chat sessions, including `session_id`, `user_id`, and `last_message_at`.
- Ensure `ChatMessage` and `LearningTutorRecord` have appropriate indexes for fast retrieval.

---

### Agent Service Layer

#### [MODIFY] [agent_service.py](file:///e:/project/chatbot-project/backend/services/agent_service.py)
- **Memory Integration**: 
    - Import `MemorySaver` from `langgraph.checkpoint.memory`.
    - Update `_build_graph` to compile with the checkpointer: `self.graph = workflow.compile(checkpointer=MemorySaver())`.
- **Session handling**:
    - Update `achat_stream` to accept `session_id` and pass it as `thread_id` in the `config` parameter of `astream_events`.
    - This ensures LangGraph automatically loads and saves the message history for that session.

---

### API Layer

#### [MODIFY] [main.py](file:///e:/project/chatbot-project/backend/main.py)
- **Storage Logic Refactoring**:
    - Enhance `log_chat_message` to:
        1. Check if a `ChatSession` exists; if not, create it.
        2. Save the user and assistant messages to `chat_messages`.
        3. (Optional) Generate a summary using AI for `learning_tutor_records` every few messages or at the end of a session.
- **Async Safety**: Ensure the database session management is robust within the background task.

## Verification Plan

### Automated Tests
- Send multiple messages within the same `session_id` and verify that the AI responds based on previous turns.
- Use `docker compose exec db mariadb ...` to query `chat_messages`, `chat_sessions`, and `learning_tutor_records` to verify data exists.

### Manual Verification
1. Open the chatbot and say "My name is John".
2. Ask "What is my name?". AI should answer "Your name is John".
3. Check the database `chat_messages` table to see both turns recorded.
4. Verify `learning_tutor_records` has a new or updated entry for the user.
