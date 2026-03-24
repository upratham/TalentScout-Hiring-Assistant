from multiprocessing.util import get_logger

import streamlit as st
from datetime import datetime

from streamlit import logger

from src.conversation import ConversationState
from src.candidate import Candidate
from src.logger import configure_logger
from src.core import Core

logging = configure_logger()


# ── Page config ───────────────────────────────────────────────────────────────

def set_page_config() -> None:
    st.set_page_config(
        page_title="TalentScout — Hiring Assistant",
        page_icon="🤝",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ── Session state bootstrap ───────────────────────────────────────────────────

def bootstrap_session() -> None:
    """
    Initialises all st.session_state keys on first load.
    Streamlit reruns the entire script on every interaction — session_state
    is the only thing that persists between reruns.
    """
    if "conv_state" not in st.session_state:
        logging.info("New session started. Initialising conversation state.")
        st.session_state.conv_state = ConversationState.initialise_conversation()

    if "display_messages" not in st.session_state:
        # Separate list for display — no system prompt shown to user
        st.session_state.display_messages = []

    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {}

    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = True

    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now().strftime("%H:%M:%S")


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Renders the candidate profile panel and session controls."""
    with st.sidebar:
        st.title("🤝 TalentScout")
        st.caption("AI Hiring Assistant")
        st.divider()

        # Candidate profile — updates in real time as info is collected
        st.subheader("Candidate Profile")
        info = st.session_state.candidate_info

        if not info:
            st.caption("Collecting information...")
        else:
            field_map = [
                ("👤 Name",       info.get("name")),
                ("📧 Email",      info.get("email")),
                ("📞 Phone",      info.get("phone")),
                ("🗓 Experience", info.get("years_experience")),
                ("💼 Role",       info.get("desired_position")),
                ("📍 Location",   info.get("location")),
                ("🛠 Tech Stack", ", ".join(info.get("tech_stack") or []) or None),
            ]
            for label, value in field_map:
                if value:
                    st.markdown(f"**{label}**")
                    st.markdown(f"{value}")
                    st.markdown("")

        st.divider()

        # Session info
        st.caption(f"Session started: {st.session_state.session_start}")
        turns = st.session_state.conv_state.turn_count
        st.caption(f"Turns completed: {turns}")

        st.divider()

        # Reset button
        if st.button("🔄 Start New Interview", use_container_width=True):
            logging.info("Session reset triggered by user.")
            for key in [
                "conv_state", "display_messages", "candidate_info",
                "greeted", "conversation_active", "session_start",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

        st.caption(
            "Candidate data is stored locally and handled "
            "in compliance with data privacy standards."
        )


# ── Auto-greeting ─────────────────────────────────────────────────────────────

def render_greeting() -> None:
    """Fires the bot's opening message on first load."""
    if not st.session_state.greeted:
        logging.debug("Generating greeting for new session.")
        with st.spinner("Starting your session..."):
            greeting = ConversationState.get_greeting(st.session_state.conv_state)

        st.session_state.display_messages.append(
            {"role": "assistant", "content": greeting}
        )
        st.session_state.greeted = True
        logging.info("Greeting rendered.")


# ── Chat history ──────────────────────────────────────────────────────────────

def render_chat_history() -> None:
    """Renders all past messages in the chat window."""
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


# ── Message handler ───────────────────────────────────────────────────────────

def handle_user_input() -> None:
    """
    Captures user input, routes it through the conversation handler,
    updates display, and triggers candidate info extraction.
    """
    user_input = st.chat_input("Type your response here...")

    if not user_input:
        return

    logging.debug("User input received. length=%d", len(user_input))

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.display_messages.append(
        {"role": "user", "content": user_input}
    )

    # Route through conversation handler
    reply, is_ended = Core.handle_message(st.session_state.conv_state, user_input)

    # Display bot reply
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.session_state.display_messages.append(
        {"role": "assistant", "content": reply}
    )

    # If conversation ended — extract, save, deactivate
    if is_ended:
        logging.info("Conversation ended. Extracting and saving candidate data.")
        _extract_and_save()
        st.session_state.conversation_active = False
        st.rerun()
        return

    # Refresh candidate info in sidebar after every few turns
    if st.session_state.conv_state.turn_count >= 2:
        _refresh_candidate_info()

    st.rerun()


def _refresh_candidate_info() -> None:
    """
    Runs extraction on the current history and updates sidebar data.
    Only called mid-conversation to keep the sidebar fresh.
    """
    info = Candidate.extract_candidate_info(st.session_state.conv_state.messages)
    extracted = info.to_dict()
    if any(extracted.values()):
        st.session_state.candidate_info = extracted
        logging.debug(
            "Sidebar refreshed. fields=%s", info.collected_fields()
        )


def _extract_and_save() -> None:
    """Extracts candidate info and saves to disk at end of conversation."""
    info = Candidate.extract_candidate_info(st.session_state.conv_state.messages)
    st.session_state.candidate_info = info.to_dict()
    saved = Candidate.save_candidate(info)
    if saved:
        logger.info("Candidate record saved. name=%s", info.name)
    else:
        logger.warning("Candidate record not saved — possibly empty.")


# ── Ended state ───────────────────────────────────────────────────────────────

def render_ended_state() -> None:
    """Shows a banner when the conversation has ended."""
    st.success(
        "This interview session has ended. "
        "Click **Start New Interview** in the sidebar to begin again."
    )


# ── Main entrypoint ───────────────────────────────────────────────────────────

def run() -> None:
    """
    Main entrypoint called by app.py.
    Orchestrates the full Streamlit page render.
    """
    set_page_config()
    bootstrap_session()
    render_sidebar()

    st.title("TalentScout Hiring Assistant")
    st.caption("Welcome! I'll guide you through the initial screening process.")

    render_greeting()
    render_chat_history()

    if st.session_state.conversation_active:
        handle_user_input()
    else:
        render_ended_state()