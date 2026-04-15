import unittest

from src.chunking.chunker import chunk_by_sections


class ChunkingV2Tests(unittest.TestCase):
    def test_overlapping_section_chunks_preserve_context(self):
        parsed = {
            "metadata": {"title": "Test Paper"},
            "pages": [
                {
                    "page_num": 1,
                    "text": (
                        "Introduction\n\n"
                        "Sentence one is short. Sentence two adds a bit more context. "
                        "Sentence three should force another chunk. Sentence four keeps the story going."
                    ),
                }
            ],
        }

        chunks = chunk_by_sections(
            parsed,
            max_chunk_size=85,
            overlap_size=30,
            max_tokens=40,
            overlap_tokens=8,
        )

        content_chunks = [chunk for chunk in chunks if "Sentence" in chunk["text"]]

        self.assertGreaterEqual(len(content_chunks), 2)
        self.assertEqual(content_chunks[0]["metadata"]["chunking_strategy"], "section_overlap")
        self.assertEqual(content_chunks[1]["metadata"]["chunking_strategy"], "section_overlap")
        self.assertIn("Sentence two adds a bit more context.", content_chunks[0]["text"])
        self.assertIn("Sentence two adds a bit more context.", content_chunks[1]["text"])

    def test_token_fallback_handles_long_sentence(self):
        long_sentence = " ".join(f"token{i}" for i in range(80))
        parsed = {
            "metadata": {"title": "Token Paper"},
            "pages": [{"page_num": 1, "text": f"Methods\n\n{long_sentence}"}],
        }

        chunks = chunk_by_sections(
            parsed,
            max_chunk_size=120,
            overlap_size=20,
            max_tokens=18,
            overlap_tokens=4,
        )

        token_chunks = [chunk for chunk in chunks if chunk["metadata"]["chunking_strategy"] == "token_fallback"]

        self.assertGreaterEqual(len(token_chunks), 2)
        self.assertTrue(all(chunk["metadata"]["token_count_estimate"] <= 18 for chunk in token_chunks))
        self.assertIn("token14 token15 token16 token17", token_chunks[0]["text"])
        self.assertIn("token14 token15 token16 token17", token_chunks[1]["text"])


if __name__ == "__main__":
    unittest.main()
