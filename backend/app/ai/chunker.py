from typing import Any, Dict, List

def format_segment_timestamp(seconds: float) -> str:
    """Converts seconds float to MM:SS or HH:MM:SS format."""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def format_segments_for_llm(segments: List[Dict[str, Any]]) -> str:
    """
    Formats transcript segments with explicit segment IDs and timestamps
    e.g. [SEG_001 | 00:04:12] Sarah: We should move the launch to Friday.
    """
    formatted_lines = []
    for seg in segments:
        seg_id = seg.get("segment_index", 0)
        start_sec = seg.get("start_time", 0.0)
        speaker = seg.get("speaker", "Speaker")
        text = seg.get("text", "").strip()
        ts = format_segment_timestamp(start_sec)
        formatted_lines.append(f"[SEG_{seg_id:03d} | {ts}] {speaker}: {text}")
    return "\n".join(formatted_lines)

def chunk_segments(
    segments: List[Dict[str, Any]],
    chunk_size: int = 40,
    overlap_size: int = 8,
) -> List[List[Dict[str, Any]]]:
    """
    Splits segments into overlapping chunks to prevent context splitting at boundaries.
    Default: 40 segments per chunk with 8 segments (20%) overlap.
    """
    if not segments:
        return []
    
    if len(segments) <= chunk_size:
        return [segments]
        
    chunks = []
    start = 0
    while start < len(segments):
        end = min(start + chunk_size, len(segments))
        chunk = segments[start:end]
        chunks.append(chunk)
        if end == len(segments):
            break
        start += (chunk_size - overlap_size)
        
    return chunks
