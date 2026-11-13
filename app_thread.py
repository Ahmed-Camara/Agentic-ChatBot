
from agentic_chatbot import chatbot, get_all_threads
from rag.vector_store import ingest_rag_document

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    AIMessageChunk
)

from langgraph.types import Command

import streamlit as st
import uuid
import os


# =====================================================
# INITIALISATION
# =====================================================

def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():
    st.session_state["message_history"] = []
    st.session_state["thread_id"] = generate_thread_id()
    add_thread(st.session_state["thread_id"])


st.title("Agentic Chatbot")


if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = get_all_threads()

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()


# =====================================================
# CONFIG LANGGRAPH
# =====================================================

def get_config():
    return {
        "configurable": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_trace"
    }


def load_conversation(thread_id):
    state = chatbot.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get("messages", [])


# =====================================================
# SIDEBAR - CONVERSATIONS
# =====================================================

st.sidebar.title("My Conversations")

if st.sidebar.button("New Chat"):
    reset_chat()
    st.rerun()


for thread_id in st.session_state["chat_threads"][::-1]:

    if st.sidebar.button(str(thread_id), key=thread_id):

        st.session_state["thread_id"] = thread_id

        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:

            if isinstance(message, HumanMessage):
                role = "user"

            elif isinstance(message, AIMessage):
                role = "assistant"

            else:
                continue

            temp_messages.append({
                "role": role,
                "content": message.content
            })

        st.session_state["message_history"] = temp_messages

        st.rerun()


# =====================================================
# STREAMING LANGGRAPH
# =====================================================

def stream_agent(agent_input, config):

    status_holder = {"box": None}

    def ai_only_stream():

        for message_chunk, metadata in chatbot.stream(
            agent_input,
            config=config,
            stream_mode="messages"
        ):

            # Suivre les tools
            if isinstance(message_chunk, ToolMessage):

                tool_name = getattr(
                    message_chunk,
                    "name",
                    "tool"
                )

                if status_holder["box"] is None:

                    status_holder["box"] = st.status(
                        f"Using {tool_name}...",
                        expanded=True
                    )

                else:

                    status_holder["box"].update(
                        label=f"Using {tool_name}...",
                        state="running",
                        expanded=True
                    )

            # Ignorer les appels de tools
            if isinstance(message_chunk, AIMessageChunk):

                if message_chunk.tool_call_chunks:
                    continue

                if message_chunk.tool_calls:
                    continue

                content = message_chunk.content

                if content:
                    yield content

        if status_holder["box"] is not None:

            status_holder["box"].update(
                label="Task completed",
                state="complete",
                expanded=False
            )

    return st.write_stream(ai_only_stream())


# =====================================================
# AFFICHAGE DE L'HISTORIQUE
# =====================================================

for message in st.session_state["message_history"]:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =====================================================
# DETECTION HITL
# =====================================================

config = get_config()

current_state = chatbot.get_state(config)

pending_interrupts = current_state.interrupts


# =====================================================
# INTERFACE HUMAN-IN-THE-LOOP
# =====================================================

if pending_interrupts:

    st.divider()

    st.warning(
        "Human intervention required. "
        "The agent is waiting for your decision."
    )

    for index, interrupt_obj in enumerate(pending_interrupts):

        interrupt_message = interrupt_obj.value

        with st.container(border=True):

            st.subheader("Approval required")

            st.markdown("**Agent request:**")

            st.info(str(interrupt_message))

            st.markdown(
                "Do you authorize the execution of this operation?"
            )

            col1, col2 = st.columns(2)

            # =========================================
            # APPROVE
            # =========================================

            with col1:

                approve = st.button(
                    "Approve",
                    key=f"approve_{st.session_state['thread_id']}_{index}",
                    type="primary",
                    use_container_width=True
                )

            # =========================================
            # REJECT
            # =========================================

            with col2:

                reject = st.button(
                    "Reject",
                    key=f"reject_{st.session_state['thread_id']}_{index}",
                    use_container_width=True
                )

            # =========================================
            # RESUME LANGGRAPH
            # =========================================

            if approve or reject:

                decision = "yes" if approve else "no"

                with st.chat_message("assistant"):

                    with st.spinner(
                        "Resuming agent execution..."
                    ):

                        ai_message = stream_agent(
                            Command(resume=decision),
                            config
                        )

                if ai_message:

                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": ai_message
                    })

                st.rerun()


# =====================================================
# CHAT INPUT + MULTIPLE FILE UPLOAD
# =====================================================

if not pending_interrupts:

    chat_submission = st.chat_input(
        "Message or upload documents...",
        accept_file="multiple",
        file_type=["pdf", "docx", "txt", "csv"]
    )

    if chat_submission is not None:

        user_input = chat_submission.text or ""
        uploaded_files = chat_submission.files or []

        display_content = ""

        if uploaded_files:

            display_content += "**Documents attached:**\n"

            for uploaded_file in uploaded_files:
                display_content += f"- 📎 {uploaded_file.name}\n"

        if user_input.strip():
            display_content += "\n" + user_input

        # =============================================
        # AFFICHAGE MESSAGE UTILISATEUR
        # =============================================

        if display_content:

            st.session_state["message_history"].append({
                "role": "user",
                "content": display_content
            })

            with st.chat_message("user"):
                st.markdown(display_content)

        # =============================================
        # INGESTION DOCUMENTS RAG
        # =============================================

        if uploaded_files:

            os.makedirs("data/uploads", exist_ok=True)

            with st.status(
                "Processing uploaded documents...",
                expanded=True
            ) as status:

                successful_files = []
                failed_files = []

                for uploaded_file in uploaded_files:

                    original_name = os.path.basename(
                        uploaded_file.name
                    )

                    try:

                        file_path = os.path.join(
                            "data/uploads",
                            f"{uuid.uuid4().hex}_{original_name}"
                        )

                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        ingest_rag_document(file_path)

                        successful_files.append(original_name)

                        st.write(
                            f"✅ {original_name} ingested successfully"
                        )

                    except Exception as e:

                        failed_files.append(original_name)

                        st.error(
                            f"Error processing {original_name}: {str(e)}"
                        )

                if failed_files:

                    status.update(
                        label="Document ingestion completed with errors",
                        state="error",
                        expanded=True
                    )

                else:

                    status.update(
                        label="All documents ingested successfully!",
                        state="complete",
                        expanded=False
                    )

        # =============================================
        # EXECUTION CHATBOT
        # =============================================

        if user_input.strip():

            with st.chat_message("assistant"):

                ai_message = stream_agent(
                    {
                        "messages": [
                            HumanMessage(content=user_input)
                        ]
                    },
                    config
                )

            # Vérifier si le workflow est interrompu
            updated_state = chatbot.get_state(config)

            if not updated_state.interrupts:

                if ai_message:

                    st.session_state["message_history"].append({
                        "role": "assistant",
                        "content": ai_message
                    })

            else:

                # L'interruption sera affichée au prochain rendu
                st.rerun()
