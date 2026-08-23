"""Small Jira Cloud REST client used by the Streamlit app."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import requests


class JiraClientError(RuntimeError):
    """An actionable Jira request or response error."""


def _plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(part for part in (_plain_text(item) for item in value) if part).strip()
    if isinstance(value, dict):
        if "text" in value:
            return _plain_text(value["text"])
        return " ".join(part for part in (_plain_text(item) for item in value.values()) if part).strip()
    return str(value).strip()


def _find_acceptance_criteria(fields: dict[str, Any]) -> str:
    labels = ("acceptance criteria", "acceptance criterion", "acceptance_criteria")
    for name, value in fields.items():
        normalized_name = re.sub(r"[_-]+", " ", str(name).lower())
        if any(label in normalized_name for label in labels):
            text = _plain_text(value)
            if text:
                return text
    return "Not specified"


def _base_url(url: str) -> str:
    return url.rstrip("/") + "/"


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str, timeout: int = 20) -> None:
        self.base_url = _base_url(base_url.strip())
        self.auth = (email.strip(), api_token.strip())
        self.timeout = timeout

    def _get(self, path: str, **kwargs: Any) -> requests.Response:
        try:
            response = requests.get(
                urljoin(self.base_url, path.lstrip("/")),
                auth=self.auth,
                headers={"Accept": "application/json"},
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise JiraClientError(f"Could not reach Jira: {exc}") from exc
        if response.status_code in (401, 403):
            raise JiraClientError("Jira rejected the credentials. Check the email and API token.")
        if response.status_code == 404:
            raise JiraClientError("The Jira issue was not found. Check the ticket key and Jira URL.")
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise JiraClientError(f"Jira returned HTTP {response.status_code}.") from exc
        return response

    def fetch_ticket(self, key: str) -> dict[str, str]:
        response = self._get(f"/rest/api/3/issue/{key}", params={"fields": "summary,description,*all"})
        data = response.json()
        fields = data.get("fields", {})
        return {
            "key": key,
            "summary": _plain_text(fields.get("summary")) or "Not specified",
            "description": _plain_text(fields.get("description")) or "Not specified",
            "acceptance_criteria": _find_acceptance_criteria(fields),
        }

    def test_connection(self) -> None:
        self._get("/rest/api/3/myself", params={"fields": "displayName"})