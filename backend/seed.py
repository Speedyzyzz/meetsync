import asyncio
from datetime import datetime, timezone, timedelta
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.services.meeting_service import MeetingService
from backend.app.core.logging import logger

SAMPLE_MEETING_1 = """00:00:00 Arun: Welcome everyone to our Product Launch Strategy sync. We need to decide whether we are ready for launch this week and resolve any outstanding blockers.
00:00:25 Sarah: Thanks Arun. Engineering has finished the core API migration and frontend components. I propose we move the launch to Friday so we have adequate buffer for sanity checks.
00:00:52 Ravi: I agree with moving to Friday. That gives me enough time to complete the comprehensive QA regression test suite by Thursday EOD.
00:01:15 Arun: Excellent. Decision finalized: launch is officially moved to Friday. Also, we will begin the rollout with a 10% canary traffic allocation before 100% rollout.
00:01:40 Elena: That makes sense. I will update the developer API documentation by October 12 so partners have current guides.
00:02:05 Sarah: I will prepare the public rollout announcement and customer email templates by Friday morning.
00:02:30 Arun: I will coordinate the deployment window and monitor cloud database read replicas.
00:02:55 Elena: One open question: Who owns direct customer communication if any edge cases occur during migration?
00:03:20 Ravi: Another question: Do we need additional cloud infrastructure or auto-scaling buffers for the expected traffic spike?"""

SAMPLE_MEETING_2 = """00:00:00 Vikram: Good morning team. Today's standup is focused on the search indexing and database performance bottlenecks.
00:00:30 Maya: We analyzed the slow queries. The transcript search is taking over 900ms when querying across 10,000 meetings.
00:01:00 Vikram: We decided to implement PostgreSQL GIN indexes with tsvectors for full-text search across transcripts and meeting titles.
00:01:35 Maya: Agreed. I will implement the GIN index migrations by tomorrow afternoon.
00:02:10 Kevin: I will update the search API endpoint to utilize rank scoring so relevant snippets are surfaced first.
00:02:45 Vikram: Let's also introduce Redis caching for frequent workspace queries. Who can take that?
00:03:15 Maya: I can pair with Kevin on Redis caching once the GIN index is verified.
00:03:40 Kevin: Open question: Should we evaluate pgvector for hybrid semantic search next quarter?"""

SAMPLE_MEETING_3 = """00:00:00 Sarah: Let's review enterprise feedback from our pilot cohort this month.
00:00:35 David: The feedback on real-time transcript citations has been overwhelmingly positive. Clients love clicking an action item and jumping directly to the exact audio timestamp.
00:01:15 Sarah: That's great to hear. However, two enterprise clients requested Single Sign-On (SAML/Okta) and audit log exports.
00:01:50 David: We decided to prioritize Jira export integration first in sprint 4, followed by SAML SSO in sprint 5.
00:02:25 Sarah: David, please finalize the Jira webhook payload specs by Monday.
00:03:00 David: Will do. Open question: What compliance certifications (SOC2 / ISO) are required before signing enterprise tier contracts?"""

async def seed_data():
    logger.info("Initializing database schema for seeding...")
    await init_db()

    async with AsyncSessionLocal() as session:
        service = MeetingService(session)
        ws_id = await service.ensure_default_workspace()

        logger.info("Seeding Meeting 1: Product Launch Strategy Sync...")
        m1 = await service.create_meeting(
            title="Product Launch Strategy Sync",
            description="Discussion on launch timelines, QA regression testing, and traffic canary deployment.",
            workspace_id=ws_id,
            source_type="transcript",
            transcript_text=SAMPLE_MEETING_1,
            attendee_names=["Arun", "Sarah", "Ravi", "Elena"],
        )

        logger.info("Seeding Meeting 2: Engineering Architecture Review...")
        m2 = await service.create_meeting(
            title="Engineering Architecture Review",
            description="Database performance optimization, GIN indexing, and query latency reductions.",
            workspace_id=ws_id,
            source_type="transcript",
            transcript_text=SAMPLE_MEETING_2,
            attendee_names=["Vikram", "Maya", "Kevin"],
        )

        logger.info("Seeding Meeting 3: Q4 Customer Feedback & Roadmap...")
        m3 = await service.create_meeting(
            title="Q4 Customer Feedback & Roadmap",
            description="Reviewing enterprise pilot feedback and prioritizing upcoming integration milestones.",
            workspace_id=ws_id,
            source_type="transcript",
            transcript_text=SAMPLE_MEETING_3,
            attendee_names=["Sarah", "David"],
        )

        logger.info("Database seeding completed successfully! Created 3 rich meetings with full extractions.")

if __name__ == "__main__":
    asyncio.run(seed_data())
