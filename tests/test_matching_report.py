"""Integrated offline checks for source ranges, local failures, and safe reports."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jobmatch.document.models import CoreDocument
from jobmatch.matching import analyzer
from jobmatch.matching.report import render_matching_report
from jobmatch.matching.report import write_matching_report


class MatchingReportTests(unittest.TestCase):
    def test_partial_failure_preserves_other_results_and_exact_source_text(self):
        core = CoreDocument(source_file="synthetic.txt", source_path="synthetic/synthetic.txt", text="Heading\r\nPython を使用。\r\n\r\nPyTorch training.\r\n")
        requirements = [
            {"requirement_id": 1, "requirement": "Python and PyTorch or TensorFlow", "evidence": []},
            {"requirement_id": 2, "requirement": "English", "evidence": [{"source_file": "certificate.txt", "source_path": "synthetic/certificate.txt", "text": "English communication.\n"}]},
            {"requirement_id": 3, "requirement": "Experience", "evidence": []},
            {"requirement_id": 4, "requirement": "Qualification", "evidence": []},
        ]
        sources, payload = analyzer.prepare_matching_input(requirements, [core], "Confirmed synthetic JD")
        self.assertEqual("".join(line["text"] for line in payload["core_documents"][0]["lines"]), core.text)
        parsed = analyzer._MatchingAssessment.model_validate({
            "matches": [
                {"requirement_id": 1, "status": "matched", "reason": "Synthetic", "supporting_evidence": [
                    {"evidence_id": "core:1", "start_line": 2, "end_line": 2},
                    {"evidence_id": "core:1", "start_line": 4, "end_line": 4},
                ]},
                {"requirement_id": 2, "status": "matched", "reason": "Synthetic", "supporting_evidence": [{"evidence_id": "rag:2:1", "start_line": 1, "end_line": 1}]},
                {"requirement_id": 3, "status": "matched", "reason": "UNSAFE_MODEL_REASON", "supporting_evidence": [
                    {"evidence_id": "core:1", "start_line": 2, "end_line": 2},
                    {"evidence_id": "core:1", "start_line": 99, "end_line": 100},
                    {"evidence_id": "core:1", "start_line": 3, "end_line": 3},
                    {"evidence_id": "core:99", "start_line": 1, "end_line": 1},
                    {"evidence_id": "rag:2:1", "start_line": 1, "end_line": 1},
                ]},
                {"requirement_id": 4, "status": "missing", "reason": "UNSAFE_MODEL_REASON", "supporting_evidence": []},
            ],
            "overall_summary": "UNSAFE_SUMMARY", "strengths": ["UNSAFE_STRENGTH"],
            "gaps": ["UNSAFE_GAP"], "application_recommendation": "UNSAFE_RECOMMENDATION",
        })
        result = analyzer.resolve_matching_result(parsed, requirements, sources)
        self.assertEqual([item.status for item in result.matches], ["matched", "matched", "unknown", "unknown"])
        self.assertEqual([item.review_required for item in result.matches], [False, False, True, True])
        self.assertEqual(result.matches[0].supporting_evidence[0].quote, "Python を使用。\r\n")
        self.assertEqual(result.matches[2].model_status, "matched")
        self.assertEqual(len(result.matches[2].supporting_evidence), 1)
        self.assertEqual({item.code for item in result.matches[2].citation_issues}, {"invalid_range", "empty_range", "unknown_source", "wrong_requirement"})
        self.assertEqual(result.matches[3].citation_issues[0].code, "missing_citations")
        self.assertEqual(result.strengths, [])
        self.assertEqual(result.gaps, [])
        report = render_matching_report(result)
        self.assertNotIn("UNSAFE_", report)
        self.assertIn("Python を使用。\r\n", report)
        self.assertIn("certificate.txt", report)
        self.assertIn("unknown", report)
        self.assertTrue(result.summary_review_required)
        with TemporaryDirectory() as directory:
            path = write_matching_report(result, Path(directory) / "report.md")
            self.assertEqual(path.read_bytes().decode("utf-8"), report)
            with self.assertRaises(FileExistsError):
                write_matching_report(result, path)

    def test_valid_result_preserves_summary_and_model_schema_has_no_quote(self):
        requirements = [{"requirement_id": 1, "requirement": "Python", "evidence": []}]
        core = CoreDocument(source_file="synthetic.txt", source_path="synthetic/synthetic.txt", text="Python experience.")
        sources, _ = analyzer.prepare_matching_input(requirements, [core])
        parsed = analyzer._MatchingAssessment.model_validate({
            "matches": [{"requirement_id": 1, "status": "matched", "reason": "Synthetic", "supporting_evidence": [{"evidence_id": "core:1", "start_line": 1, "end_line": 1}]}],
            "overall_summary": "Original summary", "strengths": ["Original strength"],
            "gaps": [], "application_recommendation": "Original recommendation",
        })
        result = analyzer.resolve_matching_result(parsed, requirements, sources)
        self.assertFalse(result.summary_review_required)
        self.assertIn("Original summary", render_matching_report(result))
        self.assertEqual(result.strengths, ["Original strength"])
        fields = analyzer._MatchingAssessment.model_json_schema()["$defs"]["EvidenceReference"]["properties"]
        self.assertEqual(set(fields), {"evidence_id", "start_line", "end_line"})


if __name__ == "__main__":
    unittest.main()
