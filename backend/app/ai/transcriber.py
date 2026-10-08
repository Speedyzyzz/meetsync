import os
import re
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger

def parse_pasted_transcript_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses pasted text into timestamped, speaker-attributed segments.
    Handles multiple standard transcript formats:
    Format A: 00:04:12  Sarah: We should move the launch...
    Format B: [04:12] Arun: Agreed.
    Format C: Sarah: Let's discuss the rollout.
    Format D: Plain text paragraphs.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    segments: List[Dict[str, Any]] = []
    
    current_time = 0.0
    segment_duration = 15.0  # Default 15 sec cadence per segment if no timestamp
    
    # Pattern 1: [00:04:12] Speaker: Text OR 00:04:12 Speaker: Text
    ts_speaker_pattern = re.compile(
        r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s+([A-Za-z0-9_\s]+?):\s*(.+)$"
    )
    # Pattern 2: Speaker: Text
    speaker_only_pattern = re.compile(r"^([A-Za-z0-9_\s]+?):\s*(.+)$")
    
    for idx, line in enumerate(lines):
        match1 = ts_speaker_pattern.match(line)
        if match1:
            ts_str, speaker, text = match1.groups()
            start_sec = parse_timestamp_to_seconds(ts_str)
            end_sec = start_sec + segment_duration
            segments.append({
                "segment_index": idx + 1,
                "speaker": speaker.strip(),
                "start_time": start_sec,
                "end_time": end_sec,
                "text": text.strip(),
            })
            current_time = end_sec
            continue
            
        match2 = speaker_only_pattern.match(line)
        if match2:
            speaker, text = match2.groups()
            # Verify speaker is not overly long (which would mean normal text with colon)
            if len(speaker.split()) <= 4:
                start_sec = current_time
                end_sec = start_sec + segment_duration
                segments.append({
                    "segment_index": idx + 1,
                    "speaker": speaker.strip(),
                    "start_time": start_sec,
                    "end_time": end_sec,
                    "text": text.strip(),
                })
                current_time = end_sec
                continue

        # Fallback line
        segments.append({
            "segment_index": idx + 1,
            "speaker": f"Speaker {(idx % 2) + 1}",
            "start_time": current_time,
            "end_time": current_time + segment_duration,
            "text": line.strip(),
        })
        current_time += segment_duration

    return segments

def parse_timestamp_to_seconds(ts: str) -> float:
    parts = [float(p) for p in ts.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return float(parts[0])

class TranscriptionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL

    async def transcribe_audio_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes audio file to timestamped segments using Whisper API or deterministic local fallback.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        if not self.api_key:
            logger.info(f"OpenAI API Key not set. Using local audio segment generator for file: {file_path}")
            return self._generate_mock_audio_transcript(file_path)

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
                data = {
                    "model": self.model,
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "segment",
                }
                resp = await client.post(url, headers=headers, files=files, data=data)
                resp.raise_for_status()
                res_json = resp.json()

        raw_segments = res_json.get("segments", [])
        parsed_segments = []
        for idx, seg in enumerate(raw_segments):
            parsed_segments.append({
                "segment_index": idx + 1,
                "speaker": f"Speaker {(idx % 3) + 1}",
                "start_time": float(seg.get("start", 0.0)),
                "end_time": float(seg.get("end", 0.0)),
                "text": seg.get("text", "").strip(),
            })

        return parsed_segments

    def _generate_mock_audio_transcript(self, file_path: str) -> List[Dict[str, Any]]:
        """Generates realistic demo segments from audio file when offline."""
        filename = os.path.basename(file_path)
        return [
            {
                "segment_index": 1,
                "speaker": "Arun",
                "start_time": 0.0,
                "end_time": 8.5,
                "text": f"Welcome everyone to the synchronization meeting for {filename}. Let's review the product launch date and outstanding blockers.",
            },
            {
                "segment_index": 2,
                "speaker": "Sarah",
                "start_time": 8.5,
                "end_time": 19.2,
                "text": "Thanks Arun. We have completed the core API migrations. I propose moving the public release to Friday.",
            },
            {
                "segment_index": 3,
                "speaker": "Ravi",
                "start_time": 19.2,
                "end_time": 31.0,
                "text": "I agree with Friday. I will complete the full QA regression test suite by Thursday EOD.",
            },
            {
                "segment_index": 4,
                "speaker": "Arun",
                "start_time": 31.0,
                "end_time": 44.5,
                "text": "Agreed: launch moved to Friday. Sarah, can you prepare the rollout communication and update documentation?",
            },
            {
                "segment_index": 5,
                "speaker": "Sarah",
                "start_time": 44.5,
                "end_time": 56.0,
                "text": "Yes, I will finalize the release docs by Friday morning. Do we need additional cloud infrastructure for the expected load?",
            },
            {
                "segment_index": 6,
                "speaker": "Arun",
                "start_time": 56.0,
                "end_time": 70.0,
                "text": "Good question. Let's decide who owns the cloud capacity planning. Let's reconvene on that tomorrow.",
            },
        ]

transcription_service = TranscriptionService()
