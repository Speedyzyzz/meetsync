import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_disguised_file_rejected_by_magic_byte_validation(client: AsyncClient):
    # Register and get token
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": "auditor@security.com",
            "name": "Security Auditor",
            "password": "Password123!",
            "workspace_name": "Security Lab",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload malicious fake mp3 containing plain text
    fake_mp3_content = b"This is a disguised shell script or plain text, not a real audio file."
    files = {"file": ("malicious.mp3", fake_mp3_content, "audio/mpeg")}
    data = {"title": "Malicious Upload Test"}

    res = await client.post("/api/meetings/upload-audio", data=data, files=files, headers=headers)
    assert res.status_code == 400
    assert "header signature" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_valid_audio_magic_header_accepted(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": "valid_user@security.com",
            "name": "Valid User",
            "password": "Password123!",
            "workspace_name": "Valid Lab",
        },
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Valid ID3 MP3 header bytes
    valid_id3_mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 256
    files = {"file": ("recording.mp3", valid_id3_mp3, "audio/mpeg")}
    data = {"title": "Valid Audio Recording"}

    res = await client.post("/api/meetings/upload-audio", data=data, files=files, headers=headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Valid Audio Recording"
    assert res.json()["source_type"] == "audio"
