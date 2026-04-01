import json
import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import LLMFactory
from langgraph.checkpoint.memory import MemorySaver
from models.schemas import IntentClassification
from services.retrieval_service import RetrievalService

# [입문자 가이드] 
# LangGraph는 "상태(State)"를 관리하며 여러 단계를 거쳐 답변을 완성합니다.
# AgentState 클래스는 챗봇이 대화 도중 어떤 데이터를 '기억'하고 들고 다녀야 하는지 정의합니다.
class AgentState(TypedDict):
  # messages: 대화 기록입니다. Annotated와 add_messages를 쓰면 새로운 메시지가 올 때 
  # 기존 리스트를 덮어쓰지 않고 뒤에 차곡차곡 추가해줍니다.
  messages: Annotated[Sequence[BaseMessage], add_messages]
  session_id: str # 대화방 ID
  user_id: str    # 사용자 ID
  intent: str     # AI가 분석한 사용자의 의도 ('TUTOR' 학습용 또는 'CS' 상담용)

class ChatbotAgent:
    def __init__(self):
      """챗봇의 두뇌인 AI 모델과 지식 검색 도구를 준비합니다."""
      # 1. AI 모델(GPT-4o 등)을 가져옵니다. 0.2의 temperature는 답변의 일관성을 높여줍니다.
      self.llm = LLMFactory.get_chat_model(temperature=0.2)
      # 2. 관련 지식을 찾아주는 '검색 서비스(RAG)'를 준비합니다.
      self.retrieval_service = RetrievalService()
      # 3. 대화의 흐름도(Graph)를 그립니다.
      self.graph = self._build_graph()

    def _build_graph(self):
      """대화의 '논리 구조(Graph)'를 설계하고 조립합니다."""
      # 우리가 정의한 AgentState를 바탕으로 흐름도를 만듭니다.
      workflow = StateGraph(AgentState)
      
      # 1. 분기점(Node) 등록: 각 단계에서 어떤 함수를 실행할지 정합니다.
      workflow.add_node("router", self.node_router)      # 1단계: 질문 분석(의도 파악)
      workflow.add_node("tutor", self.node_tutor)        # 2단계(A): 학습 튜터 모드
      workflow.add_node("cs_support", self.node_cs)      # 2단계(B): CS 상담원 모드
      
      # 2. 시작점 설정: 질문이 들어오면 무조건 'router'부터 시작합니다.
      workflow.set_entry_point("router")
      
      # 3. 갈림길(Conditional Edge) 설정: router 분석 결과(TUTOR 또는 CS)에 따라 다른 길로 보냅니다.
      workflow.add_conditional_edges(
          "router",
          lambda state: state["intent"],
          {"TUTOR": "tutor", "CS": "cs_support"}
      )
      
      # 4. 마무리: 각 모드에서 답변을 마치면 대화를 끝(END)냅니다.
      workflow.add_edge("tutor", END)
      workflow.add_edge("cs_support", END)
      
      # 5. 메모리 기능 추가: MemorySaver는 이전 대화 내용을 기억하게 해줍니다.
      return workflow.compile(checkpointer=MemorySaver())

    async def node_router(self, state: AgentState):
      """사용자가 왜 말을 걸었는지(학습 질문인지, 서비스 문의인지) 분류합니다."""
      last_message = state["messages"][-1].content
      
      # 분류 작업은 빠르고 저렴한 'Flash' 모델을 사용합니다.
      base_llm = LLMFactory.get_chat_model(temperature=0, is_flash=True)
      # AI가 답변을 마음대로 하지 않고, 우리가 정한 구조(IntentClassification)로만 답하게 강제합니다.
      classifier_llm = base_llm.with_structured_output(IntentClassification)

      prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 지능형 상담 분류원입니다. 사용자의 질문을 정확히 분석하여 TUTOR(학습 질문) 또는 CS(일반 문의)로 분류하세요."),
        ("human", "{user_message}")
      ])
      
      try:
        # AI에게 분석을 시킵니다.
        result = await (prompt | classifier_llm).ainvoke({"user_message": last_message})
        return {"intent": result.intent}
      except Exception as e:
        print(f"의도 파악 중 오류 발생: {e}")
        return {"intent": "CS"} # 오류 시 기본값으로 '상담' 모드를 선택합니다.

    async def node_tutor(self, state: AgentState):
      """전문 학습 튜터로서 정답 대신 힌트와 원리를 설명합니다."""
      # 질문과 관련된 학습 지식을 검색해옵니다. (RAG)
      context = self.retrieval_service.get_combined_context(
        state["user_id"], state["messages"][-1].content, state["intent"]
      )
      
      # 튜터로서의 인격(Persona)과 행동 수칙을 주입합니다.
      sys_prompt = SystemMessage(content=f"""당신은 다정하고 명확한 AI 학습 튜터입니다. 
        [튜터링 원칙]
        1. 정답을 바로 말하지 말고, 학생이 스스로 생각할 수 있는 '힌트'를 먼저 주세요.
        2. 질문이 구체적이지 않으면 더 자세히 물어봐달라고 부드럽게 요청하세요.
        3. 자료에 없는 내용을 짐작해서 답하지 마세요.

        [학생을 위한 참고 자료]
        {context}""")


      full_content = ""
      # 한 글자씩 실시간으로 생성(Streaming)하며 모읍니다.
      async for chunk in self.llm.astream([sys_prompt] + state["messages"]):
        full_content += chunk.content
      
      # 최종 생성된 전체 문장을 대화 기록에 추가합니다.
      return {"messages": [AIMessage(content=full_content)]}

    async def node_cs(self, state: AgentState):
      """CS 상담원이 되어 공지사항이나 안내 가이드를 바탕으로 답변합니다."""
      context = self.retrieval_service.get_combined_context(
        state["user_id"], state["messages"][-1].content, state["intent"]
      )
      
      sys_prompt = SystemMessage(content=f"""당신은 빠르고 정확한 서비스 지원 상담원입니다. 
        [상담 수칙]
        1. 제공된 자료를 바탕으로 질문에 대해 정중하고 명확하게 답변하세요.
        2. 모르는 내용은 확인 후 안내해 드리겠다고 솔직하게 말씀하세요.
        3. 해결이 어려운 경우 상담원 연결을 안내하세요.

        [서비스 가이드 자료]
        {context}""")

      full_content = ""
      async for chunk in self.llm.astream([sys_prompt] + state["messages"]):
        full_content += chunk.content
      
      return {"messages": [AIMessage(content=full_content)]}

    async def achat_stream(self, session_id: str, user_id: str, message: str, on_complete=None):
      """AI의 생각을 한 글자씩 실시간(SSE)으로 프론트엔드에 전달합니다."""
      input_state = {
        "messages": [HumanMessage(content=message)],
        "session_id": session_id,
        "user_id": user_id
      }

      # 세션 ID를 'thread_id'로 넘겨주면, AI가 "아, 아까 대화하던 그 사람이구나!" 하고 기억합니다.
      config = {"configurable": {"thread_id": session_id}}

      full_response = ""
      final_intent = "UNKNOWN"

      # astream_events는 AI 내부에서 일어나는 모든 일을 실시간 이벤트로 받아옵니다.
      async for event in self.graph.astream_events(input_state, config, version="v2"):
        kind = event["event"]
        
        # 1. 의도 분석 단계가 끝났을 때: 어떤 모드(TUTOR/CS)인지 전송합니다.
        if kind == "on_chain_end" and event["name"] == "router":
          final_intent = event["data"]["output"].get("intent", "UNKNOWN")
          yield f"data: {json.dumps({'type': 'intent', 'intent': final_intent})}\n\n"

        # 2. 실시간 답변 생성 중: 생성되는 단어(Token)를 즉시 전송합니다.
        elif kind == "on_chat_model_stream":
          content = event["data"]["chunk"].content
          if content:
            full_response += content
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
      
      # 3. 모든 답변 생성이 완료되었을 때: 로그 저장 콜백을 실행합니다.
      if on_complete:
        await on_complete(full_response, final_intent)
        
      # 4. 전송 종료 알람
      yield f"data: {json.dumps({'type': 'end'})}\n\n"


