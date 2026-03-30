export interface ChatRequest {
  session_id: string;
  user_id: string;
  message: string;
}

export interface ChatResponse {
  response: string;
  intent: string;
}