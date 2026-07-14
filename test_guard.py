"""Tests for recalq-guard. Run: python3 -m pytest test_guard.py -v"""
from recalq_guard import is_safe_match, explain_match

def test_negation_enable_disable():
    assert is_safe_match("how to enable ssh root", "how to enable ssh root") is True
    assert is_safe_match("how to disable ssh root", "how to enable ssh root") is False

def test_negation_increase_decrease():
    assert is_safe_match("how to decrease memory", "how to increase memory") is False

def test_negation_word():
    assert is_safe_match("how to connect without vpn", "how to connect with vpn") is False

def test_entity_swap():
    assert is_safe_match("restart apache", "restart nginx") is False

def test_legit_rephrase_passes():
    assert is_safe_match("explain kubernetes", "what is kubernetes") is True
    assert is_safe_match("how do I restart the nginx service", "how to restart nginx service") is True

def test_explain_gives_reason():
    r = explain_match("how to disable ssh", "how to enable ssh")
    assert r.safe is False
    assert r.polarity_conflict is True
    assert "polarity" in r.reason
