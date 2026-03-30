import { ChatRequest, ChatResponse } from '../types/chat';

// Docker 환경에서 Nginx를 통하거나 로컬 테스트용 프록시 URL
const API_BASE_URL = 'http://localhost:8000/api';

export const ChatService = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return await response.json();
  }
};