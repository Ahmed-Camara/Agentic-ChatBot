
from agentic_chatbot import chatbot, get_all_threads
from rag.vector_store import ingest_rag_document
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
import streamlit as st
import uuid
import os


def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])


st.title("Agentic Chatbot")


# Initialisation des variables de session
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = get_all_threads()

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()


# =====================================================
# GESTION DES CONVERSATIONS
# =====================================================

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={
            "configurable": {"thread_id": thread_id}
        }
    )
    return state.values.get("messages", [])


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
# AFFICHAGE DE L'HISTORIQUE
# =====================================================

for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =====================================================
# CHAT INPUT + MULTIPLE FILE UPLOAD
# =====================================================

chat_submission = st.chat_input(
    "Message or upload documents...",
    accept_file="multiple",
    file_type=["pdf", "docx", "txt", "csv"]
)


if chat_submission is not None:

    user_input = chat_submission.text or ""
    uploaded_files = chat_submission.files or []

    # Construction du message utilisateur
    display_content = ""

    if uploaded_files:
        display_content += "**Documents joints :**\n"
        for uploaded_file in uploaded_files:
            display_content += f"- 📎 {uploaded_file.name}\n"

    if user_input.strip():
        display_content += "\n" + user_input

    # Affichage du message utilisateur
    if display_content:
        st.session_state["message_history"].append({
            "role": "user",
            "content": display_content
        })

        with st.chat_message("user"):
            st.markdown(display_content)


    # =================================================
    # INGESTION DES DOCUMENTS DANS LE VECTOR STORE
    # =================================================

    if uploaded_files:

        os.makedirs("data/uploads", exist_ok=True)

        with st.status(
            "Processing uploaded documents...",
            expanded=True
        ) as status:

            successful_files = []
            failed_files = []

            for uploaded_file in uploaded_files:

                try:
                    # Nom sécurisé et unique pour éviter les conflits
                    original_name = os.path.basename(uploaded_file.name)

                    file_path = os.path.join(
                        "data/uploads",
                        f"{uuid.uuid4().hex}_{original_name}"
                    )

                    # Sauvegarde du document
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Ingestion dans le RAG
                    ingest_rag_document(file_path)

                    successful_files.append(original_name)

                    st.write(f"✅ {original_name} ingested successfully")

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


    # =================================================
    # EXECUTION DU CHATBOT LANGGRAPH
    # =================================================

    if user_input.strip():

        config = {
            "configurable": {
                "thread_id": st.session_state["thread_id"]
            },
            "run_name": "chat_trace"
        }

        with st.chat_message("assistant"):

            status_holder = {"box": None}

            def ai_only_stream():

                for message_chunk, metadata in chatbot.stream(
                    {
                        "messages": [
                            HumanMessage(content=user_input)
                        ]
                    },
                    config=config,
                    stream_mode="messages"
                ):

                    # 1. Suivre l'exécution des tools
                    if isinstance(message_chunk, ToolMessage):

                        tool_name = getattr(
                            message_chunk, "name", "tool"
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

                    # 2. Ignorer les messages intermédiaires
                    if isinstance(message_chunk, AIMessageChunk):

                        if message_chunk.tool_call_chunks:
                            continue

                        if message_chunk.tool_calls:
                            continue

                        # Afficher uniquement le contenu textuel
                        content = message_chunk.content

                        if content:
                            yield content

                # 3. Terminer le statut après l'exécution
                if status_holder["box"] is not None:
                    status_holder["box"].update(
                        label="Task completed",
                        state="complete",
                        expanded=False
                    )

            ai_message = st.write_stream(ai_only_stream())

        st.session_state['message_history'].append({
            "role": "assistant",
            "content": ai_message
        })
