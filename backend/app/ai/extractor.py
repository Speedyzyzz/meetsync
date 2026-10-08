import json
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import sanitize_untrusted_transcript, wrap_untrusted_content
from backend.app.schemas.extraction import (
    ActionItemExtraction,
    DecisionExtraction,
    MeetingExtraction,
    OpenQuestionExtraction,
)
from backend.app.ai.prompts import CHUNK_SYNTHESIS_PROMPT, EXTRACTION_SYSTEM_PROMPT
from backend.app.ai.chunker import chunk_segments, format_segments_for_llm

INPUT_COST_PER_1M_TOKENS = 0.150   # gpt-4o-mini
OUTPUT_COST_PER_1M_TOKENS = 0.600  # gpt-4o-mini

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000 * INPUT_COST_PER_1M_TOKENS) + (
        output_tokens / 1_000_000 * OUTPUT_COST_PER_1M_TOKENS
    )

class ExtractionEngine:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL

    async def extract_meeting(
        self,
        segments: List[Dict[str, Any]],
        meeting_title: str = "Meeting",
    ) -> Tuple[MeetingExtraction, int, float]:
        """
        Executes structured extraction on meeting segments.
        Returns: (MeetingExtraction domain object, token_count, cost_usd)
        """
        if not segments:
            empty_extraction = MeetingExtraction(
                summary="No transcript segments recorded for this meeting.",
                decisions=[],
                action_items=[],
                open_questions=[],
                detected_attendees=[],
                estimated_duration_seconds=0,
            )
            return empty_extraction, 0, 0.0

        chunks = chunk_segments(segments, chunk_size=40, overlap_size=8)
        
        # If OpenAI API Key is not set, use the high-fidelity offline extractor
        if not self.api_key:
            logger.info("OPENAI_API_KEY not configured. Running offline deterministic intelligence extractor.")
            extraction = self._offline_extract(segments, meeting_title)
            # Estimate tokens: 1 word ~ 1.3 tokens
            total_words = sum(len(seg.get("text", "").split()) for seg in segments)
            est_tokens = int(total_words * 1.3) + 400
            cost = calculate_cost(est_tokens, 300)
            return extraction, est_tokens, cost

        # Multi-chunk or single-chunk online LLM execution
        chunk_extractions: List[MeetingExtraction] = []
        total_tokens = 0
        total_cost = 0.0

        for idx, chunk in enumerate(chunks):
            formatted_text = format_segments_for_llm(chunk)
            sanitized_text, injection_detected = sanitize_untrusted_transcript(formatted_text)
            if injection_detected:
                logger.warning(f"Indirect prompt injection patterns detected and neutralized in chunk {idx+1}")
            
            payload = wrap_untrusted_content(sanitized_text)
            chunk_result, tokens, cost = await self._call_llm_json(
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_prompt=f"Meeting Title: {meeting_title}\n\nTranscript Content:\n{payload}",
            )
            total_tokens += tokens
            total_cost += cost
            chunk_extractions.append(chunk_result)

        if len(chunk_extractions) == 1:
            return chunk_extractions[0], total_tokens, total_cost

        # Hierarchical synthesis for multi-chunk meetings
        synthesized, syn_tokens, syn_cost = await self._synthesize_chunks(
            chunk_extractions, meeting_title
        )
        total_tokens += syn_tokens
        total_cost += syn_cost
        return synthesized, total_tokens, total_cost

    async def _call_llm_json(
        self, system_prompt: str, user_prompt: str
    ) -> Tuple[MeetingExtraction, int, float]:
        """Calls OpenAI Chat Completion with JSON mode and retries."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            result = resp.json()

        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        cost = calculate_cost(prompt_tokens, completion_tokens)

        content = result["choices"][0]["message"]["content"]
        raw_json = json.loads(content)
        validated = MeetingExtraction.model_validate(raw_json)
        return validated, total_tokens, cost

    async def _synthesize_chunks(
        self, extractions: List[MeetingExtraction], meeting_title: str
    ) -> Tuple[MeetingExtraction, int, float]:
        """Synthesizes multiple chunk extractions into one consolidated result."""
        merged_data = {
            "meeting_title": meeting_title,
            "chunks": [e.model_dump() for e in extractions],
        }
        user_prompt = f"Consolidate these meeting chunks:\n{json.dumps(merged_data, indent=2)}"
        return await self._call_llm_json(
            system_prompt=CHUNK_SYNTHESIS_PROMPT, user_prompt=user_prompt
        )

    def _offline_extract(
        self, segments: List[Dict[str, Any]], meeting_title: str
    ) -> MeetingExtraction:
        """
        Deterministic, offline extraction engine with semantic regex heuristics.
        Used for local development, zero-credit demos, and continuous testing.
        """
        all_speakers = set()
        decisions: List[DecisionExtraction] = []
        action_items: List[ActionItemExtraction] = []
        open_questions: List[OpenQuestionExtraction] = []

        decision_triggers = [
            r"agree(d)?\s+(to|on|that)?",
            r"decid(e|ed)\s+(to|on|that)?",
            r"let's\s+move\s+the\s+",
            r"we\s+will\s+go\s+with",
            r"approved\s+",
            r"finalized\s+",
            r"conclusion\s+is",
        ]
        action_triggers = [
            r"(will|to)\s+(complete|prepare|update|deploy|implement|test|fix|write|send|check|create|build|finish|finalize|run|execute|review)",
            r"assigned\s+to",
            r"action\s+item",
            r"take\s+ownership\s+of",
            r"responsible\s+for",
        ]
        question_triggers = [
            r"who\s+(owns|will|can|is)",
            r"do\s+we\s+need",
            r"what\s+is\s+the\s+",
            r"how\s+should\s+we",
            r"when\s+will",
            r"\?$",
        ]

        for seg in segments:
            idx = seg.get("segment_index", 0)
            speaker = seg.get("speaker", "Speaker")
            text = seg.get("text", "").strip()
            if speaker:
                all_speakers.add(speaker)

            # Check decisions
            for d_pat in decision_triggers:
                if re.search(d_pat, text, re.IGNORECASE):
                    decisions.append(
                        DecisionExtraction(
                            decision=text,
                            context=f"Agreed by {speaker} during discussion",
                            source_segment_ids=[idx],
                        )
                    )
                    break

            # Check action items
            for a_pat in action_triggers:
                if re.search(a_pat, text, re.IGNORECASE):
                    # Check if assignee mentioned
                    owner = speaker
                    task_text = text
                    deadline = None
                    if "by friday" in text.lower():
                        deadline = "Friday EOD"
                    elif "by tomorrow" in text.lower():
                        deadline = "Tomorrow"
                    elif "next week" in text.lower():
                        deadline = "Next Week"

                    action_items.append(
                        ActionItemExtraction(
                            task=task_text,
                            owner=owner,
                            deadline=deadline,
                            priority="high" if "qa" in text.lower() or "deploy" in text.lower() or "urgent" in text.lower() else "medium",
                            source_segment_ids=[idx],
                        )
                    )
                    break

            # Check open questions
            for q_pat in question_triggers:
                if re.search(q_pat, text, re.IGNORECASE) or text.endswith("?"):
                    open_questions.append(
                        OpenQuestionExtraction(
                            question=text,
                            context=f"Raised by {speaker}",
                            source_segment_ids=[idx],
                        )
                    )
                    break

        # Deduplicate decisions & actions
        unique_decisions = []
        seen_d = set()
        for d in decisions:
            if d.decision.lower() not in seen_d:
                seen_d.add(d.decision.lower())
                unique_decisions.append(d)

        unique_actions = []
        seen_a = set()
        for a in action_items:
            if a.task.lower() not in seen_a:
                seen_a.add(a.task.lower())
                unique_actions.append(a)

        unique_questions = []
        seen_q = set()
        for q in open_questions:
            if q.question.lower() not in seen_q:
                seen_q.add(q.question.lower())
                unique_questions.append(q)

        # Executive Summary synthesis
        summary_lines = [
            f"The team convened for '{meeting_title}' with {len(all_speakers)} participant(s): {', '.join(sorted(all_speakers)) if all_speakers else 'Team members'}.",
        ]
        if unique_decisions:
            summary_lines.append(f"Key agreements were reached including: {unique_decisions[0].decision}")
        if unique_actions:
            summary_lines.append(f"{len(unique_actions)} concrete action item(s) were assigned to drive forward the agenda.")
        if unique_questions:
            summary_lines.append(f"{len(unique_questions)} open question(s) remain under active review.")
        
        summary = " ".join(summary_lines)
        if len(segments) > 0:
            last_seg = segments[-1]
            est_duration = int(last_seg.get("end_time", 0.0))
        else:
            est_duration = 0

        return MeetingExtraction(
            summary=summary,
            decisions=unique_decisions[:10],
            action_items=unique_actions[:15],
            open_questions=unique_questions[:10],
            detected_attendees=sorted(list(all_speakers)),
            estimated_duration_seconds=est_duration if est_duration > 0 else 1800,
        )

extractor = ExtractionEngine()
