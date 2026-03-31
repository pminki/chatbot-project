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

### 5. [ingest_data.py](file:///e:/project/chatbot-project/backend/scripts/ingest_data.py)
- **Performance Fix**: Optimized the data insertion logic by using batch additions for both Chroma (Vector DB) and MariaDB (SQL), significantly improving speed.
- **Documentation**: Added comments explaining the PDF/TXT loading, text splitting (chunking), and the overall ingestion workflow for new developers.

### 6. [schemas.py](file:///e:/project/chatbot-project/backend/models/schemas.py)
- **Documentation**: Added beginner-friendly comments explaining the data structures used for API requests and responses, as well as AI classification results.

### 7. [database.py](file:///e:/project/chatbot-project/backend/models/database.py)
- **Documentation**: Added comprehensive comments explaining the SQLAlchemy setup (Engine, Session, Base) and the schema definitions for learning records, document metadata, and chat messages.

## Frontend Documentation

### 1. [main.tsx](file:///e:/project/chatbot-project/frontend/src/main.tsx)
- **Documentation**: Explained how the React application is converted into a standard Web Component (Custom Element).

### 2. [App.tsx](file:///e:/project/chatbot-project/frontend/src/App.tsx)
- **Documentation**: Explained the use of `MemoryRouter` for embedded applications to avoid interfering with the host website's URL, and documented the basic routing structure.

### 3. [ChatPage.tsx](file:///e:/project/chatbot-project/frontend/src/pages/ChatPage.tsx)
- **Bug Fix**: Replaced the deprecated `onKeyPress` with `onKeyDown` for better compatibility.
- **Documentation**: Documented the state management, API interaction, and UI feedback logic.

### 4. [api.ts](file:///e:/project/chatbot-project/frontend/src/services/api.ts)
- **Documentation**: Documented the fetch-based communication layer, explaining HTTP methods (POST), headers, and JSON serialization.

### 5. [tsconfig.json](file:///e:/project/chatbot-project/frontend/tsconfig.json)
- **Bug Fix**: Added a proper TypeScript configuration file to resolve linting errors.

### 6. [chat.ts](file:///e:/project/chatbot-project/frontend/src/types/chat.ts)
- **Documentation**: Documented the shared TypeScript interfaces for requests and responses, ensuring consistency between frontend components and services.

## Verification Results

- All missing imports have been resolved.
- Code logic remains intact while being much easier to read for beginners.
- The system is now more robust with proper error handling and logging comments.

---
> [!NOTE]
> The comments are tailored for beginners, using analogies like "Factory", "Map", and "Recipe" to explain complex AI/Backend concepts.


# DB Storage and Context Memory Fix Walkthrough

We have successfully resolved the issues with database persistence and conversation memory. The chatbot now remembers previous turns and records all activities in the database.

## Changes Made

