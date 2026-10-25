
import math
import sys
from collections import Counter

from database import get_all_documents
from transforms import tokenize, remove_stop_words


def cosine_similarity(
    query_vector: dict[str, float],
    document_vector: dict[str, float],
) -> float:
    """Oblicza podobieństwo cosinusowe dwóch wektorów."""

    common_terms = query_vector.keys() & document_vector.keys()

    dot_product = sum(
        query_vector[token] * document_vector[token]
        for token in common_terms
    )

    query_norm = math.sqrt(
        sum(weight ** 2 for weight in query_vector.values())
    )
    document_norm = math.sqrt(
        sum(weight ** 2 for weight in document_vector.values())
    )

    if query_norm == 0 or document_norm == 0:
        return 0.0

    return dot_product / (query_norm * document_norm)


def search(query: str, limit: int = 10) -> list[dict]:
    """Zwraca dokumenty uporządkowane według podobieństwa do zapytania."""

    documents = get_all_documents()

    if not documents:
        return []

    query_tokens = remove_stop_words(tokenize(query))

    if not query_tokens:
        return []

    query_frequencies = Counter(query_tokens)
    number_of_documents = len(documents)

    # Liczba dokumentów zawierających każdy token.
    document_frequency = Counter()

    for document in documents:
        document_frequency.update(
            document["index_structure"].keys()
        )

    # Wagi zapytania liczymy według tych samych statystyk IDF,
    # które odpowiadają aktualnemu indeksowi dokumentów.
    total_query_terms = sum(query_frequencies.values())

    query_vector = {}

    for token, frequency in query_frequencies.items():
        df = document_frequency.get(token, 0)

        if df == 0:
            continue

        idf = math.log(
            (number_of_documents + 1) / (df + 1)
        ) + 1

        query_vector[token] = (
            frequency / total_query_terms
        ) * idf

    if not query_vector:
        return []

    results = []

    for document in documents:
        score = cosine_similarity(
            query_vector,
            document["index_structure"],
        )

        if score > 0:
            results.append({
                "id": document["id"],
                "filename": document["filename"],
                "score": score,
            })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:limit]


def main():
    if len(sys.argv) < 2:
        print('Użycie: python search.py "zapytanie"')
        return

    query = " ".join(sys.argv[1:])
    results = search(query)

    print(f'\nWyniki dla zapytania: "{query}"\n')

    if not results:
        print("Nie znaleziono pasujących dokumentów.")
        return

    for position, result in enumerate(results, start=1):
        print(
            f"{position}. {result['filename']}\n"
            f"   ID: {result['id']}\n"
            f"   Podobieństwo: {result['score']:.4f}"
        )


if __name__ == "__main__":
    main()
