# AI Response UI Enhancement Plan

This plan aims to transform the current plain-text AI responses into professional, readable, and interactive content using Markdown rendering and syntax highlighting.

## Proposed Changes

### Frontend Infrastructure

#### [DEPENDENCY] Package Installation
- **[NEW] react-markdown**: The core engine to render Markdown.
- **[NEW] remark-gfm**: Extension for GitHub Flavored Markdown (tables, tasklists).
- **[NEW] react-syntax-highlighter**: For high-quality code block rendering.
- **[NEW] lucide-react**: Premium icons for "Copy" and "Thinking" indicators.

### Component Layer

#### [NEW] [MarkdownRenderer.tsx](file:///e:/project/chatbot-project/frontend/src/components/MarkdownRenderer.tsx)
- Create a dedicated component that:
    - Wraps the AI text in a Markdown parser.
    - Applies Tailwind styles to base elements (`p`, `ul`, `ol`, `h1-h6`).
    - Integrates a code block component with syntax highlighting and a "Copy to Clipboard" button.
    - Handles line breaks and spacing automatically.

### UI Layer

#### [MODIFY] [ChatPage.tsx](file:///e:/project/chatbot-project/frontend/src/pages/ChatPage.tsx)
- Replace static text rendering with the new `MarkdownRenderer`.
- **Message Bubble Refresh**:
    - Increase max-width for better content flow.
    - Add subtle background gradients based on the intent (`TUTOR` vs `CS`).
    - Improve the "Thinking" animation to look more like a modern skeleton loader.
- **Improved Scrolling**: Ensure smooth scrolling even with large code blocks.

#### [MODIFY] [index.css](file:///e:/project/chatbot-project/frontend/src/index.css)
- Add typography tokens to handle `prose` styles specifically for chat bubbles.
- Add styles for the code block container (rounded corners, dark theme).

## Verification Plan

### Automated Tests
- Verify that a message containing "```python\nprint('hello')\n```" renders as a code block.
- Verify that a message with `* item 1\n* item 2` renders as a bulleted list.

### Manual Verification
1. Ask the AI: "Explain the for loop in Python with an example."
2. Check if:
    - The explanation is separated by paragraphs.
    - The code block has syntax highlighting and a "Copy" button.
    - The key points are bolded or highlighted.
3. Verify the layout on mobile (responsive check).
