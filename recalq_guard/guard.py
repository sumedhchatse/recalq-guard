"""
Core guard logic — polarity/negation + concept-overlap checks.
Pure Python, no dependencies. Works with any semantic cache.
"""
import re
from dataclasses import dataclass, field
from typing import Optional, List

# Antonym pairs where a match would give the OPPOSITE (wrong) answer.
DEFAULT_POLARITY_PAIRS = [
    ("enable", "disable"), ("enabled", "disabled"), ("allow", "deny"),
    ("allow", "block"), ("increase", "decrease"), ("add", "remove"),
    ("start", "stop"), ("open", "close"), ("mount", "unmount"),
    ("grant", "revoke"), ("activate", "deactivate"), ("connect", "disconnect"),
    ("install", "uninstall"), ("lock", "unlock"), ("show", "hide"),
    ("expand", "shrink"), ("attach", "detach"), ("bind", "unbind"),
    ("accept", "reject"), ("include", "exclude"), ("create", "delete"),
    ("turn on", "turn off"), ("power on", "power off"), ("up", "down"),
    ("encrypt", "decrypt"), ("compress", "decompress"), ("import", "export"),
]

NEGATION_TOKENS = {
    "not", "no", "never", "without", "cannot", "can't", "dont", "don't",
    "avoid", "prevent", "stop", "except", "excluding", "neither", "nor",
}

# Minimal stopwords so concept overlap focuses on meaningful terms.
STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "or", "is", "are",
    "how", "what", "why", "when", "where", "do", "does", "i", "my", "with",
    "can", "you", "me", "please", "explain", "tell", "about", "give", "this",
}


@dataclass
class GuardResult:
    safe: bool
    reason: str
    polarity_conflict: bool = False
    concept_gap: bool = False
    details: dict = field(default_factory=dict)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _polarity_sides(tokens, pairs):
    text = " " + " ".join(tokens) + " "
    sides = set()
    for a, b in pairs:
        if f" {a} " in text: sides.add((a, b, "a"))
        if f" {b} " in text: sides.add((a, b, "b"))
    return sides


def _has_negation(tokens):
    return bool(set(tokens) & NEGATION_TOKENS)


class Guard:
    """
    Configurable guard. Use the module-level is_safe_match() for defaults,
    or instantiate Guard(...) to customize thresholds / antonym pairs.
    """
    def __init__(self, polarity_pairs=None, min_concept_overlap=0.6,
                 check_negation=True, check_concepts=True):
        self.pairs = polarity_pairs or DEFAULT_POLARITY_PAIRS
        self.min_concept_overlap = min_concept_overlap
        self.check_negation = check_negation
        self.check_concepts = check_concepts

    def evaluate(self, query: str, cached_query: str) -> GuardResult:
        q = _tokens(query)
        c = _tokens(cached_query)

        # 1. Polarity conflict — opposite side of an antonym pair
        q_sides = _polarity_sides(q, self.pairs)
        c_sides = _polarity_sides(c, self.pairs)
        for (a, b, sq) in q_sides:
            for (a2, b2, sc) in c_sides:
                if a == a2 and b == b2 and sq != sc:
                    return GuardResult(
                        safe=False,
                        reason=f"polarity conflict: '{a if sq=='a' else b}' vs '{a2 if sc=='a' else b2}'",
                        polarity_conflict=True,
                        details={"pair": (a, b)},
                    )

        # 2. Negation asymmetry — one negates, the other doesn't
        if self.check_negation:
            if _has_negation(q) != _has_negation(c):
                return GuardResult(
                    safe=False,
                    reason="negation asymmetry (one query negates, the other does not)",
                    polarity_conflict=True,
                )

        # 3. Concept overlap — major content words must sufficiently match
        if self.check_concepts:
            qc = {w for w in q if w not in STOPWORDS and len(w) > 2}
            cc = {w for w in c if w not in STOPWORDS and len(w) > 2}
            if qc:
                overlap = len(qc & cc) / len(qc)
                if overlap <= self.min_concept_overlap:
                    return GuardResult(
                        safe=False,
                        reason=f"concept gap: only {overlap:.0%} of query concepts in cached query",
                        concept_gap=True,
                        details={"overlap": round(overlap, 2), "missing": sorted(qc - cc)},
                    )

        return GuardResult(safe=True, reason="no polarity or concept conflict")


_default_guard = Guard()

def is_safe_match(query: str, cached_query: str) -> bool:
    """Return True if serving the cached answer for `query` is safe."""
    return _default_guard.evaluate(query, cached_query).safe

def explain_match(query: str, cached_query: str) -> GuardResult:
    """Return the full GuardResult with reason and details."""
    return _default_guard.evaluate(query, cached_query)
