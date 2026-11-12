import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools.tool import web_search,calculator,get_stock_price,get_current_weather,get_datetime_information

load_dotenv()


BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
GEM_MODEL = os.getenv("GEM_MODEL")
API_KEY = os.getenv("API_KEY")
GEM_API_KEY = os.getenv("GEM_API_KEY")
config = {"configurable": {"thread_id": "chat-session-1"},"run_name":"chat_trace"}


tools = [web_search,calculator,get_stock_price,get_current_weather,get_datetime_information]

model = ChatOpenAI(model=MODEL,
                   base_url=BASE_URL,temperature=0.7,verbose=True,api_key=API_KEY)

llm_with_tools = model.bind_tools(tools)
