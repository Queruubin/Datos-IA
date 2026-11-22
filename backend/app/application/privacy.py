"""PII masking applied to every question before it is sent to the LLM or stored."""

import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A run of digits that may be split by spaces, dots or dashes ('300 123 4567', '1.023.456.789'),
# optionally with an international prefix ('+57 ...').
DIGIT_RUN = re.compile(r"(?<![\w$])\+?\d(?:[ .-]?\d)*(?!\w)")
YEAR = re.compile(r"(?:19|20)\d{2}")
MIN_SENSITIVE_DIGITS = 6  # cédulas have 6-10 digits, phones 7-10; years (4) are kept

EMAIL_MASK = "[CORREO]"
NUMBER_MASK = "[NUMERO]"


def mask_pii(text: str) -> str:
    """Mask emails and phone/ID-like numbers. Years ('2025', '2024-2025') and amounts written
    with a '$' are kept because they are needed to answer the question."""
    masked = EMAIL.sub(EMAIL_MASK, text)
    return DIGIT_RUN.sub(_mask_number, masked)


def _mask_number(match: re.Match[str]) -> str:
    value = match.group()
    digits = re.sub(r"\D", "", value)
    if len(digits) < MIN_SENSITIVE_DIGITS:
        return value
    if match.string[: match.start()].rstrip().endswith("$"):  # an amount, not a person
        return value
    groups = [group for group in re.split(r"[ .-]", value.lstrip("+")) if group]
    if all(YEAR.fullmatch(group) for group in groups):  # e.g. '2024 2025' or '2024-2025'
        return value
    return NUMBER_MASK
