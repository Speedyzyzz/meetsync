import pytest

@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_create_and_get_meeting_endpoint(client):
    payload = {
        "title": "Architecture Review",
        "description": "Database query optimization review",
        "source_type": "transcript",
        "transcript_text": "00:00:10 Alice: We will deploy Redis for caching.\n00:00:30 Bob: I will benchmark latency by tomorrow.",
        "attendee_names": ["Alice", "Bob"],
    }
    create_res = await client.post("/api/meetings", json=payload)
    assert create_res.status_code == 200
    meeting_data = create_res.json()
    assert meeting_data["title"] == "Architecture Review"
    assert meeting_data["status"] == "COMPLETED"
    meeting_id = meeting_data["id"]

    # Fetch meeting detail
    get_res = await client.get(f"/api/meetings/{meeting_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert len(detail["segments"]) == 2
    assert len(detail["action_items"]) >= 1

    # Search for Bob
    search_res = await client.get("/api/search?q=Redis")
    assert search_res.status_code == 200
    assert search_res.json()["total_matches"] >= 1

    # Export markdown
    export_res = await client.get(f"/api/meetings/{meeting_id}/export?format=markdown")
    assert export_res.status_code == 200
    assert "# Architecture Review" in export_res.json()["content"]
