"""Load and persist local application settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "config.json"
DEFAULT_SETTINGS: dict[str, Any] = {
    "jira_url": "",
    "jira_email": "",
    "jira_api_token": "",
    "groq_api_key": "",
    "default_test_case_count": 10,
    "groq_model": "llama-3.1-8b-instant",
}


def _load_seed_environment() -> None:
    """Load root and legacy src environment files without overriding real env vars."""
    for environment_file in (PROJECT_DIR / ".env", PROJECT_DIR / "src" / ".env"):
        if environment_file.exists():
            load_dotenv(environment_file, override=False)


def _environment_settings() -> dict[str, Any]:
    return {
        "jira_url": os.getenv("JIRA_URL", "").strip(),
        "jira_email": os.getenv("JIRA_EMAIL", "").strip(),
        "jira_api_token": os.getenv("JIRA_API_TOKEN", "").strip(),
        "groq_api_key": (
            os.getenv("GROQ_API_KEY", "").strip()
            or os.getenv("GROQ_API_TOKEN", "").strip()
        ),
    }


def load_settings() -> dict[str, Any]:
    """Return persisted settings, seeded from environment values when absent."""
    _load_seed_environment()
    settings = DEFAULT_SETTINGS.copy()
    settings.update(_environment_settings())

    if CONFIG_PATH.exists():
        try:
            persisted = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            persisted = {}
        if isinstance(persisted, dict):
            settings.update({key: value for key, value in persisted.items() if key in settings})

    try:
        settings["default_test_case_count"] = max(1, int(settings["default_test_case_count"]))
    except (TypeError, ValueError):
        settings["default_test_case_count"] = DEFAULT_SETTINGS["default_test_case_count"]
    return settings


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Persist only known settings and return the normalized result."""
    normalized = DEFAULT_SETTINGS.copy()
    normalized.update({key: value for key, value in settings.items() if key in normalized})
    normalized["default_test_case_count"] = max(1, int(normalized["default_test_case_count"]))
    CONFIG_PATH.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return normalized


def missing_settings(settings: dict[str, Any]) -> list[str]:
    required = {
        "jira_url": "Jira URL",
        "jira_email": "Jira email",
        "jira_api_token": "Jira API token",
        "groq_api_key": "Groq API key",
    }
    return [label for key, label in required.items() if not str(settings.get(key, "")).strip()]