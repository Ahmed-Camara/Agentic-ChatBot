# LangGraph Chatbot

A chat application built with LangGraph, LangChain, and Streamlit. It connects to a model through an OpenAI-compatible API; configure the API URL, model name, and API key using environment variables.

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
BASE_URL=......
MODEL=your-model-name
API_KEY=your-api-key
```

Replace the example values with the endpoint, model name, and API key provided by your model service. If the service does not require authentication, use a placeholder value if its OpenAI-compatible endpoint accepts one. Keep real credentials private: do not commit your `.env` file or paste API keys into source code. Start the model service before launching the application.

## Run the application

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

## How it works

- `app.py` provides the Streamlit chat interface and streams model responses.
- `agentic_chatbot.py` configures the model, defines the message state, and builds the LangGraph graph.
- `MemorySaver` stores checkpoints in memory while the process is running. Checkpoints are not persisted after the process stops.

## Dependencies

Python dependencies are listed in [`requirements.txt`](./requirements.txt).
