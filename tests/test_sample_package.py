import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts.fetch_sample_package import fetch_sample_package, load_manifest


class SamplePackageTests(TestCase):
    def test_sample_package_manifest_and_questions_exist(self):
        package_dir = Path("sample_packages/attention-is-all-you-need")
        manifest = load_manifest(package_dir)
        questions = json.loads((package_dir / "questions.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["package_id"], "attention-is-all-you-need")
        self.assertTrue(manifest["paper_url"].startswith("https://"))
        self.assertGreaterEqual(len(questions), 3)
        self.assertTrue(all("question" in item for item in questions))

    def test_fetch_sample_package_downloads_to_requested_directory(self):
        package_dir = Path("sample_packages/attention-is-all-you-need")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "downloads"

            def fake_urlretrieve(url, destination):
                Path(destination).write_bytes(b"%PDF-1.4\n%fake\n")
                return str(destination), None

            with patch("scripts.fetch_sample_package.urlretrieve", side_effect=fake_urlretrieve) as mocked:
                output_path = fetch_sample_package(package_dir, output_dir)

            self.assertEqual(output_path, output_dir / "attention-is-all-you-need.pdf")
            self.assertTrue(output_path.exists())
            mocked.assert_called_once()
