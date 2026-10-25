
import unittest
from unittest.mock import patch

from search import search, cosine_similarity


class SearchTest(unittest.TestCase):
    def test_cosine_similarity_identical_vectors(self):
        vector = {"apache": 0.5, "beam": 0.7}

        score = cosine_similarity(vector, vector)

        self.assertAlmostEqual(score, 1.0)

    def test_cosine_similarity_without_common_terms(self):
        score = cosine_similarity(
            {"apache": 0.5},
            {"python": 0.7},
        )

        self.assertEqual(score, 0.0)

    def test_search_ranks_best_document_first(self):
        documents = [
            {
                "id": 1,
                "filename": "python.txt",
                "index_structure": {
                    "python": 0.8,
                    "programming": 0.4,
                },
            },
            {
                "id": 2,
                "filename": "beam.txt",
                "index_structure": {
                    "apache": 0.5,
                    "beam": 0.7,
                    "processing": 0.3,
                },
            },
        ]

        with patch("search.get_all_documents", return_value=documents):
            results = search("apache beam")

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "beam.txt")

    def test_search_returns_empty_for_stop_words_only(self):
        with patch("search.get_all_documents", return_value=[]):
            results = search("the and is")

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
