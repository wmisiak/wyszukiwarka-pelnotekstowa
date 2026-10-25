
import unittest

from indexer import calculate_idf, build_tfidf_index


class IndexerTest(unittest.TestCase):
    def test_calculate_idf(self):
        token, idf = calculate_idf(
            ("python", 2),
            number_of_documents=4,
        )

        self.assertEqual(token, "python")
        self.assertAlmostEqual(idf, 1.5108256238)

    def test_tfidf_weights(self):
        document = {
            "id": 1,
            "filename": "python.txt",
            "term_frequency": {
                "python": 2,
                "code": 1,
            },
        }

        idf_values = {
            "python": 1.5,
            "code": 2.0,
        }

        result = build_tfidf_index(document, idf_values)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["filename"], "python.txt")
        self.assertAlmostEqual(
            result["index_structure"]["python"],
            1.0,
        )
        self.assertAlmostEqual(
            result["index_structure"]["code"],
            0.66666667,
        )

    def test_empty_document(self):
        document = {
            "id": 2,
            "filename": "empty.txt",
            "term_frequency": {},
        }

        result = build_tfidf_index(document, {})

        self.assertEqual(result["index_structure"], {})


if __name__ == "__main__":
    unittest.main()
