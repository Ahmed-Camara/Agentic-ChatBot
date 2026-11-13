# Agentic Chatbot

An agentic chatbot built with **LangGraph** and **Streamlit**. It can call tools (web search, calculator, stock prices, weather, date/time), answer questions about PDFs you upload (RAG with FAISS), and stop to ask for your approval before sensitive actions (human-in-the-loop). Conversations are saved in SQLite, so you can switch between threads and pick one up later.

## Features

- **Tool calling**: the LLM decides which tool to call through LangGraph's `ToolNode` and `tools_condition`.
- **RAG on PDFs**: you upload PDFs from the chat. They are split into chunks, embedded and stored in a FAISS index. The model then searches them with `rag_tool`.
- **Human-in-the-loop (HITL)**: the `purchase_stock` tool pauses the graph with `interrupt()` and waits for you to approve or reject in the UI.
- **Persistent conversations**: `SqliteSaver` stores checkpoints for each `thread_id`. You can reopen any past conversation from the sidebar.
- **Streaming UI**: answers stream token by token, and a status box shows which tool is running.

## Project structure

```text
ChatBot/
├── agentic_chatbot.py     # LangGraph graph: state, chat_node, tools, checkpointer
├── app_thread.py          # Main Streamlit UI (threads, uploads, HITL approval)
├── app.py                 # Minimal single-thread Streamlit UI
├── tools/
│   └── tool.py            # All LangChain tools (incl. rag_tool and purchase_stock)
├── rag/
│   ├── embedding.py       # OpenAI-compatible embeddings
│   ├── vector_store.py    # PDF ingestion → FAISS index
│   └── retriever.py       # Loads FAISS index and returns a retriever (k=4)
├── graph/, llm/           # Modules for a future refactor (not used by the app yet)
├── data/uploads/          # PDFs uploaded through the UI
├── docs/                  # Sample PDFs
├── db/
│   ├── thread/chatbot.db  # SQLite checkpoints (conversations)
│   └── rag_db/faiss_db/   # FAISS vector index
└── requirements.txt
```

## Tools

| Tool | Description | External service |
| --- | --- | --- |
| `web_search` | Searches the internet and returns title, URL and snippet | Tavily |
| `calculator` | Evaluates math expressions (with `math`, `abs`, `round`, `min`, `max`, `sum`) | — |
| `get_stock_price` | Latest quote for a stock symbol (e.g. `AAPL`) | Alpha Vantage |
| `get_current_weather` | Current weather for a city | OpenWeather |
| `get_datetime_information` | Current date/time, tomorrow, yesterday (default timezone `Africa/Abidjan`) | — |
| `rag_tool` | Returns relevant passages from the uploaded PDFs, with source and page | FAISS + embeddings |
| `purchase_stock` | **Simulated** stock purchase that requires human approval | — (simulation) |

## How it works

### Graph

```text
START → chat_node ──(tool calls?)──► tools ──► chat_node
                 └──(no tool calls)──► END
```

- `chat_node` adds a system prompt with tool-usage rules and calls the LLM, which is bound to the tools.
- `tools_condition` sends the flow to `tools` when the LLM requests a tool, and to `END` otherwise.
- Tool results go back to `chat_node`, which writes the final answer.
- The graph is compiled with a `SqliteSaver` checkpointer stored in `db/thread/chatbot.db`.

### Human-in-the-loop

The HITL logic lives inside the `purchase_stock` tool:

1. The tool calls `interrupt("Approve buying {quantity} shares of {symbol} ? (yes/no)")`, and the graph pauses in the `tools` node.
2. `app_thread.py` reads the pending interrupts from `chatbot.get_state(config).interrupts`. It shows an **Approval required** panel with **Approve** / **Reject** buttons, and hides the chat input until you decide.
3. The graph resumes with `Command(resume="yes")` or `Command(resume="no")`.
4. If you answered `"yes"`, the tool returns `status: success`. Otherwise it returns `status: cancelled`. The LLM then writes its answer from that result.

Because the pause is stored in the checkpointer, a pending approval is still there after a page refresh or when you switch back to that thread.

### RAG

1. When you upload a PDF in the chat, it is saved to `data/uploads/` with a unique prefix.
2. `ingest_rag_document()` loads it with `PyPDFLoader`, splits it with `RecursiveCharacterTextSplitter`, embeds the chunks and saves a FAISS index to `db/rag_db/faiss_db`.
3. `rag_tool` loads that index and returns the top 4 chunks for the query.

## Environment variables

Create a `.env` file at the project root:

```env
# Chat model (OpenAI-compatible endpoint)
BASE_URL=https://your-openai-compatible-endpoint
MODEL=your-model-name
API_KEY=your-api-key

# Embeddings (RAG)
EMBEDDING_BASE_URL=https://your-embedding-endpoint
EMBEDDING_MODEL=your-embedding-model

# Tools
TAVILY_API_KEY=your-tavily-key
ALPHA_VANTAGE=your-alpha-vantage-key
OPEN_WEATHER_API_KEY=your-openweather-key
```

`.env` and `db/` are listed in `.gitignore`. Never commit API keys.

## Installation

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked, call the venv interpreter directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Since `db/` is not versioned, create the database folders before the first run:

```powershell
New-Item -ItemType Directory -Force db\thread, db\rag_db
```

## Run

Main app (threads, PDF upload, HITL):

```powershell
streamlit run app_thread.py
```

Minimal app (single thread, no upload, no HITL panel):

```powershell
streamlit run app.py
```

## Try the HITL flow

1. Run `app_thread.py`.
2. Ask: *"Buy 10 shares of AAPL"*.
3. The **Approval required** panel appears. Click **Approve** or **Reject**.
4. The agent resumes and confirms or cancels the (simulated) order.

## Known limitations

- `purchase_stock` is a simulation. No real order is placed.
- HITL only covers `purchase_stock`. The other tools run without approval.
- Each new upload **replaces** the FAISS index, so only the most recently uploaded PDFs can be searched.
- The upload field accepts `docx`, `txt` and `csv`, but ingestion uses `PyPDFLoader`, so only PDFs are supported.
- `rag_tool` fails if no document has been uploaded yet, because the FAISS index does not exist.
- `app.py` does not handle interrupts. Use `app_thread.py` for the HITL flow.
- The `graph/` and `llm/` modules are placeholders for a future refactor.

## License

See [LICENSE](LICENSE).
