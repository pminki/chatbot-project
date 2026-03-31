import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ChatPage } from './pages/ChatPage';

/**
 * [App 컴포넌트 프롭스]
 */
export interface AppProps {
  userId?: string;
}

/**
 * [App 컴포넌트]
 * 전체 웹 애플리케이션의 뼈대(Shell)를 형성합니다.
 */
export const App: React.FC<AppProps> = ({ userId }) => {
  return (
    /**
     * [MemoryRouter]
     * 일반적인 주소창(BrowserRouter) 대신 메모리 상에서 페이지 이동을 관리합니다.
     * 챗봇처럼 다른 사이트에 '삽입'되어 작동하는 경우, 브라우저 주소창을 건드리면 안 되기 때문에 사용합니다.
     */
    <MemoryRouter initialEntries={['/']} future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <Routes>
        {/* '/' 경로(기본 페이지)로 접속했을 때 ChatPage 컴포넌트를 보여줍니다. */}
        <Route path="/" element={<ChatPage userId={userId} />} />
      </Routes>
    </MemoryRouter>
  );
};


export default App;
