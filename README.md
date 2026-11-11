# LangGraph Chatbot

A chat application built with LangGraph, LangChain, and Streamlit. It connects to a model through an OpenAI-compatible API; configure the API URL and model name using environment variables.

## Requirements

- Python 3.10 or later
- An OpenAI-compatible model API endpoint accessible from your machine

## Installation

From the project directory, create and activate a virtual environment in PowerShell, then install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell's execution policy prevents activation, install using the virtual environment's interpreter directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
BASE_URL=http://localhost:8000/v1
MODEL=your-model-name
```

Replace the URL with your model service's endpoint and `your-model-name` with a model it supports. Start the model service before launching the application.

## Run the application

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

## How it works

- `app.py` provides the Streamlit chat interface and streams model responses.
- `agentic_chatbot.py` configures the model, defines the message state, and builds the LangGraph graph.
- `MemorySaver` stores checkpoints in memory while the process is running. Checkpoints are not persisted after the process stops.

The `thread_id` is currently set to `chat-session-1` in `agentic_chatbot.py`. For separate conversations, use a distinct thread ID for each session.

## Dependencies

Python dependencies are listed in [`requirements.txt`](./requirements.txt).
