"""Offline checks for explicit Python/framework excerpt coverage."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jobmatch.document.models import CoreDocument
from jobmatch.matching import analyzer


REQUIREMENT = "Proficiency in Python and deep learning frameworks such as PyTorch or TensorFlow"


class CitationCoverageTests(unittest.TestCase):
    def analyze(self, quotes, requirement=REQUIREMENT, status="matched"):
        document = CoreDocument(
            source_file="synthetic.txt", source_path="synthetic/synthetic.txt",
            text="Python development.\nPyTorch training.\nTensorFlow evaluation.",
        )
        parsed = analyzer._MatchingAssessment.model_validate({
            "matches": [{
                "requirement_id": 1, "status": status, "reason": "Synthetic assessment",
                "supporting_evidence": [
                    {"evidence_id": "core:1", "start_line": document.text.splitlines().index(quote) + 1, "end_line": document.text.splitlines().index(quote) + 1}
                    for quote in quotes
                ],
            }],
            "overall_summary": "Synthetic only", "application_recommendation": "Review evidence",
        })
        with patch.object(analyzer, "load_dotenv"), patch.object(analyzer, "OpenAI") as client:
            client.return_value.chat.completions.parse.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))],
            )
            return analyzer.analyze_matches(
                [{"requirement_id": 1, "requirement": requirement, "evidence": []}],
                core_documents=[document],
            )

    def test_noncontiguous_quotes_from_same_source_cover_both_conditions(self):
        result = self.analyze(["Python development.", "PyTorch training."])
        self.assertEqual(result.matches[0].status, "matched")
        self.assertEqual(len(result.matches[0].supporting_evidence), 2)
        self.assertEqual(result.validation_warnings, [])

    def test_framework_only_quote_warns_even_when_full_source_contains_python(self):
        result = self.analyze(["PyTorch training."])
        self.assertEqual(result.matches[0].status, "matched")
        self.assertTrue(any("Python" in warning for warning in result.validation_warnings))
        self.assertEqual(len(result.validation_warnings), 1)

    def test_python_only_quote_warns_about_framework(self):
        result = self.analyze(["Python development."])
        self.assertTrue(any("framework" in warning for warning in result.validation_warnings))

    def test_one_or_alternative_is_sufficient_for_excerpt_check(self):
        result = self.analyze(["Python development.", "TensorFlow evaluation."])
        self.assertEqual(result.validation_warnings, [])

    def test_top_level_or_is_not_misread_as_and(self):
        result = self.analyze(["PyTorch training."], requirement="Experience with Python or PyTorch")
        self.assertEqual(result.validation_warnings, [])

    def test_partial_does_not_require_excerpts_for_unverified_conditions(self):
        result = self.analyze(["PyTorch training."], status="partial")
        self.assertEqual(result.matches[0].status, "partial")
        self.assertEqual(result.validation_warnings, [])


if __name__ == "__main__":
    unittest.main()
