from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from models.schemas import IntentClassification
from services.retrieval_service import RetrievalService

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    user_id: str
    intent: str

class ChatbotAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.retrieval_service = RetrievalService()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("router", self.node_router)
        workflow.add_node("tutor", self.node_tutor)
        workflow.add_node("cs_support", self.node_cs)
        
        workflow.set_entry_point("router")
        workflow.add_conditional_edges(
            "router",
            lambda state: state["intent"],
            {"TUTOR": "tutor", "CS": "cs_support"}
        )
        workflow.add_edge("tutor", END)
        workflow.add_edge("cs_support", END)
        return workflow.compile()

    def node_router(self, state: AgentState):
        last_message = state["messages"][-1].content
        classifier_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(IntentClassification)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "사용자의 메시지를 분석하여 TUTOR(학습 질문, 내용 설명) 또는 CS(로그인, 버그, 오류 문의)로 분류하세요."),
            ("human", "{user_message}")
        ])
        try:
            result = (prompt | classifier_llm).invoke({"user_message": last_message})
            return {"intent": result.intent}
        except:
            return {"intent": "CS"}

    def node_tutor(self, state: AgentState):
        context = self.retrieval_service.get_combined_context(state["user_id"], state["messages"][-1].content, state["intent"])
        
        # 프롬프트에 '모를 때의 행동 지침'을 강력하게 추가합니다.
        sys_prompt = SystemMessage(content=f"""당신은 친절한 AI 학습 튜터입니다.
          정답 대신 힌트로 유도하세요.

          [엄격한 제약 사항]
          1. 제공된 [참고 자료]에 없거나 당신이 확실히 알지 못하는 정보라면, 절대 지어내지 마세요.
          2. 모르는 질문에는 반드시 "제가 아직 학습하지 못한 내용입니다. 확인 후 안내해 드리겠습니다."라고 솔직하게 답변하세요.

          {context}""")

        response = self.llm.invoke([sys_prompt] + state["messages"])
        return {"messages": [response]}

    def node_cs(self, state: AgentState):
        context = self.retrieval_service.get_combined_context(state["user_id"], state["messages"][-1].content, state["intent"])
        
        # CS 프롬프트에도 동일한 제약 사항 추가
        sys_prompt = SystemMessage(content=f"""당신은 전문 CS 상담원입니다. 

          [엄격한 제약 사항]
          1. 제공된 [참고 자료]에 근거하여 안내하세요.
          2. 자료에 없는 오류나 모르는 내용에 대해서는 임의로 답변하지 말고 "해당 내용은 시스템지원팀에 접수하여 확인해 드리겠습니다."라고 안내하세요.

          {context}""")

        response = self.llm.invoke([sys_prompt] + state["messages"])
        return {"messages": [response]}

    def chat(self, session_id: str, user_id: str, message: str):
        result = self.graph.invoke({
            "messages": [HumanMessage(content=message)],
            "session_id": session_id,
            "user_id": user_id
        })
        return {"response": result["messages"][-1].content, "intent": result.get("intent", "UNKNOWN")}