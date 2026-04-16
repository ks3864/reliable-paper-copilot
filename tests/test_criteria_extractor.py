"""Tests for inclusion and exclusion criteria extraction."""

import unittest

from src.extraction import extract_inclusion_exclusion_criteria


class CriteriaExtractorTests(unittest.TestCase):
    def test_extracts_inclusion_and_exclusion_criteria_from_chunks(self):
        chunks = [
            {
                "section": "methods",
                "text": "Inclusion criteria included adults aged 18 years or older with confirmed ischemic stroke. Exclusion criteria included prior intracranial hemorrhage or missing baseline imaging.",
            },
            {
                "section": "study population",
                "text": "Participants were eligible if they provided written informed consent and had at least 12 months of follow-up.",
            },
        ]

        results = extract_inclusion_exclusion_criteria(chunks=chunks)

        self.assertEqual(
            [(item["type"], item["text"]) for item in results[:3]],
            [
                ("inclusion", "Adults aged 18 years or older with confirmed ischemic stroke"),
                ("inclusion", "They provided written informed consent and had at least 12 months of follow-up"),
                ("exclusion", "Prior intracranial hemorrhage or missing baseline imaging"),
            ],
        )
        self.assertTrue(all("confidence" in item for item in results))

    def test_deduplicates_and_keeps_best_section(self):
        chunks = [
            {"section": "methods", "text": "Exclusion criteria included active infection or pregnancy."},
            {"section": "discussion", "text": "Exclusion criteria included active infection or pregnancy."},
        ]

        results = extract_inclusion_exclusion_criteria(chunks=chunks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "exclusion")
        self.assertEqual(results[0]["text"], "Active infection or pregnancy")
        self.assertEqual(results[0]["section"], "methods")

    def test_extracts_from_parsed_pages_when_chunks_not_provided(self):
        parsed_data = {
            "pages": [
                {
                    "page_number": 4,
                    "text": "Patients were excluded if they had severe renal failure or incomplete laboratory data.",
                }
            ]
        }

        results = extract_inclusion_exclusion_criteria(parsed_data=parsed_data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "exclusion")
        self.assertEqual(results[0]["text"], "They had severe renal failure or incomplete laboratory data")
        self.assertEqual(results[0]["section"], "page_4")


if __name__ == "__main__":
    unittest.main()
