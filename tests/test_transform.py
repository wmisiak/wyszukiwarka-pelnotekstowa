
import unittest

from transforms import (
    tokenize,
    remove_stop_words,
    calculate_term_frequency,
)


class TransformsTest(unittest.TestCase):
    def test_tokenize(self):
        self.assertEqual(
            tokenize("Hello, Apache Beam!"),
            ["hello", "apache", "beam"],
        )

    def test_remove_stop_words(self):
        self.assertEqual(
            remove_stop_words(["the", "apache", "beam", "a"]),
            ["apache", "beam"],
        )

    def test_term_frequency(self):
        self.assertEqual(
            calculate_term_frequency(["beam", "apache", "beam"]),
            {"beam": 2, "apache": 1},
        )


if __name__ == "__main__":
    unittest.main()
