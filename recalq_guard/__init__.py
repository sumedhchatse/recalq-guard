"""
recalq-guard — Negation & polarity awareness for semantic caches.

Plain semantic caching returns WRONG answers when queries flip meaning:
  "how to ENABLE ssh" vs "how to DISABLE ssh"  -> 95% similar, opposite answer.

recalq-guard adds a rejection layer that catches these. Wrap ANY semantic
cache: before serving a cached hit, ask guard whether the match is safe.

Basic usage:
    from recalq_guard import is_safe_match

    # You have a candidate cache hit (cosine similarity already passed):
    if is_safe_match(user_query, cached_query):
        return cached_answer      # safe to serve
    else:
        call_the_llm()            # polarity/concept mismatch -> don't serve

Zero heavy dependencies. Pure Python.
"""
from .guard import is_safe_match, explain_match, GuardResult, Guard

__version__ = "0.1.0"
__all__ = ["is_safe_match", "explain_match", "GuardResult", "Guard"]
