import hashlib
import re
from typing import Tuple

# Suspicious phrases often used in indirect prompt injection attacks
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"disregard\s+(above|previous|system)", re.IGNORECASE),
    re.compile(r"override\s+system\s+directive", re.IGNORECASE),
]

# Strict boundary tokens that isolate untrusted meeting content
TRANSCRIPT_START_TAG = "===BEGIN_UNTRUSTED_MEETING_TRANSCRIPT==="
TRANSCRIPT_END_TAG = "===END_UNTRUSTED_MEETING_TRANSCRIPT==="

def sanitize_untrusted_transcript(text: str) -> Tuple[str, bool]:
    """
    Sanitizes raw transcript text to prevent indirect prompt injection.
    Flags if suspicious patterns were detected.
    Replaces blatant attack directives with neutralized text.
    """
    if not text:
        return "", False
        
    has_injection_attempt = False
    cleaned_text = text
    
    # Strip null bytes and non-printable control characters (keep newlines, tabs)
    cleaned_text = "".join(ch for ch in cleaned_text if ch == "\n" or ch == "\r" or ch == "\t" or (32 <= ord(ch) <= 126) or ord(ch) > 127)
    
    # Detect injection attempts
    for pattern in INJECTION_PATTERNS:
        if pattern.search(cleaned_text):
            has_injection_attempt = True
            cleaned_text = pattern.sub("[REDACTED_SUSPICIOUS_DIRECTIVE]", cleaned_text)
            
    return cleaned_text, has_injection_attempt

def wrap_untrusted_content(text: str) -> str:
    """
    Wraps sanitized text into strict sandboxing delimiters.
    """
    return f"{TRANSCRIPT_START_TAG}\n{text}\n{TRANSCRIPT_END_TAG}"

def hash_password(password: str) -> str:
    """Simple salted hash for internal user credentials."""
    salt = "meetsync_salt_secure_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
