import React from 'react';
import * as ReactDOMClient from 'react-dom/client';
import reactToWebComponent from 'react-to-webcomponent';
import App from './App';

const WebChatbot = reactToWebComponent(App, React, ReactDOMClient, {
  shadowDOM: false,
});

customElements.define('ai-chatbot', WebChatbot);