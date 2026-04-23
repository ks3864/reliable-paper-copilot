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
        self.assertIn("Filter papers by title, file name, or id", response.text)
        self.assertIn("No papers loaded yet.", response.text)
        self.assertIn("Retrieval mode", response.text)
        self.assertIn("Hybrid fusion", response.text)

    def test_web_ui_surfaces_richer_paper_metadata_sections(self):
        response = self.client.get("/")

        self.assertIn("Automated ingestion notes", response.text)
        self.assertIn("Operator notes", response.text)
        self.assertIn("Abstract preview", response.text)
        self.assertIn("Extracted datasets", response.text)
        self.assertIn("Evidence", response.text)
        self.assertIn("Copy paper brief", response.text)
        self.assertIn("Download paper brief", response.text)
        self.assertIn("Export activity transcript", response.text)
        self.assertIn("Copy activity transcript", response.text)
        self.assertIn("Download activity transcript", response.text)
        self.assertIn("Copy or download the five most recent paper questions as a shareable Markdown transcript.", response.text)
        self.assertIn("Delete paper", response.text)
        self.assertIn("Recent question history", response.text)
        self.assertIn("Operator metadata history", response.text)
        self.assertIn("Edit operator metadata", response.text)
        self.assertIn("Source label", response.text)
        self.assertIn("Source URL", response.text)
        self.assertIn("Citation hint", response.text)
        self.assertIn("Save metadata", response.text)
        self.assertIn("function updatePaperDetails", response.text)
        self.assertIn("function renderEvidence", response.text)
        self.assertIn("function renderAnswer", response.text)
        self.assertIn("function buildPaperSearchText", response.text)
        self.assertIn("function sortPapersByRecency", response.text)
        self.assertIn("function getVisiblePapers", response.text)
        self.assertIn("function renderPaperOptions", response.text)
        self.assertIn("function buildBriefMarkdown", response.text)
        self.assertIn("function fetchPaperActivity", response.text)
        self.assertIn("function fetchPaperActivityTranscript", response.text)
        self.assertIn("function handleActivityTranscriptAction", response.text)
        self.assertIn("function savePaperMetadata", response.text)
        self.assertIn("function parseOperatorNotes", response.text)
        self.assertIn("function populateMetadataEditor", response.text)
        self.assertIn("function renderActivityItems", response.text)
        self.assertIn("function formatTimestamp", response.text)
        self.assertIn("function renderMetadataHistory", response.text)
        self.assertIn("Update ${Number(item.operator_update_count || 0) || \"?\"}", response.text)
        self.assertIn("Source URL saved", response.text)
        self.assertIn("history-item", response.text)
        self.assertIn("function handleBriefAction", response.text)
        self.assertIn("function handleDeletePaper", response.text)
        self.assertIn("window.confirm(`Delete ${paperLabel}? This removes the paper and its saved artifacts.`)", response.text)
        self.assertIn("citation-anchor", response.text)
        self.assertIn("is-highlighted", response.text)

    def test_web_ui_references_existing_api_routes(self):
        response = self.client.get("/")

        self.assertIn('fetch("/upload"', response.text)
        self.assertIn('fetch("/ask"', response.text)
        self.assertIn('fetch("/papers"', response.text)
        self.assertIn('fetch("/health"', response.text)
        self.assertIn('fetch(`/papers/${paperId}/brief`)', response.text)
        self.assertIn('fetch(`/papers/${paperId}/activity?limit=5`)', response.text)
        self.assertIn('fetch(`/papers/${paperId}/activity/export?limit=5`)', response.text)
        self.assertIn('fetch(`/papers/${paperId}/metadata`, {', response.text)
        self.assertIn('method: "PATCH"', response.text)
        self.assertIn('fetch(`/papers/${paperId}`, { method: "DELETE" })', response.text)
        self.assertIn('paperSearchInput.addEventListener("input"', response.text)
        self.assertIn('paperSelect.addEventListener("change"', response.text)
        self.assertIn('copyBriefButton.addEventListener("click"', response.text)
        self.assertIn('downloadBriefButton.addEventListener("click"', response.text)
        self.assertIn('copyActivityButton.addEventListener("click"', response.text)
        self.assertIn('downloadActivityButton.addEventListener("click"', response.text)
        self.assertIn('deletePaperButton.addEventListener("click"', response.text)
        self.assertIn('saveMetadataButton.addEventListener("click"', response.text)
        self.assertIn('last_operator_update_source: "web-ui"', response.text)
        self.assertIn('navigator.clipboard.writeText(briefMarkdown)', response.text)
        self.assertIn('navigator.clipboard.writeText(transcriptMarkdown)', response.text)
        self.assertIn('URL.createObjectURL(blob)', response.text)
        self.assertIn('Showing ${visibleCount} of ${totalCount} ${suffix}, newest first.', response.text)
        self.assertIn('${totalCount} ${suffix} available, newest first.', response.text)
        self.assertIn('await refreshPapers();', response.text)
        self.assertIn('retrieval_mode: retrievalMode', response.text)
        self.assertIn('renderRetrievalScores(payload)', response.text)
        self.assertIn('id="retrieval-scores-table"', response.text)


if __name__ == "__main__":
    unittest.main()
