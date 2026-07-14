"""
Example: add negation-safety to LiteLLM's semantic cache.

LiteLLM (and most gateways) serve a cached answer whenever cosine
similarity passes a threshold. That returns WRONG answers on negation.
recalq-guard adds one check before you trust the hit.
"""
from recalq_guard import is_safe_match

def safe_cache_lookup(user_query, cache):
    """
    cache.semantic_search(q) -> (cached_query, cached_answer, score) or None
    Wrap it so a polarity/concept conflict falls through to the LLM.
    """
    hit = cache.semantic_search(user_query)
    if hit is None:
        return None
    cached_query, cached_answer, score = hit
    if is_safe_match(user_query, cached_query):
        return cached_answer          # safe — serve from cache
    return None                        # unsafe — treat as miss, call LLM

# One line changes plain caching into negation-aware caching.
