# Fix Database Schema Mismatch for Chat Logging

The chat messages and sessions are not being saved because the backend application (SQLAlchemy) expects columns in the database that do not exist, or has different column names than the actual database schema. Specifically, the `chat_sessions` table is missing the `last_message_at` column used in the model, and instead has an `updated_at` column.

## User Review Required

> [!IMPORTANT]
> The fix involves modifying the SQLAlchemy models to match the existing database schema defined in `init.sql`. This is generally safer than modifying the database directly in production, but since this is a development environment, I've opted for synchronization.

> [!WARNING]
> No data will be lost, but some existing rows might have NULL in the newly added model fields if they weren't already populated (though in this case, the columns already exist in the DB, just not in the model).

## Proposed Changes

### Backend Models

#### [MODIFY] [database.py](file:///e:/project/chatbot-project/backend/models/database.py)
Update the `ChatSession` and `RagDocumentMeta` models to match the actual database schema.

- `ChatSession`:
    - Rename `last_message_at` to `updated_at` for consistency with `init.sql`.
    - Add `session_type` column (String(20), default="NORMAL").
- `RagDocumentMeta`:
    - Add `created_at` and `updated_at` columns.
- `ChatMessage`:
    - Ensure `tokens_used` is consistent (it is currently `BigInteger`, which is fine for `INT` in DB).

## Open Questions

- Should I also update `init.sql` to match any changes, or do you prefer keeping the model as the source of truth? (Currently, I'm matching the model to `init.sql` as it is the "installed" schema).

## Verification Plan

### Automated Tests
- I will run a script to attempt a database connection and a simple query on the `ChatSession` table to ensure no `OperationalError` (Unknown column) occurs.

### Manual Verification
- I will ask the user to send a chat message and check if it is successfully saved to the `chat_messages` and `chat_sessions` tables by checking the backend logs for any "로그 저장 실패" (Log Save Failed) messages.
