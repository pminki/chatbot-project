import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

# 다양한 AI 모델(OpenAI, Google Gemini 등)을 상황에 맞춰 생성해주는 '공장(Factory)' 클래스입니다.
# 프로그램의 다른 곳에서 어떤 모델을 쓸지 일일이 고민하지 않고, 이 공장에 요청만 하면 됩니다.
class LLMFactory:
  """
  환경 변수(LLM_PROVIDER) 설정값에 따라 OpenAI 또는 Google Vertex AI의
  대화형 모델(Chat)과 문장 수치화 모델(Embedding)을 동적으로 골라서 반환합니다.
  """
  
  @staticmethod
  def get_chat_model(temperature=0.2, model_name=None, is_flash=False):
    """
    실제로 대화를 나눌 '채팅 모델' 객체를 만들어줍니다.
    
    Args:
        temperature (float): 답변의 '온도' (0에 가까울수록 단호하고 정확하며, 1에 가까울수록 창의적이고 다양함)
        model_name (str): 사용할 특정 모델 이름 (지정하지 않으면 각 제공자의 기본 모델 사용)
        is_flash (bool): True일 경우 가벼운 모델(분류, 단순 작업용)을 사용합니다.
    """
    # 실행 환경(환경 변수)에서 어떤 AI 회사의 모델을 쓸지 확인합니다. (기본값은 openai)
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "vertexai":
      if model_name:
        target_model = model_name
      else:
        # 가벼운 분류 작업에는 'flash' 계열을, 깊이 있는 생각에는 'pro' 계열을 주로 씁니다.
        target_model = "gemini-2.5-flash" if is_flash else "gemini-2.5-flash-lite"
      
      return ChatVertexAI(
        model_name=target_model, 
        temperature=temperature,
        max_output_tokens=2048 # 모델이 한 번에 내놓을 답변의 최대 글자 수 조절
      )
    else:
      if model_name:
        target_model = model_name
      else:
        # 'gpt-4o-mini'는 속도가 매우 빠르고 비용이 저렴하여 챗봇 응대에 효율적입니다.
        target_model = "gpt-4o" if is_flash else "gpt-4o-mini"
      
      return ChatOpenAI(
        model=target_model, 
        temperature=temperature
      )


  @staticmethod
  def get_embeddings():
    """
    문장을 숫자의 나열(벡터)로 변환해주는 '임베딩 모델'을 만들어줍니다.
    이 숫자들이 있어야 '질문과 비슷한 문서'를 수학적으로 찾아낼 수 있습니다.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "vertexai":
      # Google의 한국어 포함 다국어 지원 임베딩 모델
      return VertexAIEmbeddings(model_name="text-multilingual-embedding-002")
    else:
      # OpenAI의 성능과 가성비가 좋은 최신 임베딩 모델
      return OpenAIEmbeddings(model="text-embedding-3-small")
