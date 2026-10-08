import json
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from backend.app.core.config import settings
from backend.app.core.logging import logger

QUEUE_KEY = "meetsync:jobs"
_redis_pool: Optional[aioredis.Redis] = None

async def get_redis_client() -> Optional[aioredis.Redis]:
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
            await _redis_pool.ping()
        except Exception as e:
            logger.warning(f"Redis not available at {settings.REDIS_URL}: {e}")
            _redis_pool = None
    return _redis_pool

async def enqueue_meeting_job(
    job_id: str,
    meeting_id: str,
    raw_transcript: Optional[str] = None,
    audio_path: Optional[str] = None,
) -> bool:
    """
    Pushes meeting processing task onto the Redis job queue for worker consumption.
    Returns True if successfully queued to Redis, False if Redis is unreachable.
    """
    client = await get_redis_client()
    if not client:
        return False

    job_payload = {
        "job_id": job_id,
        "meeting_id": meeting_id,
        "raw_transcript": raw_transcript,
        "audio_path": audio_path,
    }

    try:
        await client.rpush(QUEUE_KEY, json.dumps(job_payload))
        logger.info(f"Meeting job {job_id} for meeting {meeting_id} published to Redis queue '{QUEUE_KEY}'")
        return True
    except Exception as e:
        logger.error(f"Failed to publish job to Redis queue: {e}")
        return False
