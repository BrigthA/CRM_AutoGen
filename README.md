# AI CRM Support --- AutoGen, RAG & Ticket Management

A customer-support CRM prototype built with **FastAPI**, **Streamlit**,
**AutoGen agents**, **FAISS + BM25 retrieval**, and **SQLite**. It
supports AI-assisted customer conversations, ticket creation and review,
document-based knowledge retrieval, and operational dashboards.

> **Deployment status:** Suitable for development and protected
> demonstrations. The current implementation does **not** provide
> production authentication, role-based access control, or tenant
> isolation. Do not expose customer data or administrative APIs publicly
> until these controls are implemented.

## Features

-   **AI Support Chat:** Conversational support, conversation history,
    and ticket creation from chat.
-   **Four-stage agent workflow:** Query → Knowledge → Resolution → Log.
-   **Knowledge retrieval:** Document ingestion and hybrid BM25/FAISS
    retrieval, with grounding checks intended to limit unsupported
    responses.
-   **Ticket Management:** Ticket search, status/category/urgency
    filters, ticket details, human review, escalation and feedback
    workflows.
-   **Dashboard and analytics:** Ticket counts, trends, categories,
    agent activity, knowledge gaps and feedback.
-   **Notifications:** Notification records and optional SMTP
    configuration.
-   **Light Teal Streamlit UI:** Collapsible sidebar, compact themed
    buttons, and unified Tickets/Human Review workspace.
-   **Persistence:** SQLite database, RAG index and agent audit records.

Some advanced capabilities (such as truly live agent streaming, complete
access control, and multi-tenant separation) are **not yet
implemented**.

## Architecture

``` text
                         Browser
                            |
                         HTTPS
                            |
                  Existing Traefik proxy
                     /             \
             / (Streamlit)       /api (FastAPI)
                    |                  |
            Streamlit frontend --------+
                    |          Internal API requests
                    v
                FastAPI backend
                    |
         Query → Knowledge → Resolution → Log
                    |
       +------------+------------------+
       |            |                  |
    SQLite      FAISS + BM25       Audit / SMTP
  CRM records   knowledge index    notifications
```

The browser accesses the frontend through `/` and the backend through
`/api`. Docker Compose also configures the Streamlit container to reach
FastAPI at `http://backend:8000`.

## Project structure

``` text
AI_CRM_Hostinger_Deploy/
├── frontend/
│   └── app.py                 # Streamlit dashboard and CRM interface
├── backend/
│   ├── main.py                # FastAPI routes
│   ├── agents.py              # AutoGen agent workflow
│   ├── rag.py                 # Document retrieval
│   ├── grounding.py           # Evidence-based answer checks
│   ├── guardrails.py          # Input checks
│   ├── notifications.py       # Email notification helpers
│   └── db.py                  # SQLAlchemy models and SQLite
├── Dockerfile                 # Backend and frontend build targets
├── compose.yaml               # Services, Traefik routes, volumes
├── requirements.txt
├── requirements-ai.txt
├── .env.example
└── README_DEPLOY.md
```

## Requirements

-   Python 3.11 for local development
-   Docker Engine and Docker Compose plugin for container deployment
-   OpenAI API key for LLM-backed agent operations
-   Sufficient memory for CPU embeddings and FAISS
-   For VPS: an existing Traefik proxy with HTTPS and a new DNS record

## Local development (Windows PowerShell)

Run commands from the project root.

``` powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-ai.txt
Copy-Item .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY` and any required SMTP settings.
Never commit `.env`.

**Terminal 1 --- API:**

``` powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 --- UI:**

``` powershell
$env:API_URL = "http://127.0.0.1:8000"
python -m streamlit run frontend/app.py --server.port 8501
```

Open `http://localhost:8501`. Test API health at
`http://127.0.0.1:8000/health`.

> The database defaults to `./data/crm.db`, relative to the directory
> from which the backend starts. Run from the project root to keep paths
> consistent. Initial model downloads may take time.

## AI agent workflow

  -----------------------------------------------------------------------
  Stage                               Responsibility
  ----------------------------------- -----------------------------------
  **QueryAgent**                      Interpret and classify the customer
                                      request

  **KnowledgeAgent**                  Retrieve relevant approved
                                      knowledge

  **ResolutionAgent**                 Produce a response informed by
                                      available evidence

  **LogAgent**                        Record the execution and associated
                                      ticket/audit information
  -----------------------------------------------------------------------

Input validation and grounding checks are included. Their presence does
not guarantee that every response is correct; test the full workflow
with representative support scenarios.

## Main API endpoints

  ---------------------------------------------------------------------------------------------
  Method                  Path                                          Purpose
  ----------------------- --------------------------------------------- -----------------------
  GET                     `/health`                                     Backend health

  POST                    `/tickets`                                    Create ticket

  GET                     `/tickets`                                    List/filter tickets

  GET                     `/tickets/{ticket_id}`                        Ticket details

  POST                    `/tickets/{ticket_id}/review`                 Human review action

  POST                    `/tickets/{ticket_id}/feedback`               Submit feedback

  POST                    `/conversations`                              Start conversation

  GET                     `/conversations`                              Conversation list

  POST                    `/conversations/{conversation_id}/messages`   Send chat message

  POST                    `/conversations/{conversation_id}/ticket`     Create ticket from
                                                                        conversation

  GET                     `/documents`                                  Knowledge documents

  POST                    `/documents/upload`                           Upload knowledge
                                                                        document

  POST                    `/documents/upload-batch`                     Upload multiple
                                                                        documents

  GET                     `/search?q=...`                               Knowledge search

  GET                     `/stats`                                      Dashboard statistics

  GET                     `/runs`                                       Agent execution records

  GET                     `/runs/export`                                Export agent run data

  GET                     `/knowledge-gaps`                             Knowledge gap data

  GET                     `/notifications`                              Notification records
  ---------------------------------------------------------------------------------------------

