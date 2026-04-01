import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import reactToWebComponent from 'react-to-webcomponent'; // React 컴포넌트를 표준 웹 컴포넌트로 바꿔주는 도구입니다. 
import App from './App'; // 실제 채팅 화면이 담긴 메인 컴포넌트입니다.
import { RagManager } from './pages/RagManager'; // 지식 베이스를 관리하는 화면입니다.
import './index.css'; // Tailwind CSS를 포함한 스타일 시트를 불러옵니다.

/**
 * [Web Component 변환 설정]
 * 1. React 컴포넌트(App, RagManager)를 가져와서 브라우저가 기본적으로 이해할 수 있는 형태(Web Component)로 감쌉니다.
 * 2. 이렇게 하면 이 프로젝트가 아닌 다른 평범한 HTML 파일에서도 <ai-chatbot> 같은 태그로 이 기능을 쓸 수 있습니다.
 */

// 챗봇 컴포넌트를 웹 컴포넌트로 변환합니다.
const WebChatbot = reactToWebComponent(App, React, ReactDOMClient, {
  shadowDOM: false, // 스타일이 외부와 분리되지 않도록 설정합니다. (Tailwind CSS를 그대로 쓰기 위함)
});

// 관리자 화면 컴포넌트도 똑같이 변환합니다.
const WebRagManager = reactToWebComponent(RagManager, React, ReactDOMClient, {
  shadowDOM: false,
});

/**
 * [커스텀 엘리먼트 등록]
 * 브라우저에게 "이제부터 <ai-chatbot> 이라는 태그를 만나면 아까 만든 WebChatbot을 보여줘!"라고 등록하는 과정입니다.
 */
customElements.define('ai-chatbot', WebChatbot); // HTML에서 <ai-chatbot></ai-chatbot>으로 사용 가능
customElements.define('ai-rag-manager', WebRagManager); // HTML에서 <ai-rag-manager></ai-rag-manager>로 사용 가능

