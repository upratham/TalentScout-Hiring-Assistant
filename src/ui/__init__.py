
import streamlit as st
from datetime import datetime
from streamlit import logger
from src.conversation import ConversationState
from src.candidate import Candidate
from src.core import Core
from src.logger import logging
from src.constants import *
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
# ── Streamlit App ─────────────────────────────────────────────

def run():
    st.set_page_config(
        page_title="TalentScout — Hiring Assistant",
        page_icon="🤝",
        layout="wide"
    )

    # ── Session State Initialisation ──────────────────────────────
    # Streamlit reruns the entire script on every user action.
    # Everything we want to persist goes in st.session_state.

    if "messages" not in st.session_state:
        # Full conversation history sent to the LLM each turn
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    if "display_messages" not in st.session_state:
        # Separate list for display only (no system prompt shown to user)
        st.session_state.display_messages = []

    if "conversation_active" not in st.session_state:
        st.session_state.conversation_active = True

    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {}

    if "greeted" not in st.session_state:
        st.session_state.greeted = False

    # ── Sidebar ───────────────────────────────────────────────────

    with st.sidebar:
        st.title("TalentScout")
        st.caption("AI Hiring Assistant")
        st.divider()

        # Show collected candidate info in real time
        st.subheader("Candidate Profile")
        info = st.session_state.candidate_info
        if not info:
            st.caption("Collecting information...")
        else:
            fields = [
                ("Name", info.get("name")),
                ("Email", info.get("email")),
                ("Phone", info.get("phone")),
                ("Experience", info.get("years_experience")),
                ("Role", info.get("desired_position")),
                ("Location", info.get("location")),
                ("Tech Stack", ", ".join(info.get("tech_stack") or []) or None),
            ]
            for label, value in fields:
                if value:
                    st.metric(label=label, value=value)

        st.divider()

        # Reset button
        if st.button("Start New Interview", use_container_width=True):
            for key in ["messages", "display_messages", "conversation_active",
                        "candidate_info", "greeted"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        st.caption("All candidate data is stored locally and handled in compliance with data privacy standards.")

    # ── Main Chat Area ────────────────────────────────────────────

    st.title("TalentScout Hiring Assistant")
    st.caption("Welcome! I will guide you through the initial screening process.")

    # Auto-greeting on first load
    if not st.session_state.greeted:
        with st.spinner("Starting your session..."):
            # Trigger the bot to send the first message
            init_msg = {"role": "user", "content": "[START]"}
            st.session_state.messages.append(init_msg)
            
            greeting = Core.call_llm(st.session_state.messages)
            
            # Remove the trigger message from history (don\'t show [START])
            st.session_state.messages.pop()
            st.session_state.messages.append(
                {"role": "assistant", "content": greeting}
            )
            st.session_state.display_messages.append(
                {"role": "assistant", "content": greeting}
            )
            st.session_state.greeted = True

    # Render all past messages
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input — only show if conversation is active
    if st.session_state.conversation_active:
        user_input = st.chat_input("Type your response here...")
        
        if user_input:
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_input)
            st.session_state.display_messages.append(
                {"role": "user", "content": user_input}
            )
            
            # Check for exit intent
            if Core.is_exit_intent(user_input):
                # Extract and save before ending
                extraction_state = {
                    "messages": st.session_state.messages,
                    "candidate_info": st.session_state.candidate_info,
                }
                extracted = Candidate.extract_candidate_info(extraction_state)
                extracted["timestamp"] = datetime.now().isoformat()
                st.session_state.candidate_info = extracted
                Candidate.save_candidate_data(extracted)

                farewell = (
                    "Thank you for your time today! The TalentScout team will review "
                    "your profile and reach out within 3-5 business days. "
                    "We wish you all the best in your career journey! Goodbye!"
                )
                with st.chat_message("assistant"):
                    st.markdown(farewell)
                st.session_state.display_messages.append(
                    {"role": "assistant", "content": farewell}
                )
                st.session_state.conversation_active = False
                st.rerun()
            
            else:
                # Regular turn — add to history and call LLM
                st.session_state.messages.append(
                    {"role": "user", "content": user_input}
                )
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        reply = Core.call_llm(st.session_state.messages)
                    st.markdown(reply)
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
                st.session_state.display_messages.append(
                    {"role": "assistant", "content": reply}
                )
                
                # Extract candidate info after each turn to keep sidebar fresh
                if len(st.session_state.messages) > 6:  # wait until some data is in
                    extraction_state = {
                        "messages": st.session_state.messages,
                        "candidate_info": st.session_state.candidate_info,
                    }
                    extracted = Candidate.extract_candidate_info(extraction_state)
                    if extracted:
                        extracted["timestamp"] = datetime.now().isoformat()
                        st.session_state.candidate_info = extracted
                
                st.rerun()

    else:
        # Conversation ended
        st.info("This interview session has ended. Click \'Start New Interview\' in the sidebar to begin again.")