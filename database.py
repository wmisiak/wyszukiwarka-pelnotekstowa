
import os
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "indexer_db"),
    "user": os.getenv("DB_USER", "a_user"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def save_document(
    document_id: int,
    filename: str,
    index_structure: dict[str, float],
) -> None:
    """Zapisuje dokument i jego indeks TF-IDF do PostgreSQL."""

    query = """
        INSERT INTO files (id, filename, index_structure)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            filename = EXCLUDED.filename,
            index_structure = EXCLUDED.index_structure
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        conn.execute(
            query,
            (document_id, filename, Jsonb(index_structure)),
        )


def get_document(document_id: int) -> dict | None:
    """Pobiera dokument o podanym identyfikatorze."""

    query = """
        SELECT id, filename, index_structure
        FROM files
        WHERE id = %s
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        row = conn.execute(query, (document_id,)).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "index_structure": row[2],
    }


def get_all_documents() -> list[dict]:
    """Pobiera wszystkie dokumenty z bazy."""

    query = """
        SELECT id, filename, index_structure
        FROM files
        ORDER BY id
    """

    with psycopg.connect(**DB_CONFIG) as conn:
        rows = conn.execute(query).fetchall()

    return [
        {
            "id": row[0],
            "filename": row[1],
            "index_structure": row[2],
        }
        for row in rows
    ]
