# Agentic Chatbot

This repository is a small LangGraph + Streamlit chatbot project built around a main chatbot graph and a thread-based chat interface.

## Actual project structure

From the current workspace, the files present are:

- `agentic_chatbot.py` — main chatbot implementation
- `app.py` — simple single-thread chat UI
- `app_thread.py` — threaded chat UI with conversation history
- `requirements.txt` — Python dependencies
- `LICENSE` — project license
- `README.md` — project documentation
- `tools/tool.py` — placeholder tool module
- `db/chatbot.db` — SQLite database used by the chatbot checkpointing layer

## What the current code does

The active chatbot implementation in `agentic_chatbot.py` includes:

- LangGraph state graph with `StateGraph`
- `add_messages`-based message state management
- OpenAI-compatible model integration with `ChatOpenAI`
- Optional Gemini integration via `ChatGoogleGenerativeAI`
- `ToolNode` and `tools_condition` usage for tool-calling flows
- SQLite checkpoint persistence via `SqliteSaver`
- thread-aware chat support with `checkpoint.list(None)` and thread IDs

The app files are:

- `app.py`: minimal chat interface for direct conversations
- `app_thread.py`: conversation sidebar and thread switching based on stored checkpoints

## Tooling state

`agentic_chatbot.py` imports tool functions such as:

- `web_search`
- `calculator`
- `get_stock_price`
- `get_current_weather`
- `get_datetime_information`

These are expected to come from `tools/tool.py`, but that file currently only contains a minimal placeholder and does not yet implement the full tool set referenced by the chatbot. In other words, the project is in a semi-developed state: the graph and UI are present, but the tool layer is still incomplete.

## Environment variables

Create a `.env` file at the project root:

```env
BASE_URL=https://your-openai-compatible-endpoint
MODEL=your-model-name
API_KEY=your-api-key
GEM_MODEL=gemini-model-name
GEM_API_KEY=your-gemini-api-key
```

Notes:

- If you only use the OpenAI-compatible endpoint, the Gemini variables can be left unset.
- Do not commit `.env` to version control.
- Keep API keys private.

## Installation

From the project directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked, use the venv interpreter directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the app

### Simple version

```powershell
streamlit run app.py
```

### Threaded version

```powershell
streamlit run app_thread.py
```

Then open the local Streamlit URL in the browser.

## How it works

- `agentic_chatbot.py` defines the message state and builds the LangGraph workflow.
- The graph adds a `chat_node` and a `tools` node.
- The model is bound to tools with `model.bind_tools(tools)`.
- `tools_condition` decides whether to continue into the tool node.
- Results are sent back to the model for follow-up reasoning.
- `SqliteSaver` stores checkpoints in `db/chatbot.db`.
- `app_thread.py` retrieves saved threads and lets the user switch between conversations.

## Current project status

This project is a working prototype/learning project. It demonstrates:

- LangGraph graph setup
- message streaming and checkpoints
- thread management with SQLite
- tool-calling architecture in LangGraph
- Streamlit UI integration

It is not yet a fully finished production-ready agent application, and the tool implementations still need to be completed for the tool-calling flow to be fully operational.
