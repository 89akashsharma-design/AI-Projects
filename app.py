from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from config_store import load_settings, missing_settings
from jira_client import JiraClient, JiraClientError
from llm_client import GroqClientError, generate


PROJECT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = PROJECT_DIR / "templates" / "testcase_creator.md"
JIRA_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
COUNT_PATTERN = re.compile(r"\b(?:create|generate)\s+(\d+)\s+(?:test\s+cases?|cases?)\b", re.IGNORECASE)


def _request_details(message: str, default_count: int) -> tuple[str | None, int]:
    key_match = JIRA_KEY_PATTERN.search(message.upper())
    count_match = COUNT_PATTERN.search(message)
    count = int(count_match.group(1)) if count_match else default_count
    return (key_match.group(0) if key_match else None, min(max(count, 1), 100))


def _build_prompt(template: str, ticket: dict[str, str], count: int) -> str:
    requirements = (
        f"Jira ticket: {ticket['key']}\n\n"
        f"Summary:\n{ticket['summary']}\n\n"
        f"Description:\n{ticket['description']}\n\n"
        f"Acceptance criteria:\n{ticket['acceptance_criteria']}"
    )
    return template.replace("[NUMBER]", str(count)).replace("[PASTE REQUIREMENTS HERE]", requirements)


def _render_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


st.set_page_config(page_title="Jira Test Case Generator", page_icon="QA", layout="centered")
st.title("Jira Test Case Generator")
st.caption("Turn one Jira ticket into a focused test-case draft.")

if "messages" not in st.session_state:
    st.session_state.messages = []
_render_history()

settings = load_settings()
message = st.chat_input("Create test cases for QA-102")
if message:
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.markdown(message)

    with st.chat_message("assistant"):
        missing = missing_settings(settings)
        key, count = _request_details(message, settings["default_test_case_count"])
        if missing:
            response = "Complete these settings before generating: " + ", ".join(missing) + "."
            st.warning(response)
        elif not key:
            response = "Include a Jira ticket key, for example `create test cases for QA-102`."
            st.info(response)
        else:
            try:
                jira = JiraClient(settings["jira_url"], settings["jira_email"], settings["jira_api_token"])
                ticket = jira.fetch_ticket(key)
                template = TEMPLATE_PATH.read_text(encoding="utf-8")
                response = generate(
                    _build_prompt(template, ticket, count),
                    settings["groq_api_key"],
                    model=settings["groq_model"],
                )
                st.markdown(response)
            except (JiraClientError, GroqClientError, OSError) as exc:
                response = f"I could not generate the test cases: {exc}"
                st.error(response)
        st.session_state.messages.append({"role": "assistant", "content": response})