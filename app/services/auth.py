"""Authentication helpers for hashing and verifying user PINs."""

from __future__ import annotations

import re

import bcrypt

PIN_PATTERN: re.Pattern[str] = re.compile(r"^\d{4,6}$")


def is_valid_pin(pin: str) -> bool:
    """Return True if the PIN is 4-6 numeric digits."""
    if not isinstance(pin, str):
        return False
    return bool(PIN_PATTERN.match(pin))


def hash_pin(pin: str) -> str:
    """Hash a numeric PIN using bcrypt."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against a stored bcrypt hash."""
    if not pin or not pin_hash:
        return False
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except ValueError:
        return False
