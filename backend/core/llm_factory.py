import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

class LLMFactory:
    """
    환경 변수(LLM_PROVIDER)에 따라 OpenAI 또는 Vertex AI의
    Chat 모델과 Embedding 모델을 동적으로 반환하는 팩토리 클래스
    """
    
    @staticmethod
    def get_chat_model(temperature=0.2, model_name=None):
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "vertexai":
            # Vertex AI의 Gemini 모델 (의도 분류 등은 flash, 복잡한 추론은 pro 추천)
            target_model = model_name or "gemini-2.5-flash-lite"
            return ChatVertexAI(
                model_name=target_model, 
                temperature=temperature,
                max_output_tokens=2048
            )
        else:
            # 기본 OpenAI 모델
            target_model = model_name or "gpt-4o-mini"
            return ChatOpenAI(
                model=target_model, 
                temperature=temperature
            )

    @staticmethod
    def get_embeddings():
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "vertexai":
            # Vertex AI 텍스트 임베딩 모델
            return VertexAIEmbeddings(model_name="text-multilingual-embedding-002")
        else:
            # OpenAI 임베딩 모델
            return OpenAIEmbeddings(model="text-embedding-3-small")