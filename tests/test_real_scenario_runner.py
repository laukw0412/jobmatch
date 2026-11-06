"""Exercise the paid-run controls without cloud requests or personal files."""

import hashlib
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from jobmatch.rag.storage import create_chroma_client

import validate_real_matching as scenario


class ScenarioRunnerTests(unittest.TestCase):
    def test_budget_rejects_excess_calls_and_cost_before_sending(self):
        with TemporaryDirectory() as directory, patch("dotenv.load_dotenv"), patch("openai.OpenAI"):
            client = scenario.BudgetedClient(Path(directory))
            try:
                with self.assertRaisesRegex(ValueError, "limit"):
                    client.reserve("chat", "x" * 1_000_000, 4096)
                self.assertEqual(client.calls, [])
                client.calls = [{}] * scenario.MAX_CALLS
                with self.assertRaisesRegex(ValueError, "limit"):
                    client.reserve("embedding", "small input")
            finally:
                client.client.close()

    def test_complete_synthetic_run_and_repeat_protection(self):
        self.exercise_synthetic_run(resume=False)

    def test_resume_reuses_paid_artifacts_and_preserves_failure(self):
        self.exercise_synthetic_run(resume=True)

    def exercise_synthetic_run(self, resume):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            run_dir.mkdir()
            source = root / "synthetic.txt"
            source.write_text("Synthetic source", encoding="utf-8")
            prepared = {
                "jd_text": "Synthetic job description",
                "core_documents": [{"source_file": "resume.txt", "source_path": str(source), "text": "Master degree. Python experience."}],
                "chunks": [
                    {"text": "English communication certificate.", "source_file": "english.txt", "source_path": str(root / "english.txt"), "chunk_index": 0, "method": "synthetic"},
                    {"text": "Japanese language certificate.", "source_file": "japanese.txt", "source_path": str(root / "japanese.txt"), "chunk_index": 0, "method": "synthetic"},
                ],
                "source_hashes": {str(source): hashlib.sha256(source.read_bytes()).hexdigest()},
            }
            scenario.write_json(run_dir / "prepared.json", prepared)
            scenario.write_json(run_dir / "plan.json", {"prepared_sha256": scenario.digest(run_dir / "prepared.json")})
            sdk = MagicMock()

            def embeddings(**kwargs):
                return SimpleNamespace(
                    data=[SimpleNamespace(embedding=[1.0, 0.0]) for text in kwargs["input"]],
                    usage=SimpleNamespace(model_dump=lambda: {"total_tokens": 10}),
                )

            def completion(**kwargs):
                self.assertFalse(kwargs["store"])
                self.assertEqual(kwargs["max_completion_tokens"], 4096)
                if kwargs["response_format"].__name__ == "JobDescription":
                    value = {
                        "job_title": "Synthetic", "company_name": None, "location": None,
                        "requirements": [
                            {"description": text, "category": "other", "priority": "required"}
                            for text in ["Master degree", "Python", "English", "Japanese language", "Publication record", "Distributed training"]
                        ],
                    }
                else:
                    payload = json.loads(kwargs["messages"][1]["content"])
                    self.assertEqual(len(payload["requirements"]), 6)
                    self.assertEqual("".join(line["text"] for line in payload["core_documents"][0]["lines"]), "Master degree. Python experience.")
                    value = {
                        "matches": [
                            {"requirement_id": item["requirement_id"], "status": "unknown", "reason": "Synthetic boundary check", "supporting_evidence": []}
                            for item in payload["requirements"]
                        ],
                        "overall_summary": "Synthetic only", "application_recommendation": "Review evidence",
                    }
                parsed = kwargs["response_format"].model_validate(value)
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))],
                    usage=SimpleNamespace(model_dump=lambda: {"prompt_tokens": 10, "completion_tokens": 10}),
                )

            sdk.embeddings.create.side_effect = embeddings
            sdk.chat.completions.parse.side_effect = completion
            with (
                patch.object(scenario, "OUTPUT_ROOT", root),
                patch("dotenv.load_dotenv"),
                patch("openai.OpenAI", return_value=sdk) as factory,
                patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
            ):
                if resume:
                    with patch("jobmatch.matching.retriever.retrieve_job_requirements", side_effect=ValueError("Synthetic stop before retrieval")):
                        with self.assertRaisesRegex(ValueError, "Synthetic stop"):
                            scenario.run(run_dir)
                    scenario.write_json(run_dir / "run_error.json", {"type": "ValueError", "message": "Synthetic stop"})
                    cached_usage = (run_dir / "api_usage.json").read_bytes()
                    self.assertEqual(sdk.embeddings.create.call_count, 1)
                    self.assertEqual(sdk.chat.completions.parse.call_count, 1)
                    self.assertEqual(scenario.inspect_resume(run_dir)["cached_chunks"], 2)
                    scenario.run(run_dir, resume=True)
                    self.assertEqual((run_dir / "api_usage.json").read_bytes(), cached_usage)
                    self.assertTrue((run_dir / "run_error.json").is_file())
                    output_dir = run_dir / "continuation"
                else:
                    scenario.run(run_dir)
                    output_dir = run_dir
                summary = json.loads((output_dir / "run_summary.json").read_text(encoding="utf-8"))
                self.assertEqual(summary["api_calls"], 9)
                self.assertEqual(summary["requirements_evaluated"], 6)
                self.assertEqual(summary["status_counts"], {"unknown": 6})
                self.assertEqual(summary["api_calls_this_attempt"], 7 if resume else 9)
                self.assertEqual(summary["reused_successful_requests"], 2 if resume else 0)
                self.assertLess(summary["reserved_cost_bound_usd"], 0.10)
                self.assertEqual(factory.call_args.kwargs["base_url"], "https://api.openai.com/v1")
                self.assertEqual(factory.call_args.kwargs["max_retries"], 0)
                with create_chroma_client(path=str(run_dir / "chroma")) as database:
                    self.assertEqual(database.get_collection("jobmatch_scenario").count(), 2)
                with self.assertRaises(FileExistsError):
                    scenario.run(run_dir, resume=resume)
                self.assertEqual(sdk.chat.completions.parse.call_count, 2)
                self.assertEqual(sdk.embeddings.create.call_count, 7)


if __name__ == "__main__":
    unittest.main()
