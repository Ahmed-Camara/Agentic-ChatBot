from langchain_core.messages import SystemMessage,BaseMessage,AIMessage
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from typing import List,Annotated
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3
from langgraph.prebuilt import ToolNode,tools_condition
from tools.tool import web_search,calculator,get_stock_price,get_current_weather,purchase_stock,get_datetime_information,rag_tool
from langgraph.types import interrupt,Command
tools = [web_search,calculator,get_stock_price,get_current_weather,
         rag_tool,purchase_stock,get_datetime_information]

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
GEM_MODEL = os.getenv("GEM_MODEL")
API_KEY = os.getenv("API_KEY")
GEM_API_KEY = os.getenv("GEM_API_KEY")

config = {"configurable": {"thread_id": "chat-session-1"},"run_name":"chat_trace"}

model = ChatOpenAI(model=MODEL,
                   base_url=BASE_URL,temperature=0.7,
                   verbose=True,api_key=API_KEY)

llm_with_tools = model.bind_tools(tools)

class ChatState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    
"""
def chat_node(state: ChatState):
    messages = state.messages
    response = llm_with_tools.invoke(messages)
    return {"messages":[response]}
"""

def chat_node(state: ChatState):
    system_message = SystemMessage(
        content=(
            "You are a helpful Agentic Chatbot with access to several tools.\n\n"
            "Tool usage instructions:\n"
            "- Use rag_tool for questions about the uploaded PDF or document.\n"
            "Always retrieve relevant document content before answering PDF-related questions.\n"
            "- Use web_search for current events, recent information, or information that requires an internet search.\n"
            "- Use calculator for mathematical calculations. Do not calculate complex expressions manually when the calculator is available.\n"
            "- Use get_stock_price when the user asks for the current price of a stock.\n"
            "- Use get_current_weather when the user asks about current weather for a location.\n"
            "Answer general questions directly when no tool is required.\n"
            "Do not invent information from the uploaded documents.\n"
            "If the user asks abour a PDF but no document is available, ask them to upload a PDF.\n"
            "Always give answer with its sources.\n"
            "After receiving a tool result, provide a clear and helpful final answer."
        )
    )
    messages = [
        system_message,*state.messages
    ]
    response = llm_with_tools.invoke(messages)
    return {"messages":[response]}

tool_node = ToolNode(tools)

connection = sqlite3.connect(database="db/thread/chatbot.db",check_same_thread=False)
checkpoint = SqliteSaver(connection)

graph = StateGraph(ChatState)

graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)


graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)

graph.add_edge("tools","chat_node")

chatbot = graph.compile(checkpointer=checkpoint)


def get_all_threads():
    all_threads = set()
    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config["configurable"]["thread_id"])
    return list(all_threads)