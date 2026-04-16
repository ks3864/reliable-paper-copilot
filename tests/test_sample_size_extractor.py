"""Tests for sample size extraction."""

import unittest

from src.extraction import extract_sample_sizes


class SampleSizeExtractorTests(unittest.TestCase):
    def test_extracts_sample_sizes_from_chunks(self):
        chunks = [
            {
                "section": "methods",
                "text": "We enrolled 1,245 patients across three hospitals. An external validation cohort of 210 subjects was also analyzed.",
            },
            {
                "section": "results",
                "text": "In the ablation study, N = 87 samples had complete follow-up.",
            },
        ]

        results = extract_sample_sizes(chunks=chunks)

        self.assertEqual([item["value"] for item in results[:3]], [1245, 210, 87])
        self.assertTrue(all("confidence" in item for item in results))

    def test_deduplicates_same_match(self):
        chunks = [
            {"section": "abstract", "text": "A total of 512 participants were enrolled."},
            {"section": "discussion", "text": "A total of 512 participants were enrolled."},
        ]

        results = extract_sample_sizes(chunks=chunks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["value"], 512)
        self.assertEqual(results[0]["section"], "abstract")

    def test_extracts_from_parsed_pages_when_chunks_not_provided(self):
        parsed_data = {
            "pages": [
                {"page_number": 2, "text": "The study included 340 individuals with longitudinal imaging."}
            ]
        }

        results = extract_sample_sizes(parsed_data=parsed_data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["value"], 340)
        self.assertEqual(results[0]["section"], "page_2")


if __name__ == "__main__":
    unittest.main()
