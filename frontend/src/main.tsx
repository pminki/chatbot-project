import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import reactToWebComponent from 'react-to-webcomponent';
import App from './App';
import { RagManager } from './pages/RagManager';
import './index.css';

/**
 * [Web Component 변환 설정]
 */
const WebChatbot = reactToWebComponent(App, React, ReactDOMClient, {
  shadowDOM: false,
});

const WebRagManager = reactToWebComponent(RagManager, React, ReactDOMClient, {
  shadowDOM: false,
});

/**
 * [커스텀 엘리먼트 등록]
 */
customElements.define('ai-chatbot', WebChatbot);
customElements.define('ai-rag-manager', WebRagManager);

