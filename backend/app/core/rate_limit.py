import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status
from backend.app.core.config import settings

# In-memory sliding window rate limiter
_request_records: Dict[str, List[float]] = defaultdict(list)

def check_rate_limit(request: Request, max_requests: int = 60, window_seconds: int = 60) -> None:
    """
    Enforces sliding-window rate limiting per client IP.
    Raises 429 Too Many Requests if threshold is exceeded.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    cutoff = now - window_seconds

    # Filter out requests older than the window
    records = [ts for ts in _request_records[client_ip] if ts > cutoff]
    
    if len(records) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: Maximum {max_requests} requests per minute allowed.",
        )

    records.append(now)
    _request_records[client_ip] = records
