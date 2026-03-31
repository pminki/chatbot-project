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
    - Change `w-[500px] h-[700px]` to `w-full h-full`.
    - Ensure the shadow, border, and background are clearly defined here.
    - **Responsive Tuning**: Ensure internal padding/font sizes feel appropriate even when narrowed on mobile.

#### [MODIFY] [index.html](file:///e:/project/chatbot-project/frontend/index.html)
- **Container Cleanup & Responsiveness**: 
    - Remove redundant styles (`bg-white`, `border`, etc.).
    - Apply responsive classes to `#chat-container`:
        - **Mobile**: `bottom-24 right-4 left-4 w-auto h-[calc(100vh-120px)] max-h-[700px]`
        - **Desktop (sm:)**: `sm:left-auto sm:right-8 sm:bottom-28 sm:w-[500px] sm:h-[700px]`
- **Button Removal**: Delete the `<button id="chat-close">` block.
- **Logic Integration**: Update script to listen for `close-chat`.

## Verification Plan

### Manual Verification
- **Layout Check**: Verify that the chat box looks identical (same shadow/border) but without double borders or misaligned icons.
- **Functionality**:
    1. Click the floating toggle button to OPEN.
    2. Click the `X` button **inside the React header** to CLOSE.
    3. Verify the scale animation and visibility toggle work as before.
