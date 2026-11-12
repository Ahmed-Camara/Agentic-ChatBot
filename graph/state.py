from pydantic import BaseModel
from typing import Annotated,List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]