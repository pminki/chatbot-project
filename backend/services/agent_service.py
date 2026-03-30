import json
import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import LLMFactory
from models.schemas import IntentClassification
from services.retrieval_service import RetrievalService

# [입문자 가이드] 
# LangGraph는 "상태(State)"를 관리하며 여러 단계를 거쳐 답변을 완성합니다.
# 이 클래스는 챗봇이 어떤 데이터를 들고 다녀야 하는지 정의합니다.
class AgentState(TypedDict):
  # 대화 기록: 새로운 메시지가 오면 기존 리스트에 자동으로 추가(add_messages)됩니다.
  messages: Annotated[Sequence[BaseMessage], add_messages]
  session_id: str
  user_id: str
  intent: str # 'TUTOR' 혹은 'CS' 분류 결과

class ChatbotAgent:
    def __init__(self):
      # AI 모델과 검색 도구를 준비합니다.
      self.llm = LLMFactory.get_chat_model(temperature=0.2)
      self.retrieval_service = RetrievalService()
      self.graph = self._build_graph()

    def _build_graph(self):
      """대화의 '논리 구조(Graph)'를 조립합니다."""
      workflow = StateGraph(AgentState)
      
      # 1. 작업 단계(Node) 등록
      workflow.add_node("router", self.node_router)
      workflow.add_node("tutor", self.node_tutor)
      workflow.add_node("cs_support", self.node_cs)
      
      # 2. 시작점 설정
      workflow.set_entry_point("router")
      
      # 3. 갈림길(Conditional Edge) 설정: intent 값에 따라 길을 나눕니다.
      workflow.add_conditional_edges(
          "router",
          lambda state: state["intent"],
          {"TUTOR": "tutor", "CS": "cs_support"}
      )
      
      # 4. 마무리 연결
      workflow.add_edge("tutor", END)
      workflow.add_edge("cs_support", END)
      
      return workflow.compile()

    async def node_router(self, state: AgentState):
      """사용자의 의도를 분석하여 TUTOR 혹은 CS로 분류합니다."""
      last_message = state["messages"][-1].content
      
      # 분석 전용 가벼운 모델 사용
      provider = os.getenv("LLM_PROVIDER", "openai")
      model_name = "gemini-1.5-flash" if provider == "vertexai" else "gpt-4o-mini"
      base_llm = LLMFactory.get_chat_model(temperature=0, model_name=model_name)
      classifier_llm = base_llm.with_structured_output(IntentClassification)
      
      prompt = ChatPromptTemplate.from_messages([
        ("system", "사용자의 의도를 TUTOR(학습 지원) 또는 CS(서비스 지원)로 분류하세요."),
        ("human", "{user_message}")
      ])
      
      try:
        # ainvoke를 통해 비동기로 결과를 받아옵니다.
        result = await (prompt | classifier_llm).ainvoke({"user_message": last_message})
        return {"intent": result.intent}
      except Exception as e:
        print(f"Routing Error: {e}")
        return {"intent": "CS"}

    async def node_tutor(self, state: AgentState):
      """학습 도우미로서 힌트와 설명을 제공합니다."""
      context = self.retrieval_service.get_combined_context(
        state["user_id"], state["messages"][-1].content, state["intent"]
      )
      
      sys_prompt = SystemMessage(content=f"""당신은 AI 학습 튜터입니다. 
        직접적인 답 대신 힌트를 주세요. 자료에 없는 내용은 모른다고 답하세요.
        {context}""")

      # [스트리밍 트릭] 
      # astream으로 한 글자씩 생성하고, 최종 결과를 모아서 상태를 업데이트합니다.
      # 이렇게 하면 외부(astream_events)에서 실시간 글자들을 가로챌 수 있습니다.
      full_content = ""
      async for chunk in self.llm.astream([sys_prompt] + state["messages"]):
        full_content += chunk.content
      
      return {"messages": [AIMessage(content=full_content)]}

    async def node_cs(self, state: AgentState):
      """서비스 문의에 대해 안내 자료를 기반으로 답변합니다."""
      context = self.retrieval_service.get_combined_context(
        state["user_id"], state["messages"][-1].content, state["intent"]
      )
      
      sys_prompt = SystemMessage(content=f"당신은 전문 CS 상담원입니다. 제공된 자료로만 답하세요.\n{context}")

      full_content = ""
      async for chunk in self.llm.astream([sys_prompt] + state["messages"]):
        full_content += chunk.content
      
      return {"messages": [AIMessage(content=full_content)]}

    async def achat_stream(self, session_id: str, user_id: str, message: str, on_complete=None):
      """
      AI의 답변을 스트리밍 방식으로 생성하고, 완료 후 콜백을 실행합니다.
      """
      input_state = {
        "messages": [HumanMessage(content=message)],
        "session_id": session_id,
        "user_id": user_id
      }

      full_response = ""
      final_intent = "UNKNOWN"

      async for event in self.graph.astream_events(input_state, version="v2"):
        kind = event["event"]
        
        if kind == "on_chain_end" and event["name"] == "router":
          final_intent = event["data"]["output"].get("intent", "UNKNOWN")
          yield f"data: {json.dumps({'type': 'intent', 'intent': final_intent})}\n\n"

        elif kind == "on_chat_model_stream":
          content = event["data"]["chunk"].content
          if content:
            full_response += content
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
      
      # 3. 모든 작업이 끝났을 때 콜백(예: DB 저장) 실행
      if on_complete:
        await on_complete(full_response, final_intent)
        
      yield f"data: {json.dumps({'type': 'end'})}\n\n"


