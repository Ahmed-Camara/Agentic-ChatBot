from langchain_core.messages import SystemMessage, HumanMessage,BaseMessage
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import List, Optional,Annotated,TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_tavily import TavilySearch
from tools.tool import web_search,calculator,get_stock_price,get_current_weather,get_datetime_information

tools = [web_search,calculator,get_stock_price,get_current_weather,get_datetime_information]

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
GEM_MODEL = os.getenv("GEM_MODEL")
API_KEY = os.getenv("API_KEY")
GEM_API_KEY = os.getenv("GEM_API_KEY")
config = {"configurable": {"thread_id": "chat-session-1"},"run_name":"chat_trace"}

model = ChatOpenAI(model=MODEL,
                   base_url=BASE_URL,temperature=0.7,verbose=True,api_key=API_KEY)
model2 = ChatGoogleGenerativeAI(model=GEM_MODEL, google_api_key=GEM_API_KEY)


llm_with_tools = model.bind_tools(tools)

class ChatState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    
def chat_node(state: ChatState):
    messages = state.messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages":[response]}

tool_node = ToolNode(tools)

connection = sqlite3.connect(database="db/chatbot.db",check_same_thread=False)
checkpoint = SqliteSaver(connection)

graph = StateGraph(ChatState)

graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)


graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)

graph.add_edge("tools","chat_node")

#graph.add_edge("chat_node",END)
#graph.add_edge("tools",END)

chatbot = graph.compile(checkpointer=checkpoint)


def get_all_threads():
    all_threads = set()
    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config["configurable"]["thread_id"])
    
    return list(all_threads)