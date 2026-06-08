import unittest

from embed_store import _rank_bm25_hits, _rrf_fuse, _tokenize_for_bm25


class HybridSearchTest(unittest.TestCase):
    def test_tokenizer_keeps_professor_names_and_course_codes(self):
        tokens = _tokenize_for_bm25("Prof Dodis's CSCIGA1170 operating systems!")

        self.assertIn("prof", tokens)
        self.assertIn("dodis", tokens)
        self.assertIn("csciga1170", tokens)
        self.assertIn("operating", tokens)
        self.assertIn("systems", tokens)

    def test_bm25_ranks_keyword_matching_review_first(self):
        records = [
            {
                "id": "curve-review",
                "text": "Review: The exams have a generous curve for midterms and finals.",
                "metadata": {"source": "rmp_franke_reviews.txt", "professor": "Hubertus Franke"},
            },
            {
                "id": "unrelated-review",
                "text": "Review: The lectures are clear and the professor is responsive.",
                "metadata": {"source": "rmp_tang_reviews.txt", "professor": "Yang Tang"},
            },
            {
                "id": "another-unrelated-review",
                "text": "Review: Homework is useful and the labs are well designed.",
                "metadata": {"source": "rmp_plock_reviews.txt", "professor": "Cory Plock"},
            },
        ]

        hits = _rank_bm25_hits("which course uses a grading curve", records, k=2)

        self.assertEqual("curve-review", hits[0]["id"])
        self.assertEqual(1, hits[0]["bm25_rank"])
        self.assertGreater(hits[0]["bm25_score"], hits[1]["bm25_score"])

    def test_rrf_fuses_semantic_and_bm25_rankings(self):
        semantic_hits = [
            {"id": "semantic-first", "semantic_rank": 1, "distance": 0.2},
            {"id": "shared", "semantic_rank": 2, "distance": 0.3},
        ]
        bm25_hits = [
            {"id": "bm25-first", "bm25_rank": 1, "bm25_score": 4.0},
            {"id": "shared", "bm25_rank": 2, "bm25_score": 3.0},
        ]

        fused = _rrf_fuse(semantic_hits, bm25_hits, k=3)

        self.assertEqual("shared", fused[0]["id"])
        self.assertEqual(2, fused[0]["semantic_rank"])
        self.assertEqual(2, fused[0]["bm25_rank"])
        self.assertGreater(fused[0]["rrf_score"], fused[1]["rrf_score"])
        self.assertEqual("hybrid", fused[0]["search_mode"])


if __name__ == "__main__":
    unittest.main()
