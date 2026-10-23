from __future__ import annotations

import hashlib
import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?88)?01[3-9]\d{8}(?!\d)")
INTL_PHONE_RE = re.compile(r"(?<!\d)\+\d{1,3}[\s-]?\d{6,14}(?!\d)")
NID_RE = re.compile(r"(?<!\d)\d{10,17}(?!\d)")
PASSPORT_RE = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")

PROHIBITED_LEGAL_PHRASES = (
    "you are compliant",
    "this is legal",
    "legally compliant",
    "this contract is enforceable",
    "we guarantee compliance",
    "guaranteed compliant",
    "legal advice",
    "certified compliant",
)

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "reveal your prompt",
    "you are now",
    "act as",
    "disregard the above",
    "developer message",
)


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}

    def replace(pattern: re.Pattern[str], label: str, value: str) -> str:
        matches = list(pattern.finditer(value))
        if matches:
            counts[label] = len(matches)
            return pattern.sub(f"[REDACTED_{label.upper()}]", value)
        return value

    redacted = replace(EMAIL_RE, "email", text)
    redacted = replace(PHONE_RE, "phone", redacted)
    redacted = replace(INTL_PHONE_RE, "phone", redacted)
    redacted = replace(NID_RE, "id_number", redacted)
    redacted = replace(PASSPORT_RE, "passport", redacted)
    return redacted, counts


def has_prompt_injection(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in PROMPT_INJECTION_MARKERS)


def find_prohibited_legal_phrases(text: str) -> list[str]:
    lower = text.lower()
    return [phrase for phrase in PROHIBITED_LEGAL_PHRASES if phrase in lower]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
