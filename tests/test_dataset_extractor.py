"""Tests for dataset name extraction."""

import unittest

from src.extraction import extract_dataset_names


class DatasetExtractorTests(unittest.TestCase):
    def test_extracts_dataset_names_from_chunks(self):
        chunks = [
            {
                "section": "methods",
                "text": "We trained the model on the MIMIC-III dataset and evaluated on the CheXpert dataset.",
            },
            {
                "section": "results",
                "text": "Performance on the PhysioNet Challenge benchmark remained strong across ablations.",
            },
        ]

        results = extract_dataset_names(chunks=chunks)

        self.assertEqual([item["name"] for item in results[:3]], ["CheXpert", "MIMIC-III", "PhysioNet Challenge"])
        self.assertTrue(all("confidence" in item for item in results))

    def test_deduplicates_and_keeps_best_evidence(self):
        chunks = [
            {"section": "abstract", "text": "We use the ImageNet dataset for pretraining."},
            {"section": "discussion", "text": "The ImageNet dataset is widely adopted."},
        ]

        results = extract_dataset_names(chunks=chunks)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ImageNet")
        self.assertEqual(results[0]["section"], "abstract")

    def test_extracts_from_parsed_pages_when_chunks_not_provided(self):
        parsed_data = {
            "pages": [
                {"page_number": 1, "text": "Our experiments use the TCGA cohort for survival prediction."}
            ]
        }

        results = extract_dataset_names(parsed_data=parsed_data)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "TCGA")
        self.assertEqual(results[0]["section"], "page_1")


if __name__ == "__main__":
    unittest.main()
