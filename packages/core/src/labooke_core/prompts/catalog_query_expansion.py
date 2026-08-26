"""Prompts for expanding a natural book request into catalog queries."""

SYSTEM_PROMPT = (
    "Turn a request for a type of book into 2-4 concise semantic catalog search queries. "
    "Cover the requested subject, goal, audience and level when present. Candidate book "
    "descriptions may use the request language or common original technical terms. Return "
    "one JSON object with exactly one key, 'queries', containing an array of strings. "
    "Return JSON only, without markdown or prose."
)

USER_PROMPT = "Book request: {request}"
