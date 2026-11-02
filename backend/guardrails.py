"""Input boundary checks for customer complaints; no external services required.

This is a conservative first layer, not a complete prompt-injection or PII DLP system.
"""
import re
from dataclasses import dataclass, field

MAX_CHARS = 10000
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
INJECTION = re.compile(
    r'(?i)(?:ignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+instructions|'
    r'(?:reveal|print|show|dump)\s+(?:the\s+)?(?:system\s+prompt|developer\s+instructions|api\s+key|secret\s+key)|'
    r'<\s*/?\s*(?:system|developer)\s*>|'
    r'\b(?:system|developer)\s*:\s*(?:override|ignore\s+instructions))'
)
CARD = re.compile(r'(?<!\d)(?:\d[ -]?){13,19}(?!\d)')

@dataclass
class GuardrailResult:
    allowed: bool
    text: str
    reason: str = ''
    warnings: list[str] = field(default_factory=list)

def validate_customer_input(value: str) -> GuardrailResult:
    if not isinstance(value, str):
        return GuardrailResult(False, '', 'Message must be text.')
    cleaned = CONTROL.sub('', value).strip()
    if len(cleaned) < 5:
        return GuardrailResult(False, '', 'Please provide at least 5 characters describing your request.')
    if len(cleaned) > MAX_CHARS:
        return GuardrailResult(False, '', f'Message exceeds {MAX_CHARS} characters.')
    if INJECTION.search(cleaned):
        return GuardrailResult(False, '', 'The message contains instructions targeting the assistant. Please describe your support issue without AI control instructions.')
    warnings = []
    if CARD.search(cleaned):
        warnings.append('Possible payment card number detected. Do not share full card numbers in support chat.')
        # Do not forward potential full card numbers to LLM, RAG or database.
        cleaned = CARD.sub('[PAYMENT NUMBER REDACTED]', cleaned)
    return GuardrailResult(True, cleaned, warnings=warnings)
