import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import reactToWebComponent from 'react-to-webcomponent';
import App from './App';
import './index.css';

/**
 * [Web Component 변환 설정]
 * React로 만든 <App /> 컴포넌트를 일반 HTML 태그처럼 쓸 수 있게 변환합니다.
 * 이를 통해 다른 웹사이트(HTML)에서도 <ai-chatbot></ai-chatbot> 태그만 넣으면 챗봇이 작동합니다.
 */
const WebChatbot = reactToWebComponent(App, React, ReactDOMClient, {
  shadowDOM: false, // 별도의 격리된 DOM(Shadow DOM)을 쓰지 않고 스타일을 공유하도록 설정
});

/**
 * [커스텀 엘리먼트 등록]
 * 브라우저에게 'ai-chatbot'이라는 이름의 새로운 태그가 정의되었음을 알립니다.
 */
customElements.define('ai-chatbot', WebChatbot);
