import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_cross_workspace_unauthorized_access_rejected(client: AsyncClient):
    # 1. Register User A in Workspace A
    res_a = await client.post(
        "/api/auth/register",
        json={
            "email": "alice@company-a.com",
            "name": "Alice Corp A",
            "password": "Password123!",
            "workspace_name": "Workspace Alpha",
        },
    )
    assert res_a.status_code == 200
    data_a = res_a.json()
    token_a = data_a["access_token"]
    ws_a_id = data_a["workspace"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Workspace-ID": ws_a_id}

    # 2. Register User B in Workspace B
    res_b = await client.post(
        "/api/auth/register",
        json={
            "email": "bob@company-b.com",
            "name": "Bob Corp B",
            "password": "Password123!",
            "workspace_name": "Workspace Beta",
        },
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    token_b = data_b["access_token"]
    ws_b_id = data_b["workspace"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Workspace-ID": ws_b_id}

    # 3. User A creates a secret meeting in Workspace A
    meeting_payload = {
        "title": "Confidential Alpha Product Roadmap",
        "description": "Top secret merger plans",
        "source_type": "transcript",
        "transcript_text": "00:00 Alice: Project Pegasus is approved. Arun will lead QA.",
        "attendee_names": ["Alice"],
    }
    create_res = await client.post("/api/meetings", json=meeting_payload, headers=headers_a)
    assert create_res.status_code == 200
    meeting_a = create_res.json()
    meeting_a_id = meeting_a["id"]

    # 4. User B attempts GET /api/meetings/{meeting_a_id} in Workspace B -> MUST BE 403 FORBIDDEN!
    get_res_b = await client.get(f"/api/meetings/{meeting_a_id}", headers=headers_b)
    assert get_res_b.status_code == 403, "User B must not be permitted to read Meeting A!"
    assert "Forbidden" in get_res_b.json()["detail"]

    # 5. User B attempts to spoof X-Workspace-ID to Workspace A -> MUST BE 403 FORBIDDEN (not a member)!
    spoofed_headers = {"Authorization": f"Bearer {token_b}", "X-Workspace-ID": ws_a_id}
    spoof_res = await client.get(f"/api/meetings/{meeting_a_id}", headers=spoofed_headers)
    assert spoof_res.status_code == 403, "User B must not be permitted to access Workspace A!"

    # 6. User B searches for 'Pegasus' in Workspace B -> MUST RETURN ZERO RESULTS!
    search_res_b = await client.get("/api/search?q=Pegasus", headers=headers_b)
    assert search_res_b.status_code == 200
    assert search_res_b.json()["total_matches"] == 0, "Search results must not leak cross-tenant meetings!"

    # 7. User B lists action items -> MUST NOT SEE ALICE'S ACTION ITEMS!
    actions_res_b = await client.get("/api/action-items", headers=headers_b)
    assert actions_res_b.status_code == 200
    assert len(actions_res_b.json()) == 0, "Action items board must not leak cross-tenant tasks!"

    # 8. User B attempts DELETE on Meeting A -> MUST BE 403 FORBIDDEN!
    del_res_b = await client.delete(f"/api/meetings/{meeting_a_id}", headers=headers_b)
    assert del_res_b.status_code == 403, "User B must not be permitted to delete Meeting A!"
