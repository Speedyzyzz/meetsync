# MeetSync REST API Documentation

Base URL: `http://localhost:8000/api`

## Health Check
- `GET /api/health` — Service status, environment, version
- `GET /api/ready` — Database connection readiness

---

## Meetings

### 1. List Meetings
- **Endpoint**: `GET /api/meetings`
- **Query Params**:
  - `workspace_id`: (optional) filter by workspace
  - `status`: (optional) filter by meeting status
  - `limit`: (default 50)
  - `offset`: (default 0)
- **Response**: Array of `MeetingOut` objects

### 2. Create Meeting (Pasted Transcript)
- **Endpoint**: `POST /api/meetings`
- **Request Body**:
```json
{
  "title": "Sprint Planning",
  "description": "Bi-weekly sprint planning",
  "source_type": "transcript",
  "transcript_text": "00:00 Arun: Let's discuss goals...",
  "attendee_names": ["Arun", "Sarah"]
}
```
- **Response**: Full `MeetingDetailOut` with extractions

### 3. Upload Audio Meeting
- **Endpoint**: `POST /api/meetings/upload-audio`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `title`: string (required)
  - `description`: string (optional)
  - `file`: audio file (.mp3, .wav, .m4a, .ogg)
- **Response**: `MeetingDetailOut`

### 4. Get Meeting Detail
- **Endpoint**: `GET /api/meetings/{id}`
- **Response**: Detailed meeting with segments, decisions, actions, questions, attendees

### 5. Trigger / Retry Processing
- **Endpoint**: `POST /api/meetings/{id}/process`
- **Response**: `MeetingDetailOut`

### 6. Job Status
- **Endpoint**: `GET /api/meetings/{id}/status`
- **Response**: `ProcessingJobOut` (progress_percent, current_step, status)

### 7. Delete Meeting
- **Endpoint**: `DELETE /api/meetings/{id}`

---

## Action Items

### 1. List Action Items
- **Endpoint**: `GET /api/action-items`
- **Query Params**:
  - `meeting_id`: (optional)
  - `status`: (optional: `pending` | `completed`)

### 2. Update Action Item Status (Optimistic UI)
- **Endpoint**: `PATCH /api/action-items/{id}`
- **Request Body**:
```json
{
  "status": "completed",
  "priority": "high",
  "deadline": "2026-10-15T00:00:00Z"
}
```

---

## Search
- **Endpoint**: `GET /api/search?q={query}`
- **Response**:
```json
{
  "query": "launch",
  "total_matches": 3,
  "results": [
    {
      "meeting_id": "...",
      "meeting_title": "Product Launch Sync",
      "result_type": "transcript",
      "snippet": "We should move the launch to Friday.",
      "matched_segment_id": 2,
      "timestamp_seconds": 25.0,
      "speaker": "Sarah"
    }
  ]
}
```

---

## Exports
- **Endpoint**: `GET /api/meetings/{id}/export?format={markdown|json|jira}`
- **Formats**:
  - `markdown`: Human-readable summary with checklists
  - `json`: Machine-readable structured payload
  - `jira`: Atlassian Jira issue creation payload
