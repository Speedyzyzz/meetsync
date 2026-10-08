# MeetSync Database Schema Reference

The database models are written using **SQLAlchemy 2.0** with async engine support (`asyncpg` for PostgreSQL, `aiosqlite` for local dev/testing) and managed via **Alembic** migrations.

## Entity Relationship Overview

```text
users
  │
  ├── memberships ── workspaces
                        │
                        └── meetings
                              ├── attendees
                              ├── transcripts
                              │     └── transcript_segments
                              ├── decisions
                              ├── action_items
                              ├── open_questions
                              └── processing_jobs
```

---

## Tables

### 1. `workspaces`
Multi-tenant isolation boundaries.
- `id`: VARCHAR(36) PK (UUID)
- `name`: VARCHAR(255)
- `slug`: VARCHAR(255) UNIQUE
- `created_at`, `updated_at`: DATETIME

### 2. `users` & `memberships`
- `users`: `id`, `email` (unique), `name`, `hashed_password`
- `memberships`: `id`, `user_id` (FK), `workspace_id` (FK), `role` (`admin`, `member`, `viewer`)

### 3. `meetings`
Central meeting entity.
- `id`: VARCHAR(36) PK (UUID)
- `workspace_id`: VARCHAR(36) FK
- `title`: VARCHAR(255)
- `description`: TEXT
- `meeting_date`: DATETIME
- `duration_seconds`: INTEGER
- `source_type`: VARCHAR(50) (`transcript` | `audio`)
- `status`: VARCHAR(50) (State machine: `UPLOADED`, `TRANSCRIBING`, `TRANSCRIBED`, `EXTRACTING`, `EXTRACTED`, `INDEXING`, `COMPLETED`, `FAILED`)
- `processing_stage`: VARCHAR(100)
- `error_message`: TEXT
- `retry_count`: INTEGER
- `token_count`: INTEGER
- `cost_usd`: FLOAT
- `audio_url`: VARCHAR(500)
- `summary`: TEXT

### 4. `transcripts` & `transcript_segments`
- `transcripts`: `id`, `meeting_id` (FK unique), `content` (TEXT), `language` (VARCHAR)
- `transcript_segments`: `id`, `transcript_id` (FK), `meeting_id` (FK), `segment_index` (INT), `speaker` (VARCHAR), `start_time` (FLOAT sec), `end_time` (FLOAT sec), `text` (TEXT)

### 5. `decisions`
- `id`: VARCHAR(36) PK
- `meeting_id`: VARCHAR(36) FK
- `decision`: TEXT
- `context`: TEXT
- `source_segment_ids`: TEXT (JSON array of segment IDs)

### 6. `action_items`
- `id`: VARCHAR(36) PK
- `meeting_id`: VARCHAR(36) FK
- `task`: TEXT
- `owner_id`: VARCHAR(36) FK (nullable)
- `owner_name`: VARCHAR(255)
- `deadline`: DATETIME
- `priority`: VARCHAR(50) (`low`, `medium`, `high`)
- `status`: VARCHAR(50) (`pending`, `in_progress`, `completed`, `cancelled`)
- `source_segment_ids`: TEXT (JSON array)
- `completed_at`: DATETIME

### 7. `open_questions`
- `id`: VARCHAR(36) PK
- `meeting_id`: VARCHAR(36) FK
- `question`: TEXT
- `context`: TEXT
- `resolved`: BOOLEAN
- `resolved_at`: DATETIME
- `resolved_by`: VARCHAR(255)
- `source_segment_ids`: TEXT (JSON array)

### 8. `processing_jobs`
State machine audit table.
- `id`: VARCHAR(36) PK
- `meeting_id`: VARCHAR(36) FK
- `status`: VARCHAR(50)
- `current_step`: VARCHAR(255)
- `progress_percent`: INTEGER
- `error_message`: TEXT
- `retry_count`: INTEGER
- `started_at`, `completed_at`: DATETIME
