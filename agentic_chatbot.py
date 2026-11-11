from langchain_core.messages import SystemMessage, HumanMessage,BaseMessage
from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import List, Optional,Annotated,TypedDict
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
GEM_MODEL = os.getenv("GEM_MODEL")
API_KEY = os.getenv("API_KEY")
GEM_API_KEY = os.getenv("GEM_API_KEY")
config = {"configurable": {"thread_id": "chat-session-1"}}

model = ChatOpenAI(model=MODEL,
                   base_url=BASE_URL,temperature=0.7,verbose=True,api_key=API_KEY)
model2 = ChatGoogleGenerativeAI(model=GEM_MODEL, google_api_key=GEM_API_KEY)
class ChatState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    
def chat_node(state: ChatState):
    messages = state.messages
    
    response = model.invoke(messages)
    return {"messages":[response]}

checkpoint = MemorySaver()

graph = StateGraph(ChatState)

graph.add_node("chat_node",chat_node)


graph.add_edge(START,"chat_node")
graph.add_edge("chat_node",END)

chatbot = graph.compile(checkpointer=checkpoint)

"""
while True:
    user_input = input("Type here: ")
    if user_input.lower() in ["exit", "quit","q"]:
        break
    response = chatbot.invoke({"messages":[HumanMessage(content=user_input)]}, config=config)
    print("Bot:", response["messages"][-1].content)
"""
