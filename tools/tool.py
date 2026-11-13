from langchain.tools import tool
from dotenv import load_dotenv
from langgraph.types import interrupt,Command
import math
import requests
from tavily import TavilyClient
import os
from typing import Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rag.retriever import get_retriever
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MODEL = os.getenv("MODEL")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
ALPHA_VANTAGE = os.getenv("ALPHA_VANTAGE")
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
tavily = TavilyClient(api_key = TAVILY_API_KEY)

@tool
def web_search(query : str) -> str:
    """Search over the internet for recent and reliable information on a topic. Returns Titles, URLs, and Contents"""
    results = tavily.search(query=query,max_results=1,search_depth="advanced",topic="general")
    print(f"Search results for query : {query}")
    
    response = []
    
    for r in results["results"]:
        print(r)
        response.append(
            f"Title: {r['title']}\nURL:{r['url']}\nSnippet: {r['content'][:300]}\n"
        )
    return "\n----\n".join(response)

@tool
def calculator(expression : str) -> str:
    """
        Useful for simple math calculations.
        Input should be a valid match expression.
        Example: 2 + 2, math.sqrt(16), 10 * 5
    """
    try:
        allowed = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max":max,
            "sum":sum
        }
        
        result = eval(expression, {"__builtins__":{}},allowed)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
    
    
@tool
def get_stock_price(symbol : str) -> dict:
    """
        Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
        using Alpha Vantage with API Key in the URL.
    """
    
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE}"
    
    res = requests.get(url)
    return res.json()


@tool
def get_current_weather(location : str)->str:
    """
        Get the current real-time weather for a given city or location.
        Args:
            location: City or location name, for example:
                "Abidjan","London, UK", or "Mew York, US"
        
        Returns:
            A formatted current weather report.
    """
    
    if not OPEN_WEATHER_API_KEY:
        return (
            "Weather API Key is missing."
            "Set the OPEN_WEATHER_API_KEY environment variable."
        )
    
    try:
        geocoding_url = "https://api.openweathermap.org/geo/1.0/direct"
        geocoding_params = {
            "q": location,
            "limit": 1,
            "appid":OPEN_WEATHER_API_KEY
        }
        
        geo_response = requests.get(geocoding_url,params=geocoding_params,timeout=10)
        
        locations: list[dict[str,Any]] = geo_response.json()
        
        if not locations:
            return f"Could not find the location : {location}"
        
        latitude = locations[0]["lat"]
        longitude = locations[0]["lon"]
        resolved_name = locations[0].get("name",location)
        country = locations[0].get("country","")
        state = locations[0].get("state","")
        
        weather_url = "https://api.openweathermap.org/data/2.5/weather"
        
        weather_params = {
            "lat":latitude,
            "lon":longitude,
            "appid":OPEN_WEATHER_API_KEY,
            "units":"metric",
        }
        
        weather_response = requests.get(weather_url,params=weather_params,timeout=10)
        
        weather_response.raise_for_status()
        
        weather_data = weather_response.json()
        
        temperature = weather_data["main"]["temp"]
        feels_like = weather_data["main"]["feels_like"]
        humidity = weather_data["main"]["humidity"]
        pressure = weather_data["main"]["pressure"]
        description = weather_data["weather"][0]["description"]
        wind_speed = weather_data.get("wind",{}).get("speed","N/A")
        visibility_meters  = weather_data.get("visibility")
        
        visibility_km = (
            round(visibility_meters / 1000,1) if visibility_meters is not None else "N/A"
        )
        
        location_parts = [resolved_name]
        
        if state:
            location_parts.append(state)
        
        if country:
            location_parts.append(country)
        
        display_location = ", ".join(location_parts)
        
        return (
            f"Current weather in {display_location}:\n"
            f"- Condition: {description.title()}\n"
            f"- Temperature: {temperature}\n"
            f"- Feels like: {feels_like}\n"
            f"- Humididty: {humidity}%\n"
            f"- Pressure: {pressure} hPa\n"
            f"- Wind speed: {wind_speed} m/s\n"
            f"- visibility: {temperature} km"
        )
    
    except requests.Timeout:
        return "The weather service request time out. Please try again."
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response else "unknown"
        
        if status_code == 401:
            return "The OpenWeather API key is invalid or inactive"
        
        return f"Weather API returned an HTTP error : {status_code}"
    
    except requests.RequestException as error:
        return f"Could not connect to the weather service: {error}"
    except (KeyError,TypeError,ValueError) as error:
        return f"Unexpected weather API response: {error}"
    





@tool
def get_datetime_information(
    query: str,
    timezone: str = "Africa/Abidjan"
) -> str:
    """
    Get real-time date and time information.

    Args:
        query: The temporal information requested.
               Examples:
               - Today's date
               - Current time
               - What day is today?
               - Tomorrow's date
               - Date 15 days from now
               - Current year

        timezone: IANA timezone. Defaults to Africa/Abidjan.

    Returns:
        Current date and time information or a calculated date.
    """
    try:
        now = datetime.now(ZoneInfo(timezone))

        today = now.date()

        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        return (
            f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Timezone: {timezone}\n"
            f"Today's date: {today.strftime('%A, %d %B %Y')}\n"
            f"Current year: {today.year}\n"
            f"Current month: {today.strftime('%B')}\n"
            f"Day of the week: {today.strftime('%A')}\n"
            f"Tomorrow: {tomorrow.strftime('%A, %d %B %Y')}\n"
            f"Yesterday: {yesterday.strftime('%A, %d %B %Y')}"
        )

    except Exception as error:
        return f"Could not retrieve date and time information: {error}"
    
 
@tool
def rag_tool(query: str) -> str:
    """
        Retrieve relevant information from the PDF document.
        
        Use this tool when the user asks factual or conceptual questions that may be
        answered using the stored PDF documents.
        
        Args:
            query: The question or search query used to retrieve PDF content.
    """
    retriever = get_retriever()
    documents = retriever.invoke(query)
    
    if not documents:
        return "No relevant information was found in the PDF."
    
    formatted_documents = []
    
    for index, document in enumerate(documents,start=1):
        source = document.metadata.get("source","unknown source")
        page = document.metadata.get("page","unknown page")
        
        formatted_documents.append(
            f"Document {index}\n"
            f"Source {source}\n"
            f"Page {page}\n"
            f"Content {document.page_content}\n"
        )
    
    return "\n\n".join(formatted_documents)
    

@tool
def purchase_stock(symbol: str, quantity: int) -> dict:
    """
        Simulate purchasing a given quantity of a stock symbol.
        
        HUMAN-IN-THE-LOOP:
        Before confirming the purchase, this tool will interrupt
        and wait for a human decision ("yes" / anything else).
    """
    decision = interrupt(f"Approve buying {quantity} shares of {symbol} ? (yes/no)")
    
    if isinstance(decision,str) and decision.lower() == "yes":
        return {
            "status":"success",
            "message": f"Purchase order placed for {quantity} shares of {symbol}.",
            "symbol":symbol,
            "quantity":quantity
        }
    else:
        return {
                    "status":"cancelled",
                    "message": f"Purchase order placed for {quantity} shares of {symbol} was declined.",
                    "symbol":symbol,
                    "quantity":quantity
                }
    