# recalq-guard

**Stop your semantic cache from serving "enable" when the user asked "disable".**

Plain semantic caching returns a cached answer whenever cosine similarity clears a threshold. But `"how to enable ssh root login"` and `"how to disable ssh root login"` are **95%+ similar** — and have **opposite** answers. Serving the wrong one is a security incident.

`recalq-guard` is a tiny, zero-dependency layer that catches these before you serve them. Wrap **any** semantic cache (LiteLLM, Portkey, your own) with one check.

```python
from recalq_guard import is_safe_match

if is_safe_match(user_query, cached_query):
    return cached_answer      # safe to serve
else:
    call_the_llm()            # polarity/concept conflict — don't serve a wrong answer
```

## Install

```bash
pip install recalq-guard
```

Zero heavy dependencies. Pure Python. Works with any embedding model or cache backend — it inspects the *text*, not the vectors.

## The problem it solves

Semantic caches match by meaning-similarity. That's great — until meaning *flips* on a word:

| User asks | Cache has | Cosine sim | Plain cache | Correct? |
|---|---|---|---|---|
| how to **disable** ssh root | how to **enable** ssh root | ~0.95 | serves "enable" answer | **WRONG** |
| how to **decrease** memory | how to **increase** memory | ~0.94 | serves "increase" answer | **WRONG** |
| how to **block** port 22 | how to **allow** port 22 | ~0.92 | serves "allow" answer | **WRONG** |

`recalq-guard` catches all three.

## Benchmark

Head-to-head on adversarial queries (same embedding model, same threshold; only the matching logic differs):

```
Dangerous cases (must reject):        9
  Plain semantic cache — wrong:       3/9   (enable/disable, increase/decrease, allow/block)
  recalq-guard — wrong:               0/9

Legitimate rephrasings (should match): 2
  Plain — missed:                      0/2
  recalq-guard — missed:               0/2
```

**Plain caching served 3 wrong answers. recalq-guard served 0 — without breaking a single legitimate match.**

Run it yourself: `python3 benchmark.py`

## How it works

Three checks, all pure-text, no LLM call, sub-millisecond:

1. **Polarity conflict** — opposite sides of an antonym pair (enable/disable, start/stop, allow/deny, +25 more, customizable).
2. **Negation asymmetry** — one query says "without/not/never", the other doesn't.
3. **Concept gap** — the distinctive content words don't sufficiently overlap (catches entity swaps like nginx↔apache).

## Customize

```python
from recalq_guard import Guard

guard = Guard(
    polarity_pairs=[("promote", "demote"), ("scale up", "scale down")],  # add your domain's antonyms
    min_concept_overlap=0.6,
)
result = guard.evaluate("how to demote a node", "how to promote a node")
print(result.safe, result.reason)   # False, "polarity conflict: 'promote' vs 'demote'"
```

## LiteLLM integration

See `examples/litellm_integration.py` — one wrapper function turns plain caching into negation-aware caching.

## Why this exists

`recalq-guard` is the open-source safety layer extracted from **Recalq** — a private semantic orchestration engine that adds intent-aware routing and compositional answer synthesis on top of caching. The negation guard is the piece that's useful to everyone, so it's open. The orchestration engine is not public.

If you're working on semantic caching, routing, or LLM infrastructure and want to talk about the rest, reach out.

## License

MIT.
