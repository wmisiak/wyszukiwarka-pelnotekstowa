
import hashlib
import math
from pathlib import Path

import apache_beam as beam
import psycopg
from psycopg.types.json import Jsonb
from apache_beam.pvalue import AsDict, AsSingleton

from database import DB_CONFIG
from transforms import TokenizeDocument


DATA_DIR = Path("data")


def read_document(filename: str) -> dict:
    """Odczytuje plik tekstowy i nadaje mu stabilne ID."""

    path = Path(filename)
    text = path.read_text(encoding="utf-8")

    # Stabilne ID: ten sam względny filename daje to samo ID.
    digest = hashlib.sha256(filename.encode("utf-8")).digest()
    document_id = int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF

    return {
        "id": document_id,
        "filename": filename,
        "text": text,
    }


def calculate_document_frequency(document: dict):
    """Emituje parę (token, 1) dla każdego unikalnego tokenu w dokumencie."""

    for token in document["term_frequency"]:
        yield token, 1


def calculate_idf(item, number_of_documents: int):
    """Oblicza wygładzone IDF dla tokenu."""

    token, document_frequency = item

    idf = math.log(
        (number_of_documents + 1) / (document_frequency + 1)
    ) + 1

    return token, idf


def build_tfidf_index(
    document: dict,
    idf_values: dict[str, float],
) -> dict:
    """Buduje indeks TF-IDF pojedynczego dokumentu."""

    frequencies = document["term_frequency"]
    total_terms = sum(frequencies.values())

    if total_terms == 0:
        weights = {}
    else:
        weights = {
            token: round(
                (frequency / total_terms) * idf_values[token],
                8,
            )
            for token, frequency in frequencies.items()
        }

    return {
        "id": document["id"],
        "filename": document["filename"],
        "index_structure": weights,
    }


class WriteToPostgresBatch(beam.DoFn):
    """Zapisuje indeksy do PostgreSQL partiami."""

    def __init__(self, db_config: dict, batch_size: int = 100):
        self.db_config = db_config
        self.batch_size = batch_size
        self.conn = None
        self.cursor = None
        self.buffer = []

    def setup(self):
        self.conn = psycopg.connect(**self.db_config)
        self.cursor = self.conn.cursor()

    def start_bundle(self):
        self.buffer = []

    def process(self, element: dict):
        self.buffer.append(
            (
                element["id"],
                element["filename"],
                Jsonb(element["index_structure"]),
            )
        )

        if len(self.buffer) >= self.batch_size:
            self._flush()

    def finish_bundle(self):
        if self.buffer:
            self._flush()

    def _flush(self):
        query = """
            INSERT INTO files (id, filename, index_structure)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                filename = EXCLUDED.filename,
                index_structure = EXCLUDED.index_structure
        """

        self.cursor.executemany(query, self.buffer)
        self.conn.commit()
        self.buffer.clear()

    def teardown(self):
        if self.cursor is not None:
            self.cursor.close()

        if self.conn is not None:
            self.conn.close()


def main():
    filenames = sorted(
        str(path)
        for path in DATA_DIR.glob("*.txt")
        if path.is_file()
    )

    if not filenames:
        raise RuntimeError(
            f"Nie znaleziono plików .txt w katalogu {DATA_DIR.resolve()}"
        )

    with beam.Pipeline() as pipeline:
        documents = (
            pipeline
            | "Utwórz listę plików" >> beam.Create(filenames)
            | "Odczytaj dokumenty" >> beam.Map(read_document)
        )

        tokenized_documents = (
            documents
            | "Tokenizacja i częstości" >> beam.ParDo(TokenizeDocument())
        )

        number_of_documents = (
            tokenized_documents
            | "Policz dokumenty" >> beam.combiners.Count.Globally()
        )

        document_frequencies = (
            tokenized_documents
            | "Unikalne tokeny dokumentów"
            >> beam.FlatMap(calculate_document_frequency)
            | "Policz dokumenty zawierające token"
            >> beam.CombinePerKey(sum)
        )

        idf_values = (
            document_frequencies
            | "Oblicz IDF"
            >> beam.Map(
                calculate_idf,
                number_of_documents=AsSingleton(number_of_documents),
            )
        )

        indexed_documents = (
            tokenized_documents
            | "Oblicz TF-IDF"
            >> beam.Map(
                build_tfidf_index,
                idf_values=AsDict(idf_values),
            )
        )

        indexed_documents | "Zapisz indeksy w PostgreSQL" >> beam.ParDo(
            WriteToPostgresBatch(DB_CONFIG)
        )


if __name__ == "__main__":
    main()
