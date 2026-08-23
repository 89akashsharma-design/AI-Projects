Plan: Jira Test Case Generator — Streamlit App
TL;DR: Two-screen Streamlit app. Chat screen takes "create test cases for JIRA-102", fetches the ticket from Jira REST API, merges details into the existing templates/testcase_creator.md template, generates test cases via Groq , and renders the output in chat. Credentials flow: .env → config.json (runtime persistence).

Architecture
User: "create test cases for JIRA-102"
  → app.py parses JIRA-102 via regex
  → jira_client.py ──GET /rest/api/2/issue/JIRA-102──▶ Jira
  → templates/testcase_creator.md loaded
  → llm_client.py ── Groq API──────────────────▶ Cloud
  → Test cases rendered in chat
Phases
Phase	Steps	Dependency
1. Foundation	Create .env, update .gitignore, create requirements.txt	None — all parallel
2. Core Modules	config_store.py → jira_client.py → llm_client.py	Sequential (each builds on prior)
3. Screens	app.py (Chat), pages/settings.py (Settings)	Depends on Phase 2
4. Polish	Prompt refinement, startup validation	Depends on Phase 3
Files to Create/Modify
File	What
AI Projects/.env	Create — user's Jira/Groq credentials
AI Projects/app.py	Create — Chat screen: parse Jira key, orchestrate fetch→template→LLM→render
AI Projects/pages/settings.py	Create — Settings form + Test Connection buttons
AI Projects/config_store.py	Create — .env loader + config.json read/write
AI Projects/jira_client.py	Create — fetch_ticket(key) → {summary, description, acceptance_criteria}
AI Projects/llm_client.py	Create — generate(prompt) with Groq
AI Projects/requirements.txt	Create — streamlit, requests, python-dotenv
templates/testcase_creator.md	Reuse — already exists
.gitignore (root)	Update — add .env, config.json
Key Design Decisions
Persistence: .env seeds initial values, config.json is the runtime store updated by Settings UI (both git-ignored)
Groq model: llama-3.1-8b-instant (fast, cheap, good structured output)
Ticket key regex: \b[A-Z]+-\d+\b matches standard Jira keys
No database: JSON file is sufficient per the prompt's "no unnecessary abstraction" rule
Template path: Read relative to app.py's directory (templates/testcase_creator.md)
Verification
Per-module: Test config_store reads .env, jira_client fetches a real ticket, and llm_client responds via Groq
Full flow: streamlit run app.py → Settings → save credentials → Chat → "create test cases for VALID-KEY" → verify complete output
Edge cases: No Jira key in message, invalid key (404), Groq unavailable, and empty settings on startup
Excluded
No multi-user auth, no deployment, no streaming, no batch processing, no CSV/PDF export — single-user internal tool only.

 