When deployed behind Traefik, the public API is prefixed with `/api`,
for example `/api/health`. The proxy strips that prefix before
forwarding to FastAPI.

## Docker deployment on Hostinger VPS

**Do not start another Traefik instance or bind ports 80/443:** this
application is designed to reuse your existing reverse proxy.

### 1. Prepare DNS and configuration

Create an **A record** for a new CRM subdomain pointing to the VPS. Use
the actual subdomain you control, not `crm.example.com`.

``` bash
cd /opt/ai-crm
cp .env.example .env
nano .env
chmod 600 .env
```

Set these values:

  -----------------------------------------------------------------------
  Variable                            Description
  ----------------------------------- -----------------------------------
  `CRM_DOMAIN`                        New CRM subdomain

  `TRAEFIK_NETWORK`                   Existing external Traefik Docker
                                      network

  `TRAEFIK_CERTRESOLVER`              Existing Traefik TLS resolver

  `OPENAI_API_KEY`                    LLM API key

  `OPENAI_MODEL`                      LLM model (example: `gpt-4o-mini`)

  `SMTP_HOST`, `SMTP_PORT`            Optional email server

  `SMTP_USER`, `SMTP_PASSWORD`        Optional SMTP credentials

  `SMTP_FROM`, `SMTP_TO_EMAIL`        Optional notification
                                      sender/recipient
  -----------------------------------------------------------------------

Check your existing Docker networks and Traefik configuration before
setting the network/resolver:

``` bash
docker network ls
docker ps --format 'table {{.Names}}\t{{.Image}}'
```

### 2. Build and start

``` bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend frontend
```

### 3. Verify

``` bash
curl -I https://YOUR_CRM_DOMAIN/
curl https://YOUR_CRM_DOMAIN/api/health
```

Expected API health response:

``` json
{"status":"ok"}
```

The frontend and backend are separate services, exposed through Traefik;
ports 8501 and 8000 are not published directly on the VPS.

### 4. Update

``` bash
docker compose up -d --build
```

Back up persistent data before rebuilding or changing schemas. **Do not
use `docker compose down -v`**, because it deletes the named data
volumes.

## Data persistence

Docker Compose defines:

-   `crm_data`: SQLite database, FAISS index and agent audit CSV.
-   `hf_cache`: Cached Hugging Face embedding models.

To migrate an existing Windows SQLite database, make a **consistent
SQLite backup**, stop the backend, and restore the backup into the
container's data volume with appropriate file permissions. Avoid copying
a live WAL database as a single file.

## UI navigation

  -----------------------------------------------------------------------
  Page                                Function
  ----------------------------------- -----------------------------------
  Dashboard                           KPIs, ticket trends and category
                                      breakdown

  AI Support Chat                     Chat and ticket creation

  Ticket Management                   All Tickets and Human Review in one
                                      workspace

  Analytics                           Operational reporting

  Notifications                       Notification history and status

  Settings                            General, Customer 360°, Agent
                                      Monitor, Knowledge Gaps, SLA
                                      Management, AI Quality & Feedback,
                                      Knowledge Base
  -----------------------------------------------------------------------

The UI uses a Light Teal theme. Actual sidebar hover behavior, button
rendering, and responsiveness should be checked in the installed
Streamlit version.

## Troubleshooting

**Frontend cannot reach backend:** Check `docker compose ps`, backend
health and the frontend's `API_URL=http://backend:8000` environment
variable.

**HTTPS or 404 errors:** Confirm `CRM_DOMAIN`, DNS A record,
`TRAEFIK_NETWORK`, and `TRAEFIK_CERTRESOLVER`. The existing Traefik
proxy must share the configured Docker network.

**Slow initial requests:** Embedding models may download on first use;
allow time and ensure the VPS has enough memory.

**Data disappeared:** Verify the named `crm_data` volume is still
attached and that no volume-removal command was used.

**SMTP notifications fail:** Check optional SMTP configuration and
delivery logs; Gmail generally requires an app password when using SMTP.

**UI styling differs:** Streamlit's rendered markup varies by version.
Test sidebar tooltips and tab buttons in a real browser rather than
relying only on Python syntax checks.

## Security and production checklist

Before public use, implement and verify:

-   User authentication, authorization and role-based permissions
-   Customer/tenant isolation and ownership checks on all ticket and
    document endpoints
-   Protection of both the UI and `/api` routes, including document
    upload/export endpoints
-   Secure secret management and rotation
-   Rate limiting, upload restrictions and audit retention
-   Backup/restore procedures and recovery testing
-   Background-job reliability and SMTP delivery verification
-   Dependency scanning, logging/monitoring and representative
    end-to-end tests

**Important:** A Streamlit login screen alone does not protect the
FastAPI routes. Secure the backend independently.

## Notes on code versions

This deployment bundle includes the **v38 Streamlit frontend** and an
available **v18 backend baseline**, with the first-chat-message
ticket-summary correction. If your local backend contains newer fixes,
replace the included backend files with your latest working copies
before building.

## Documentation

For VPS-specific instructions, see
[`README_DEPLOY.md`](README_DEPLOY.md).

------------------------------------------------------------------------

**Stack:** Python · FastAPI · Streamlit · AutoGen · FAISS · BM25 ·
SQLAlchemy · SQLite · Plotly · Docker Compose · Traefik
