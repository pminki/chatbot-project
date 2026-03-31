# Unified Chat UI & Logic Integration

Unify the chat box styling and close functionality into the React component to eliminate duplication and visual inconsistencies.

## User Review Required

> [!IMPORTANT]
> The "Close" (X) logic will move from the static HTML button to the React component's header button. We will use a `CustomEvent` named `close-chat` to bridge the gap between the React component and the legacy script in `index.html`.

## Proposed Changes

### [Component] UI Architecture Refactoring

#### [MODIFY] [ChatPage.tsx](file:///e:/project/chatbot-project/frontend/src/pages/ChatPage.tsx)
- Add a custom event dispatcher to the `X` button in the header.
- Refine the main container classes:
    - Change `w-[500px] h-[700px]` to `w-full h-full` or ensure it matches the parent perfectly.
    - Remove `mx-auto my-8` which was causing alignment issues within the fixed container.
    - Ensure the shadow, border, and background are clearly defined here as the "source of truth".

#### [MODIFY] [index.html](file:///e:/project/chatbot-project/frontend/index.html)
- **Container Cleanup**: Remove `bg-white`, `rounded-2xl`, `shadow-2xl`, `border`, `overflow-hidden` from `#chat-container`. It should be a transparent positioning wrapper.
- **Button Removal**: Delete the `<button id="chat-close">` block and its SVG content.
- **Logic Integration**: Update the script to add an event listener for `close-chat` on the window or the `ai-chatbot` element.

## Verification Plan

### Manual Verification
- **Layout Check**: Verify that the chat box looks identical (same shadow/border) but without double borders or misaligned icons.
- **Functionality**:
    1. Click the floating toggle button to OPEN.
    2. Click the `X` button **inside the React header** to CLOSE.
    3. Verify the scale animation and visibility toggle work as before.
