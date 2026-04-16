"""Tests for limitations extraction."""

import unittest

from src.extraction import extract_limitations


class LimitationsExtractorTests(unittest.TestCase):
    def test_extracts_limitations_from_chunks(self):
        chunks = [
            {
                "section": "discussion",
                "text": "Important limitations include the retrospective single-center design and possible selection bias. Future work should validate the findings prospectively.",
            },
            {
                "section": "conclusion",
                "text": "One limitation was the small sample size, which may reduce generalizability.",
            },
        ]

        results = extract_limitations(chunks=chunks)

        self.assertEqual(
            [item["text"] for item in results[:2]],
            [
                "The retrospective single-center design and possible selection bias",
                "The small sample size, which may reduce generalizability",
            ],
        )
        self.assertTrue(all("confidence" in item for item in results))

    def test_deduplicates_and_keeps_best_section(self):
        chunks = [
            {"section": "discussion", "text": "A limitation of this study was the lack of external validation."},
            {"section": "methods", "text": "A limitation of this study was the lack of external validation."},
        ]

        results = extract_limitations(chunks=chunks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "The lack of external validation")
        self.assertEqual(results[0]["section"], "discussion")

    def test_extracts_from_parsed_pages_when_chunks_not_provided(self):
        parsed_data = {
            "pages": [
                {
                    "page_number": 3,
                    "text": "We acknowledge that follow-up was limited to 6 months, which may underestimate late events.",
                }
            ]
        }

        results = extract_limitations(parsed_data=parsed_data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Follow-up was limited to 6 months, which may underestimate late events")
        self.assertEqual(results[0]["section"], "page_3")


if __name__ == "__main__":
    unittest.main()
