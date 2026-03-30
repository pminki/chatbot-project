from typing import TypedDict, Annotated, Sequence
import os  # 환경 변수(os.getenv) 사용을 위해 필요한 모듈입니다.
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from models.schemas import IntentClassification
from services.retrieval_service import RetrievalService
from core.llm_factory import LLMFactory

# 챗봇의 상태(데이터)를 정의하는 클래스입니다.
# LangGraph에서 노드들이 이 데이터를 공유하며 업데이트합니다.
class AgentState(TypedDict):
  # 대화 기록: 'add_messages'는 새로운 메시지를 기존 대화 리스트에 자동으로 덧붙여주는 역할을 합니다.
  messages: Annotated[Sequence[BaseMessage], add_messages]

  # 사용자 및 대화 세션 식별을 위한 고유 ID
  session_id: str
  user_id: str

  # 사용자의 의도 분석 결과 (예: 학습 질문, 단순 문의 등)
  intent: str

# 실제 챗봇의 지능과 대화 흐름(워크플로우)을 담당하는 메인 클래스입니다.
class ChatbotAgent:
    def __init__(self):
      # 1. LLM 모델 초기화: LLMFactory를 통해 현재 설정된 제공자(OpenAI, Vertex AI 등)의 모델을 가져옵니다.
      # temperature=0.2는 답변의 일관성과 정확도를 높이기 위한 설정입니다.
      self.llm = LLMFactory.get_chat_model(temperature=0.2)
      
      # 2. 정보 검색 서비스: 사용자의 질문에 답변하기 위해 필요한 지식(DB 등)을 찾아오는 도구입니다.
      self.retrieval_service = RetrievalService()
      
      # 3. 그래프 빌드: 대화의 논리적인 흐름도를 생성하고 실행 가능한 상태로 컴파일합니다.
      self.graph = self._build_graph()

    def _build_graph(self):
      """대화의 '지도(Graph)'를 그립니다. 어디서 시작하고 어디로 흐를지 정의합니다."""
      workflow = StateGraph(AgentState)
      
      # 각각의 독립된 작업 단계(Node)를 등록합니다.
      workflow.add_node("router", self.node_router)      # 의도 분석 단계
      workflow.add_node("tutor", self.node_tutor)        # 학습 도움말 작성 단계
      workflow.add_node("cs_support", self.node_cs)     # 고객 지원 응대 단계
      
      # 대화의 시작점(Entry Point)은 항상 'router'로 설정합니다.
      workflow.set_entry_point("router")
      
      # 조건부 연결(Conditional Edges): 'router' 단계의 결과(intent)에 따라 다음 갈 길을 정합니다.
      workflow.add_conditional_edges(
          "router",
          lambda state: state["intent"],  # 상태 정보 중 'intent' 값을 보고 판단합니다.
          {"TUTOR": "tutor", "CS": "cs_support"} # TUTOR면 tutor 노드로, CS면 cs_support 노드로!
      )
      
      # 응답 작성이 완료되면 대화를 종료(END)합니다.
      workflow.add_edge("tutor", END)
      workflow.add_edge("cs_support", END)
      
      return workflow.compile()

    def node_router(self, state: AgentState):
      """사용자가 보낸 메시지가 '무엇에 관한 것인지 (CS, TUTOR)' 분류하는 역할을 합니다."""
      last_message = state["messages"][-1].content
      
      # 의도 분류는 빠른 응답이 중요하므로, 가볍고 경제적인 모델(flash, mini)을 사용합니다.
      base_llm = LLMFactory.get_chat_model(
          temperature=0, 
          model_name="gemini-2.5-flash-lite" if os.getenv("LLM_PROVIDER") == "vertexai" else "gpt-4o-mini"
      )
      
      # LLM이 정해진 형식(IntentClassification)으로만 대답하도록 강제합니다.
      classifier_llm = base_llm.with_structured_output(IntentClassification)
      
      # 분류를 위한 구체적인 지시사항(Prompt)
      prompt = ChatPromptTemplate.from_messages([
        ("system", "사용자의 메시지를 분석하여 TUTOR(학습 질문, 내용 설명) 또는 CS(로그인, 버그, 오류 문의)로 분류하세요."),
        ("human", "{user_message}")
      ])
      
      try:
        # 지시사항과 모델을 결합하여 실행합니다.
        # 이 메시지만을 가지고 TUTOR인지 CS인지 LLM이 판별
        result = (prompt | classifier_llm).invoke({"user_message": last_message})
        return {"intent": result.intent}
      except Exception as e:
        # 예상치 못한 오류 발생 시, 가장 안전한 'CS' 분류로 처리합니다.
        print(f"의도 분류(라우팅) 실패: {e}")
        return {"intent": "CS"}

    def node_tutor(self, state: AgentState):
      """제공된 학습 자료를 바탕으로 학생에게 힌트와 설명을 제공합니다."""
      # 질문과 관련된 학습 데이터(Context)를 검색해옵니다.
      context = self.retrieval_service.get_combined_context(
        state["user_id"], 
        state["messages"][-1].content, 
        state["intent"]
      )
      
      # AI의 성격과 지켜야 할 규칙을 설정합니다. (할루시네이션(가짜 답변) 방지 중심)
      sys_prompt = SystemMessage(content=f"""당신은 친절한 AI 학습 튜터입니다.
        정답 대신 힌트로 유도하세요.

        [튜터링 원칙]
        1. 절대 정답을 바로 알려주지 마세요. 
        2. 학생이 틀린 답을 하거나 모른다고 할 경우, 개념을 잘게 쪼개어 힌트를 제공하세요.
        3. 칭찬과 격려를 아끼지 마세요.
        4. 한 번에 너무 많은 정보를 주지 말고, 학생이 소화할 수 있는 만큼만 설명한 뒤 질문을 던지세요.

        [엄격한 제약 사항]
        1. 제공된 [참고 자료]에 없거나 당신이 확실히 알지 못하는 정보라면, 절대 지어내지 마세요.
        2. 모르는 질문에는 반드시 "제가 아직 학습하지 못한 내용입니다. 확인 후 안내해 드리겠습니다."라고 솔직하게 답변하세요.

        {context}""")

      # 시스템 지시문과 지금까지의 대화 기록을 합쳐 LLM에게 전달합니다.
      response = self.llm.invoke([sys_prompt] + state["messages"])
      return {"messages": [response]}

    def node_cs(self, state: AgentState):
      """서비스 이용 관련 문의에 대해 공식 안내 자료를 기반으로 답변합니다."""
      context = self.retrieval_service.get_combined_context(
          state["user_id"], 
          state["messages"][-1].content, 
          state["intent"]
      )
      
      # 상담원으로서의 정체성과 한계를 설정합니다.
      sys_prompt = SystemMessage(content=f"""당신은 전문 CS 상담원입니다. 

        [엄격한 제약 사항]
        1. 제공된 [참고 자료]에 근거하여 안내하세요.
        2. 자료에 없는 오류나 모르는 내용에 대해서는 임의로 답변하지 말고 "해당 내용은 운영팀에서 확인 후 답변드리겠습니다."라고 안내하세요.

        {context}""")

      response = self.llm.invoke([sys_prompt] + state["messages"])
      return {"messages": [response]}

    def chat(self, session_id: str, user_id: str, message: str):
      """사용자의 입력을 받아 전체 그래프(워크플로우)를 실행하고 최종 답변을 반환합니다."""
      # 그래프 실행 시작
      result = self.graph.invoke({
        "messages": [HumanMessage(content=message)],
        "session_id": session_id,
        "user_id": user_id
      })
      
      # 최종 응답 내용과 판별된 의도를 반환합니다.
      return {
          "response": result["messages"][-1].content, 
          "intent": result.get("intent", "UNKNOWN")
      }
