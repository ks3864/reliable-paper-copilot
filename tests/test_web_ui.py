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

    def test_web_ui_references_existing_api_routes(self):
        response = self.client.get("/")

        self.assertIn('fetch("/upload"', response.text)
        self.assertIn('fetch("/ask"', response.text)
        self.assertIn('fetch("/papers"', response.text)
        self.assertIn('fetch("/health"', response.text)


if __name__ == "__main__":
    unittest.main()
