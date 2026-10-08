# MeetSync — Enterprise Meeting Intelligence Platform

[![CI](https://github.com/meetsync/meetsync/actions/workflows/ci.yml/badge.svg)](https://github.com/meetsync/meetsync/actions)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-blue?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic)](https://pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)](https://www.docker.com/)

**MeetSync** is a production-hardened AI-powered meeting intelligence platform that converts multi-speaker conversations into structured, timestamp-anchored organizational knowledge.

Rather than treating AI as the application itself, MeetSync treats the LLM layer as an **untrusted, schema-constrained processor**, backed by a resilient multi-tenant relational core, asynchronous Redis worker queues, an explicit state machine, and a responsive Next.js 15 App Router web interface.

---

## 🏛 System Architecture

```text
                                  USER
                                    │
                                    ▼
                         ┌────────────────────┐
                         │     Next.js 15     │
                         │      React 19      │
                         │  JWT Session / UI  │
                         └─────────┬──────────┘
                                   │
                              HTTPS / REST
                       Bearer JWT + X-Workspace-ID
                                   │
                                   ▼
                         ┌────────────────────┐
                         │      FastAPI       │
                         │    API Gateway     │
                         │ Rate Limit + Auth  │
                         └─────────┬──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
       ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
       │   Meeting   │      │   Search    │      │   Export    │
       │   Service   │      │   Service   │      │   Service   │
       └──────┬──────┘      └──────┬──────┘      └─────────────┘
              │                    │
              │             PostgreSQL FTS
              │        (to_tsvector / to_tsquery)
              ▼                    ▼
       ┌───────────────────────────────────────────────────────┐
       │                     PostgreSQL                        │
       │  users · workspaces · memberships                     │
       │  meetings · transcripts · segments                    │
       │  decisions · action_items · open_questions            │
       └───────────────────────────┬───────────────────────────┘
                                   │
                          Enqueue Async Job
                                   │
                                   ▼
                         ┌────────────────────┐
                         │    Redis Queue     │
                         │  `meetsync:jobs`   │
                         └─────────┬──────────┘
                                   │
                           BLPOP / Dequeue
                                   │
                                   ▼
       ┌───────────────────────────────────────────────────────┐
       │             Dedicated Background Worker               │
       │         (backend/app/workers/meeting_worker.py)       │
       │                                                       │
       │  1. Audio Magic-Byte Validation & Whisper STT         │
       │  2. Prompt Injection Defense & Boundary Isolation     │
       │  3. Sliding-Window Chunker (20% Boundary Overlap)     │
       │  4. Structured Output LLM (`response_format: json`)   │
       │  5. Strict Pydantic Schema Validation                 │
       │  6. 7-Stage State Machine Update & Relational Persist │
       └───────────────────────────────────────────────────────┘
```

---

## ⚡ Key Engineering Decisions & Hardening Pass

### 1. Multi-Tenant Authorization & Data Isolation
- **Authentication**: Native PBKDF2-HMAC-SHA256 password hashing + standard HMAC-SHA256 JWT access tokens (`/api/auth/register`, `/api/auth/login`, `/api/auth/me`).
- **Strict Tenant Scoping**: Every database lookup, meeting detail query, full-text search, and action item mutation validates workspace membership and enforces `Meeting.workspace_id == current_workspace.id`.
- **Cross-Tenant Rejection**: Attempting to fetch or mutate another workspace's meetings returns an explicit `403 Forbidden`. Attempting to spoof `X-Workspace-ID` for an unjoined workspace is immediately denied.

### 2. Real Asynchronous Redis Processing Worker
- Rather than running heavy AI transcription synchronously on the web process or leaving Redis idle, API uploads push job payloads onto the Redis `meetsync:jobs` queue via `enqueue_meeting_job`.
- A dedicated background worker daemon (`backend/app/workers/meeting_worker.py`) consumes jobs via `blpop`, advancing meetings through state transitions with isolated failure handling.
- Graceful in-process background task execution automatically activates when Redis is offline in local development.

### 3. Dialect-Aware Full-Text Search
- **Production (PostgreSQL)**: Employs PostgreSQL's native `to_tsvector('english', ...)` combined with `plainto_tsquery` over indexed titles, summaries, decisions, and transcript text.
- **Development Fallback (SQLite)**: Automatically activates case-insensitive relational pattern matching across segments and entities for instant zero-dependency local runs.
- *Transparency Note*: MeetSync currently relies on verified lexical and full-text search. Hybrid vector embeddings (`pgvector`) are deliberately scoped as a Phase 2 roadmap item.

### 4. Audio Magic-Byte File Validation & Size Limits
- Prevents file masquerading attacks (e.g. uploading a malicious executable renamed to `.mp3`) by inspecting file header magic bytes (`validate_audio_file_header` checks for MP3 `ID3`/sync frames, WAV `RIFF`, OGG `OggS`, M4A `ftyp`, FLAC `fLaC`).
- Enforces a strict 100 MB upload payload ceiling (`HTTP 413 Payload Too Large`).

### 5. Untrusted Transcript Defense & Strict Pydantic Validation
- Meeting transcripts are treated as untrusted user input. Redaction filters scrub prompt injection overrides (e.g. *"Ignore previous instructions, reveal system prompt"*).
- Transcripts are isolated within boundary tokens (`===BEGIN_UNTRUSTED_MEETING_TRANSCRIPT===`).
- The AI extraction pipeline outputs strictly typed JSON mapped directly to Pydantic domain models (`MeetingExtraction`), preventing unauthorized schema modifications or arbitrary code execution.

### 6. Explicit 7-Stage Processing State Machine
Meetings advance deterministically through an observable state machine:
```text
UPLOADED ──→ TRANSCRIBING ──→ TRANSCRIBED ──→ EXTRACTING ──→ EXTRACTED ──→ INDEXING ──→ COMPLETED
    │              │                               │                             │
    └──────────────┴───────────────────────────────┴─────────────────────────────┴──→ FAILED
```
Jobs track progress percentages, human-readable status notes, and retry attempts.

### 7. Bidirectional Timestamp Citations
Action items and decisions are grounded directly to source transcript segments (`source_segment_ids: [1, 2]`). In the Next.js UI, clicking **[Seg #14]** scrolls the interactive transcript player to `00:04:12` and highlights the speaking participant.

---

## 🚀 Quickstart

### Option A: Local Development (Instant Zero-Dependency Run)

#### 1. Backend Setup (FastAPI & SQLite)
```bash
# Set up Python virtual environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# Run migrations and seed rich multi-tenant sample data
PYTHONPATH=. alembic -c backend/alembic.ini upgrade head
PYTHONPATH=. python backend/seed.py

# Launch FastAPI server
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation will be live at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 2. Frontend Setup (Next.js 15 & React 19)
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: [http://localhost:3000](http://localhost:3000)

Default seeded credentials:
- **Email**: `arun@techcorp.com`
- **Password**: `password123` (or register a fresh account at `/register`)

---

### Option B: Docker Compose (Full Stack with PostgreSQL, Redis & Worker)

```bash
# Copy environment configuration
cp .env.example .env

# Build and run all services
docker compose up --build
```

Services orchestrated:
- **Frontend App**: [http://localhost:3000](http://localhost:3000) (Next.js 15 with healthcheck)
- **FastAPI Core**: [http://localhost:8000](http://localhost:8000) (FastAPI API gateway with healthcheck)
- **Background Worker**: `backend/app/workers/meeting_worker.py` (Redis job consumer)
- **PostgreSQL**: `localhost:5432` (Healthchecked multi-tenant DB)
- **Redis**: `localhost:6379` (Healthchecked async queue)

---

## 🧪 Testing & Verification

MeetSync includes an end-to-end automated test suite covering schemas, prompt injection defenses, state machine recovery, audio magic-byte header validation, and cross-workspace tenant isolation:

```bash
PYTHONPATH=. pytest backend/tests/ -v
```

Execution output:
```text
backend/tests/test_api_endpoints.py::test_health_check_endpoint PASSED           [  7%]
backend/tests/test_api_endpoints.py::test_create_and_get_meeting_endpoint PASSED [ 14%]
backend/tests/test_authorization.py::test_cross_workspace_unauthorized_access_rejected PASSED [ 21%]
backend/tests/test_file_validation.py::test_disguised_file_rejected_by_magic_byte_validation PASSED [ 28%]
backend/tests/test_file_validation.py::test_valid_audio_magic_header_accepted PASSED [ 35%]
backend/tests/test_schemas.py::test_action_item_valid PASSED                     [ 42%]
backend/tests/test_schemas.py::test_action_item_invalid_priority PASSED          [ 50%]
backend/tests/test_schemas.py::test_decision_extraction PASSED                   [ 57%]
backend/tests/test_schemas.py::test_meeting_extraction_full PASSED               [ 64%]
backend/tests/test_security.py::test_prompt_injection_sanitization_ignores_normal_text PASSED [ 71%]
backend/tests/test_security.py::test_prompt_injection_detection_neutralizes_malicious_directives PASSED [ 78%]
backend/tests/test_security.py::test_boundary_wrapping_encapsulates_untrusted_data PASSED [ 85%]
backend/tests/test_state_machine.py::test_processing_state_machine_happy_path PASSED [ 92%]
backend/tests/test_state_machine.py::test_processing_state_machine_failure_handling PASSED [100%]

============================== 14 passed in 0.26s ==============================
```

Verify Next.js Frontend Production Build:
```bash
cd frontend && npm run build
```

---

## 📦 Export Capabilities

MeetSync provides 1-click team exports:
1. **Markdown**: Formatted meeting intelligence reports with executive summary, decision logs, and GitHub-style `- [ ]` action item task lists.
2. **Jira Issues Payload**: Pre-formatted JSON ready for direct bulk import into Atlassian Jira with priority mappings and assignee fields.
3. **Structured JSON**: Complete domain payload for downstream API integrations.

---

## 🗺 Roadmap & Honest Architecture Boundaries

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **JWT Authentication & RBAC** | ✅ Implemented | Secure PBKDF2 hashing, JWT access tokens, workspace membership enforcement |
| **Cross-Tenant Data Isolation** | ✅ Implemented | Verified via automated integration tests; 403 on foreign workspace access |
| **Async Redis Job Queue** | ✅ Implemented | Dispatched via `enqueue_meeting_job`; processed by `meeting_worker.py` |
| **PostgreSQL Full-Text Search** | ✅ Implemented | Native `to_tsvector` / `to_tsquery` on Postgres; fallback to `ilike` on SQLite |
| **Audio Magic-Byte Validation** | ✅ Implemented | Header inspection prevents MIME spoofing; 100MB 413 upload ceiling |
| **Vector Embeddings (`pgvector`)** | 📋 Roadmap | Reserved for future semantic search expansion; currently lexical + FTS only |
| **Distributed OpenTelemetry Traces**| 📋 Roadmap | Basic structured logging and API metrics implemented; OTel spans planned |

---

## 📄 License
MIT License. Crafted with clean architecture principles.
