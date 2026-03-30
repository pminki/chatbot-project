import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ChatPage } from './pages/ChatPage';

export const App: React.FC = () => {
  return (
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<ChatPage />} />
      </Routes>
    </MemoryRouter>
  );
};
export default App;