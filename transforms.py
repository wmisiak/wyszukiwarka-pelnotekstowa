
import re
from collections import Counter

import apache_beam as beam


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "for", "from", "in", "is", "it", "of", "on", "or",
    "the", "to", "with", "this", "that",
}


def tokenize(text: str) -> list[str]:
    """Dzieli tekst na małe litery i usuwa interpunkcję."""

    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def remove_stop_words(tokens: list[str]) -> list[str]:
    """Usuwa stop words oraz bardzo krótkie tokeny."""

    return [
        token
        for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]


def calculate_term_frequency(tokens: list[str]) -> dict[str, int]:
    """Zwraca liczbę wystąpień każdego tokenu."""

    return dict(Counter(tokens))


class TokenizeDocument(beam.DoFn):
    """Przygotowuje tekst dokumentu do indeksowania."""

    def process(self, document: dict):
        tokens = tokenize(document["text"])
        tokens = remove_stop_words(tokens)

        yield {
            "id": document["id"],
            "filename": document["filename"],
            "term_frequency": calculate_term_frequency(tokens),
        }
