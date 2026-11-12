from graph.state import ChatState
from llm.model import llm_with_tools

def chat_node(state: ChatState):
    messages = state.messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages":[response]}