import asyncio
import json
import signal
import sys
from typing import Optional
import redis.asyncio as aioredis
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.core.logging import logger
from backend.app.services.meeting_service import MeetingService

QUEUE_KEY = "meetsync:jobs"

class MeetingWorker:
    def __init__(self):
        self.running = True

    def stop(self):
        logger.info("Worker received shutdown signal. Terminating gracefully...")
        self.running = False

    async def run(self):
        logger.info(f"MeetSync Background Worker initializing... Connecting to Redis at {settings.REDIS_URL}")
        await init_db()

        client: Optional[aioredis.Redis] = None
        try:
            client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            logger.info(f"Worker connected to Redis. Polling queue '{QUEUE_KEY}'...")
        except Exception as e:
            logger.error(f"Worker could not connect to Redis: {e}")
            return

        while self.running:
            try:
                # Block for 2 seconds waiting for incoming jobs
                item = await client.blpop(QUEUE_KEY, timeout=2)
                if not item:
                    continue

                _, payload_str = item
                data = json.loads(payload_str)
                meeting_id = data.get("meeting_id")
                raw_transcript = data.get("raw_transcript")
                audio_path = data.get("audio_path")

                logger.info(f"Worker picked up job for meeting {meeting_id}")

                async with AsyncSessionLocal() as session:
                    service = MeetingService(session)
                    await service.process_meeting(
                        meeting_id=meeting_id,
                        raw_transcript=raw_transcript,
                        audio_file_path=audio_path,
                    )
                logger.info(f"Worker completed processing for meeting {meeting_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker encountered processing exception: {e}", exc_info=True)
                await asyncio.sleep(1)

        if client:
            await client.aclose()
        logger.info("Worker stopped cleanly.")

def main():
    worker = MeetingWorker()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass  # Windows or non-main thread

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
