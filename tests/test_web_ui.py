import unittest

from fastapi.testclient import TestClient

from src.api.main import app


class WebUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_serves_web_ui(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Reliable Scientific Paper Copilot", response.text)
        self.assertIn("Upload a PDF", response.text)
        self.assertIn("Ask a question", response.text)
        self.assertIn("Selected paper details", response.text)
        self.assertIn("Retrieval mode", response.text)
        self.assertIn("Hybrid fusion", response.text)

    def test_web_ui_surfaces_richer_paper_metadata_sections(self):
        response = self.client.get("/")

        self.assertIn("Automated ingestion notes", response.text)
        self.assertIn("Operator notes", response.text)
        self.assertIn("Abstract preview", response.text)
        self.assertIn("Extracted datasets", response.text)
        self.assertIn("Evidence", response.text)
        self.assertIn("function updatePaperDetails", response.text)
        self.assertIn("function renderEvidence", response.text)
        self.assertIn("function renderAnswer", response.text)
        self.assertIn("citation-anchor", response.text)
        self.assertIn("is-highlighted", response.text)

    def test_web_ui_references_existing_api_routes(self):
        response = self.client.get("/")

        self.assertIn('fetch("/upload"', response.text)
        self.assertIn('fetch("/ask"', response.text)
        self.assertIn('fetch("/papers"', response.text)
        self.assertIn('fetch("/health"', response.text)
        self.assertIn('paperSelect.addEventListener("change"', response.text)
        self.assertIn('retrieval_mode: retrievalMode', response.text)
        self.assertIn('renderRetrievalScores(payload)', response.text)
        self.assertIn('id="retrieval-scores-table"', response.text)


if __name__ == "__main__":
    unittest.main()
