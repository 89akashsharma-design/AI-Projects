from __future__ import annotations

import streamlit as st

from config_store import load_settings, missing_settings, save_settings
from jira_client import JiraClient, JiraClientError
from llm_client import GroqClientError, test_connection as test_groq_connection


st.set_page_config(page_title="Settings | Jira Test Case Generator", page_icon="Settings", layout="centered")
st.title("Settings")
st.caption("Credentials are stored locally in config.json and are never shown in plain text.")

settings = load_settings()
with st.form("settings"):
    jira_url = st.text_input("Jira base URL", value=settings["jira_url"], placeholder="https://your-company.atlassian.net")
    jira_email = st.text_input("Jira email", value=settings["jira_email"])
    jira_api_token = st.text_input("Jira API token", value=settings["jira_api_token"], type="password")
    groq_api_key = st.text_input("Groq API key", value=settings["groq_api_key"], type="password")
    default_count = st.number_input(
        "Default test-case count", min_value=1, max_value=100, value=int(settings["default_test_case_count"]), step=1
    )
    saved = st.form_submit_button("Save settings", type="primary", use_container_width=True)

if saved:
    save_settings(
        {
            "jira_url": jira_url,
            "jira_email": jira_email,
            "jira_api_token": jira_api_token,
            "groq_api_key": groq_api_key,
            "default_test_case_count": default_count,
            "groq_model": settings["groq_model"],
        }
    )
    st.success("Settings saved locally.")
    settings = load_settings()

st.divider()
st.subheader("Connection tests")
test_jira, test_groq = st.columns(2)
with test_jira:
    if st.button("Test Jira", use_container_width=True):
        missing = [name for name in missing_settings(settings) if name != "Groq API key"]
        if missing:
            st.error("Complete Jira settings: " + ", ".join(missing) + ".")
        else:
            try:
                JiraClient(settings["jira_url"], settings["jira_email"], settings["jira_api_token"]).test_connection()
                st.success("Jira connection succeeded.")
            except JiraClientError as exc:
                st.error(str(exc))
with test_groq:
    if st.button("Test Groq", use_container_width=True):
        if not settings["groq_api_key"]:
            st.error("Add a Groq API key first.")
        else:
            try:
                test_groq_connection(settings["groq_api_key"], model=settings["groq_model"])
                st.success("Groq connection succeeded.")
            except GroqClientError as exc:
                st.error(str(exc))