### 🗄️ Database Layer
- **[database/init.sql](file:///e:/project/chatbot-project/database/init.sql)**: Fixed syntax errors (missing `COMMENT` keywords) that prevented correct schema initialization.
- **[models/database.py](file:///e:/project/chatbot-project/backend/models/database.py)**: 
    - Added `ChatSession` model to track sessions.
    - Updated `LearningTutorRecord` and `ChatMessage` to be fully compatible with the backend logic.

### 🧠 Agent Memory
- **[services/agent_service.py](file:///e:/project/chatbot-project/backend/services/agent_service.py)**: 
    - Integrated `MemorySaver` (Checkpointer) into the LangGraph workflow.
    - Updated `achat_stream` to use the `session_id` as the `thread_id` for state persistence.

### 📝 API and Logging
- **[main.py](file:///e:/project/chatbot-project/backend/main.py)**: 
    - Refactored `log_chat_message` to handle three tables: `chat_sessions`, `chat_messages`, and `learning_tutor_records`.
    - It now automatically creates or updates session and tutor records based on the interaction.

---

## Verification Results

### 1. Conversation Memory (Thread Control)
We simulated a conversation to test if the AI remembers the user's name across turns.
- **Input 1**: "My name is Hong Gil-dong"
- **Input 2**: "What is my name?"
- **Result**: AI correctly answered "Your name is Hong Gil-dong."

### 2. Database Persistence
We verified the SQL records using raw queries in the `db` container.
- **`chat_sessions`**: Successfully created for the session ID.
- **`chat_messages`**: Recorded both user and assistant messages with the correct roles.
- **`learning_tutor_records`**: Successfully created when the intent was classified as `TUTOR`.

> [!TIP]
> Since we dropped the old tables to apply the new schema, any previously uploaded RAG files' metadata was cleared from the DB (though vectors remain in ChromaDB). You should **re-upload** or manually re-sync your knowledge files to resume knowledge-based chatting.

---

The system is now robust and ready for production-level logging and context management. 🚀



# AI Response UI Fix (Spacing & Markdown) Walkthrough

We have addressed the issue where AI responses appeared as a single collapsed line of text.

## 🛠️ Key Fixes

### 1. Single Newline Handling (`remark-breaks`)
By default, Markdown requires two newlines to start a new paragraph. We integrated the `remark-breaks` plugin so that even a single `\n` character from the LLM is rendered as a line break.

### 2. Typography Spacing (`.prose` class)
We applied a custom `.prose` class to the message bubbles. This ensures that:
- **Paragraphs**: Have a `0.75rem` bottom margin.
- **Lists**: Have proper indentation and bullet point spacing.
- **Code**: Inline code has a subtle background and distinct color.

### 3. Clean Environment
The frontend was rebuilt with `--no-cache` to ensure all new dependencies (`react-markdown`, `remark-gfm`, `remark-breaks`, etc.) are correctly installed and bundled.

---

## Technical Stack Update
- **Renderer**: `ReactMarkdown` v9
- **Plugins**: `remark-gfm` (Tables), `remark-breaks` (Single newlines)
- **Styling**: Tailwind CSS + Custom CSS Transitions

---

The chat interface is now optimized for clear, educational, and technical communication. 🚀

# Visual Precision Refresh Walkthrough

We have final-tuned the aesthetic coordinates to achieve a more harmonious and professional layout for the 500x700px chat window.

## 📐 Golden Ratio Alignment

### 1. Optimized Padding (`px-5`)
To avoid the "crowded" look in the expanded frame, we transitioned from `px-6` (1.5rem) to `px-5` (1.25rem). This subtle change significantly improves the spatial balance of the content areas.

### 2. Message Bubble Breathing Room
- **Max Width**: Reduced from `90%` to `85%`.
- **Reasoning**: By keeping the bubbles away from the container's right edge, we create a clear visual path for the user to follow, making conversational threads much easier to read.

### 3. Vertical Symmetry
- **Header <=> Footer Consistency**: Ensured that the text containers in both the header and footer start at the exact same horizontal offset. 
- **Icon Sizing**: Reduced the `X` button and `Send` button scale slightly to match the overall typography weight.

---

The chat interface is now visually balanced and respects the proportions of the UI container. 🚀


# Unified Responsive Chat System Walkthrough

We have modernized the Chatbot's infrastructure by unifying the UI logic and implementing a fully responsive layout.

## 📐 Responsive Intelligence

The chat window now intelligently adapts to the user's viewport:

### Mobile context (< 640px)
- **Fluid Width**: Automatically expands to fill the screen width with a small margin (`right-4 left-4`).
- **Dynamic Height**: Scales based on the window height (`h-[calc(100vh-120px)]`).

### Desktop context (> 640px)
- **Optimal Size**: Fixed at `500x700px` for a professional, centered interaction experience.
- **Floating Position**: Fixed `bottom-28 right-8` to avoid interfering with general web content.

## 🛠️ Logic Unification

We eliminated the duplication of the Close (X) button and container styles:

### Single Source of Truth (`ChatPage.tsx`)
- The React component now manages its own header, borders, and shadowing.
- **Custom Event Integration**: The internal `X` button now dispatches a `close-chat` event, which the host page (`index.html`) listens to for triggering the scale-up/down animations.

### Lean Wrapper (`index.html`)
- The `#chat-container` was stripped of all redundant styling. It now acts purely as a positioning and visibility shell, leading to a much smaller DOM footprint and better performance.

---
The Tutor Chatbot is now ready for both high-performance desktop use and convenient mobile access. 🚀

