"""Small text helpers shared by every source parser."""

import re
import unicodedata


def strip_accents(text: object) -> str:
    """Remove accents/diacritics: 'Cristóbal' -> 'Cristobal'."""
    decomposed = unicodedata.normalize("NFKD", str(text))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_column(name: object) -> str:
    """Snake_case column name:'% de avance  propuesta' -> 'pct_de_avance_propuesta'."""
    text = strip_accents(name).lower().replace("%", "pct")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def normalize_label(value: object) -> str:
    """Canonical form for category labels: uppercase, no accents, single spaces."""
    return re.sub(r"\s+", " ", strip_accents(value).upper()).strip()
