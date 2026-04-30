"""Tests for HMAC signature computation."""
import base64

from douban_scraper.frodo import compute_signature


def test_compute_signature_basic():
    """Signature should be a base64-encoded HMAC-SHA1 string."""
    sig = compute_signature("/api/v2/user/123/interests", "1234567890")
    assert isinstance(sig, str)
    assert len(sig) > 0
    # Should be valid base64
    base64.b64decode(sig)  # Should not raise


def test_compute_signature_deterministic():
    """Same inputs → same output."""
    sig1 = compute_signature("/api/v2/user/123/interests", "1234567890")
    sig2 = compute_signature("/api/v2/user/123/interests", "1234567890")
    assert sig1 == sig2


def test_compute_signature_different_inputs():
    """Different inputs → different outputs."""
    sig1 = compute_signature("/api/v2/user/123/interests", "1234567890")
    sig2 = compute_signature("/api/v2/user/456/interests", "0987654321")
    assert sig1 != sig2


def test_compute_signature_sha1_length():
    """Decoded signature should be exactly 20 bytes (SHA-1)."""
    sig = compute_signature("/api/v2/user/123/interests", "1234567890")
    decoded = base64.b64decode(sig)
    assert len(decoded) == 20


def test_compute_signature_url_encoded():
    """URL path with special characters should be encoded before signing."""
    sig1 = compute_signature("/api/v2/user/123/interests", "9999")
    sig2 = compute_signature("/api/v2/user/123/interests?type=movie", "9999")
    assert sig1 != sig2  # Different paths → different sigs
