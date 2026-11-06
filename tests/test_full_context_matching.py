"""Offline checks using synthetic text and mocked cloud/database boundaries."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from jobmatch.document import context
from jobmatch.document.models import CoreDocument
from jobmatch.jobs.models import JobDescription
from jobmatch.jobs.models import JobRequirement
from jobmatch.matching import analyzer
from jobmatch.matching import retriever
from jobmatch.matching import workflow
from jobmatch.rag import retrieval


def requirements():
    return [
        {
            "requirement_id": 1,
            "requirement": "Python and English",
            "category": "technical_skill",
            "priority": "required",
            "evidence": [{
                "source_file": "certificate.txt",
                "source_path": "synthetic/certificate.txt",
                "chunk_index": 2,
                "text": "English level B2.",
            }],
        },
        {
            "requirement_id": 2,
            "requirement": "Professional cloud deployment experience",
            "category": "experience",
            "priority": "preferred",
            "evidence": [],
        },
    ]


def assessment(first_citations=None, first_status="matched"):
    return {
        "matches": [
            {
                "requirement_id": 1,
                "status": first_status,
                "reason": "Synthetic assessment.",
                "supporting_evidence": first_citations or [],
            },
            {"requirement_id": 2, "status": "unknown", "reason": "No direct evidence.", "supporting_evidence": []},
        ],
        "overall_summary": "Synthetic summary.",
        "strengths": [],
        "gaps": [],
        "application_recommendation": "Review uncertain requirements.",
    }


def parsed_response(response_data):
    def respond(**kwargs):
        parsed = kwargs["response_format"].model_validate(response_data)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))])

    return respond


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.client_patch = patch.object(analyzer, "OpenAI")
        self.client = self.client_patch.start().return_value
        self.addCleanup(self.client_patch.stop)
        self.env_patch = patch.object(analyzer, "load_dotenv")
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.core = CoreDocument(
            source_file="resume.txt",
            source_path="synthetic/resume.txt",
            text="Synthetic resume\nPython development.\nAcademic research only.",
        )

    def analyze(self, response_data, **kwargs):
        self.client.chat.completions.parse.side_effect = parsed_response(response_data)
        return analyzer.analyze_matches(requirements(), core_documents=[self.core], **kwargs)

    def test_combined_input_and_self_contained_sources(self):
        citations = [
            {"evidence_id": "core:1", "start_line": 2, "end_line": 2},
            {"evidence_id": "rag:1:1", "start_line": 1, "end_line": 1},
        ]
        result = self.analyze(assessment(citations), confirmed_jd_text="Confirmed synthetic JD.")
        payload = json.loads(self.client.chat.completions.parse.call_args.kwargs["messages"][1]["content"])
        self.assertEqual(payload["confirmed_jd_text"], "Confirmed synthetic JD.")
        self.assertEqual("".join(line["text"] for line in payload["core_documents"][0]["lines"]), self.core.text)
        self.assertNotIn("source_path", payload["core_documents"][0])
        self.assertNotIn("source_path", payload["requirements"][0]["evidence"][0])
        self.assertEqual(payload["requirements"][0]["evidence"][0]["evidence_id"], "rag:1:1")
        match = result.matches[0]
        self.assertEqual(match.supporting_evidence_indices, [1])
        core, rag = match.supporting_evidence
        self.assertEqual((core.source_type, core.source_file, core.source_path), ("core", "resume.txt", self.core.source_path))
        self.assertEqual(core.text, self.core.text)
        self.assertEqual(core.quote, "Python development.\n")
        self.assertEqual((core.start_line, core.end_line), (2, 2))
        self.assertEqual((rag.source_type, rag.chunk_index), ("rag", 2))
        self.assertEqual(rag.text, "English level B2.")
        self.assertEqual(result.matches[1].status, "unknown")
        self.assertEqual(result.matches[1].supporting_evidence, [])
        self.assertIn("source_file", json.loads(result.model_dump_json())["matches"][0]["supporting_evidence"][0])

    def test_core_can_support_requirement_with_no_rag_results(self):
        response = assessment()
        response["matches"][1].update(
            status="partial",
            supporting_evidence=[{"evidence_id": "core:1", "start_line": 3, "end_line": 3}],
        )
        result = self.analyze(response)
        self.assertEqual(result.matches[1].status, "partial")
        self.assertEqual(result.matches[1].supporting_evidence_indices, [])
        self.assertEqual(result.matches[1].supporting_evidence[0].source_type, "core")

    def test_invalid_or_cross_requirement_ids_are_rejected(self):
        for evidence_id in ("core:99", "rag:2:1", "1"):
            with self.subTest(evidence_id=evidence_id):
                result = self.analyze(assessment([{"evidence_id": evidence_id, "start_line": 1, "end_line": 1}]))
                self.assertEqual(result.matches[0].status, "unknown")
                self.assertTrue(result.matches[0].review_required)
                self.assertFalse(result.matches[1].review_required)
        response = assessment()
        response["matches"][1]["supporting_evidence"] = [{"evidence_id": "rag:1:1", "start_line": 1, "end_line": 1}]
        result = self.analyze(response)
        self.assertEqual(result.matches[1].citation_issues[0].code, "wrong_requirement")

    def test_invalid_ranges_are_reported_without_aborting(self):
        for start, end in ((0, 1), (3, 2), (1, 99), (-1, 1)):
            with self.subTest(start=start, end=end):
                result = self.analyze(assessment([{"evidence_id": "core:1", "start_line": start, "end_line": end}]))
                self.assertEqual(result.matches[0].citation_issues[0].code, "invalid_range")
                self.assertTrue(result.summary_review_required)

    def test_uncited_decisions_become_unknown(self):
        for status in ("matched", "partial", "missing"):
            with self.subTest(status=status):
                result = self.analyze(assessment(first_status=status))
                self.assertEqual(result.matches[0].status, "unknown")
                self.assertEqual(result.matches[0].supporting_evidence, [])
                self.assertEqual(len(result.validation_warnings), 1)

    def test_missing_with_counterevidence_is_preserved(self):
        result = self.analyze(assessment([{"evidence_id": "core:1", "start_line": 3, "end_line": 3}], "missing"))
        self.assertEqual(result.matches[0].status, "missing")

    def test_unknown_clears_citations_and_duplicates_are_removed(self):
        citation = {"evidence_id": "core:1", "start_line": 2, "end_line": 2}
        result = self.analyze(assessment([citation, citation]))
        self.assertEqual(len(result.matches[0].supporting_evidence), 1)
        result = self.analyze(assessment([citation], "unknown"))
        self.assertEqual(result.matches[0].supporting_evidence, [])
        self.assertEqual(result.matches[0].supporting_evidence_indices, [])

    def test_requirement_coverage_is_checked(self):
        for ids in ([1], [1, 1], [1, 3]):
            with self.subTest(ids=ids):
                response = assessment()
                response["matches"] = [dict(response["matches"][0], requirement_id=value) for value in ids]
                with self.assertRaisesRegex(ValueError, "missing or duplicate requirements"):
                    self.analyze(response)

    def test_budget_and_bad_sources_fail_before_api_call(self):
        with self.assertRaisesRegex(ValueError, "character budget"):
            self.analyze(assessment(), max_input_chars=20)
        self.client.chat.completions.parse.assert_not_called()
        bad_input = requirements()
        bad_input[0]["evidence"][0].pop("source_file")
        with self.assertRaisesRegex(ValueError, "source filename"):
            analyzer.analyze_matches(bad_input)
        self.client.chat.completions.parse.assert_not_called()

    def test_rag_only_legacy_entry_still_returns_indices(self):
        self.client.chat.completions.parse.side_effect = parsed_response(
            assessment([{"evidence_id": "rag:1:1", "start_line": 1, "end_line": 1}])
        )
        result = analyzer.analyze_matches(requirements())
        self.assertEqual(result.matches[0].supporting_evidence_indices, [1])
        self.assertEqual(result.matches[0].supporting_evidence[0].source_file, "certificate.txt")


class CoreDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(context, "DOCUMENTS_DIR", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_only_selected_files_are_read_in_full_and_deduplicated(self):
        resume = self.root / "resume.txt"
        resume.write_text("\ufeffSynthetic resume\nPython.\n", encoding="utf-8")
        career = self.root / "career.md"
        career.write_text("# Career\nSynthetic research.\n", encoding="utf-8")
        (self.root / "unselected.txt").write_bytes(b"\xff")
        documents = context.load_core_documents([resume, career, resume])
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0].text, "Synthetic resume\nPython.\n")
        self.assertEqual(documents[1].text, "# Career\nSynthetic research.\n")
        self.assertEqual(documents[0].source_path, str(resume.resolve()))

    def test_empty_selection_outside_path_missing_and_empty_files_fail(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            context.load_core_documents([])
        with self.assertRaisesRegex(ValueError, "inside data/documents"):
            context.load_core_documents([self.root.parent / "outside.txt"])
        with self.assertRaises(FileNotFoundError):
            context.load_core_documents([self.root / "missing.txt"])
        empty = self.root / "empty.txt"
        empty.write_text(" \n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no readable text"):
            context.load_core_documents([empty])

    def test_over_budget_and_unreadable_files_fail_explicitly(self):
        sample = self.root / "sample.txt"
        sample.write_text("Synthetic content", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "character budget"):
            context.load_core_documents([sample], max_chars=3)
        sample.write_bytes(b"\xff")
        with self.assertRaisesRegex(ValueError, "Could not read core document"):
            context.load_core_documents([sample])


class WorkflowAndRetrievalTests(unittest.TestCase):
    def test_workflow_combines_selected_file_jd_and_mandatory_retrieval(self):
        job = JobDescription(
            job_title="Synthetic role", company_name=None, location=None,
            requirements=[
                JobRequirement(description="Python and English", category="technical_skill", priority="required"),
                JobRequirement(description="Professional cloud deployment experience", category="experience", priority="preferred"),
            ],
        )
        response = assessment([{"evidence_id": "core:1", "start_line": 2, "end_line": 2}])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            resume = root / "resume.txt"
            resume.write_text("Synthetic resume\nPython.", encoding="utf-8")
            with (
                patch.object(context, "DOCUMENTS_DIR", root),
                patch.object(workflow, "extract_job_description", return_value=job) as extract,
                patch.object(workflow, "retrieve_job_requirements", return_value=requirements()) as retrieve,
                patch.object(analyzer, "load_dotenv"),
                patch.object(analyzer, "OpenAI") as client,
            ):
                client.return_value.chat.completions.parse.side_effect = parsed_response(response)
                report_path = root / "report.md"
                result = workflow.match_job("Confirmed synthetic JD", [resume], report_path=report_path)
                extract.assert_called_once_with("Confirmed synthetic JD", model="gpt-4.1-mini")
                retrieve.assert_called_once_with(
                    job, top_k=5, strategy="source", excluded_source_paths={str(resume.resolve())},
                    chroma_path=workflow.CHROMA_PATH, collection_name=workflow.COLLECTION_NAME,
                    included_source_paths=None,
                )
                self.assertEqual(result.matches[0].supporting_evidence[0].text, "Synthetic resume\nPython.")
                self.assertTrue(report_path.is_file())
                self.assertIn("resume.txt", report_path.read_text(encoding="utf-8"))
                with self.assertRaises(FileExistsError):
                    workflow.match_job("Confirmed synthetic JD", [resume], report_path=report_path)
                self.assertEqual(extract.call_count, 1)

    def test_missing_core_selection_stops_before_paid_steps(self):
        with patch.object(workflow, "extract_job_description") as extract, patch.object(workflow, "retrieve_job_requirements") as retrieve:
            with self.assertRaisesRegex(ValueError, "at least one"):
                workflow.match_job("Confirmed synthetic JD", [])
            extract.assert_not_called()
            retrieve.assert_not_called()

    def test_requirement_retrieval_passes_core_exclusion(self):
        job = JobDescription(job_title=None, company_name=None, location=None, requirements=[
            JobRequirement(description="English", category="language", priority="required"),
        ])
        with patch.object(retriever, "retrieve_chunks", return_value=requirements()[0]["evidence"]) as retrieve:
            result = retriever.retrieve_job_requirements(job, excluded_source_paths={"synthetic/resume.txt"})
            self.assertEqual(retrieve.call_args.kwargs["excluded_source_paths"], {"synthetic/resume.txt"})
            self.assertEqual(result[0]["evidence"][0]["source_file"], "certificate.txt")

    def test_core_exclusion_applies_in_chroma_query_before_top_k(self):
        collection = MagicMock()
        collection.count.return_value = 3
        collection.query.return_value = {
            "documents": [["English level B2."]],
            "metadatas": [[{"source_file": "certificate.txt", "source_path": "synthetic/certificate.txt", "chunk_index": 2}]],
            "distances": [[0.1]],
        }
        with (
            patch.object(retrieval, "create_chroma_client") as db,
            patch.object(retrieval, "OpenAI") as client,
            patch.object(retrieval, "load_dotenv"),
        ):
            db.return_value.__enter__.return_value = db.return_value
            db.return_value.get_collection.return_value = collection
            client.return_value.embeddings.create.return_value = SimpleNamespace(data=[SimpleNamespace(embedding=[1.0, 0.0])])
            result = retrieval.retrieve_chunks("English", top_k=2, excluded_source_paths={"synthetic/resume.txt"})
            self.assertEqual(collection.query.call_args.kwargs["where"], {"source_path": {"$nin": ["synthetic/resume.txt"]}})
            self.assertEqual(collection.query.call_args.kwargs["n_results"], 2)
            self.assertEqual(result[0]["source_file"], "certificate.txt")


if __name__ == "__main__":
    unittest.main()
