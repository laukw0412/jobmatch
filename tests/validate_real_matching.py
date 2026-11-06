"""Prepare a private scenario offline, then execute one explicitly authorized run."""

import argparse
from collections import Counter
from contextlib import ExitStack
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from jobmatch.document.context import DOCUMENTS_DIR


OUTPUT_ROOT = DOCUMENTS_DIR.parent / "test_outputs" / "scenario_validation"
CORE_NAMES = ["KA WANG LAU Resume (EN).pdf", "職務経歴書_劉嘉泓.pdf"]
SUPPLEMENT_NAMES = ["外国語（英語）試験成績証明書.pdf", "N1 unofficial.png"]
MODEL = "gpt-4.1-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_OUTPUT_TOKENS = 4096
MAX_CALLS = 9
MAX_COST_USD = 0.10
GROUPS = {
    "masters_degree": r"master",
    "python_frameworks": r"python",
    "english": r"english",
    "japanese_language": r"japanese.*language|language.*japanese",
    "publications": r"publication|publish|conference|journal",
    "distributed_cloud_training": r"distributed|cloud",
}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def offline(stack):
    attempts = []

    def block(*args, **kwargs):
        attempts.append(1)
        raise OSError("Network disabled during preparation")

    stack.enter_context(patch.dict(os.environ, {
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1",
    }))
    for name in ("connect", "connect_ex", "sendto"):
        stack.enter_context(patch.object(socket.socket, name, block))
    for name in ("create_connection", "getaddrinfo"):
        stack.enter_context(patch.object(socket, name, block))
    return attempts


def prepare():
    run_dir = OUTPUT_ROOT / datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    with (run_dir / "prepare.log").open("w", encoding="utf-8") as log, ExitStack() as stack:
        stack.enter_context(redirect_stdout(log))
        stack.enter_context(redirect_stderr(log))
        attempts = offline(stack)
        import pymupdf
        from jobmatch.document.context import load_core_documents
        from jobmatch.document.extraction import extract_pdf
        from jobmatch.rag.chunking import chunk_document

        jd_path = DOCUMENTS_DIR.parent / "test_extracted_job.txt"
        jd = jd_path.read_text(encoding="utf-8")
        cores = load_core_documents([DOCUMENTS_DIR / name for name in CORE_NAMES])
        audits = []
        for index, core in enumerate(cores, 1):
            with pymupdf.open(core.source_path) as pdf:
                native = "\n".join(page.get_text() for page in pdf)
            compact = lambda text: re.sub(r"\W", "", text).casefold()
            numbers = lambda text: set(re.findall(r"\d+(?:[./:-]\d+)*", text))
            audits.append({
                "source_file": core.source_file,
                "parsed_chars": len(core.text),
                "normalized_character_multiset_equal": Counter(compact(native)) == Counter(compact(core.text)),
                "missing_native_numbers": sorted(numbers(native) - numbers(core.text)),
                "missing_native_words_after_format_normalization": [
                    word for word in set(re.findall(r"\w+", native.casefold()))
                    if len(word) > 1 and word not in compact(core.text)
                ],
            })
            (run_dir / f"core_{index}.md").write_text(core.text, encoding="utf-8")

        chunks = []
        supplementary = []
        for name in SUPPLEMENT_NAMES:
            path = (DOCUMENTS_DIR / name).resolve()
            document_chunks = chunk_document(path)
            if not document_chunks:
                raise ValueError("Selected supplementary document produced no chunks")
            for chunk in document_chunks:
                chunks.append({**chunk, "source_path": str(path)})
            item = {"source_file": name, "chunks": len(document_chunks), "characters": sum(len(c["text"]) for c in document_chunks)}
            if path.suffix == ".pdf":
                with pymupdf.open(path) as pdf:
                    native = "\n".join(page.get_text() for page in pdf)
                parsed = extract_pdf(path).text
                all_chunks = "\n".join(c["text"] for c in document_chunks)
                # compare the previously documented score case without printing values
                score_values = ["99", "24", "29", "23"]
                has_value = lambda text, value: bool(re.search(r"(?<!\d)" + value + r"(?!\d)", text))
                item["historical_score_values_in_native"] = all(has_value(native, value) for value in score_values)
                item["historical_score_values_in_parsed"] = all(has_value(parsed, value) for value in score_values)
                item["historical_score_values_in_chunks"] = all(has_value(all_chunks, value) for value in score_values)
                (run_dir / "english_certificate_native.txt").write_text(native, encoding="utf-8")
            supplementary.append(item)

        sources = [DOCUMENTS_DIR / name for name in CORE_NAMES + SUPPLEMENT_NAMES] + [jd_path]
        prepared = {
            "jd_text": jd, "core_documents": [core.model_dump() for core in cores],
            "chunks": chunks, "source_hashes": {str(path.resolve()): digest(path) for path in sources},
        }
        write_json(run_dir / "prepared.json", prepared)
        write_json(run_dir / "core_audit.json", audits)
        raw_input = jd + "\n".join(core.text for core in cores) + "\n".join(chunk["text"] for chunk in chunks)
        plan = {
            "run_dir": str(run_dir), "model": MODEL, "embedding_model": EMBEDDING_MODEL,
            "prepared_sha256": digest(run_dir / "prepared.json"),
            "jd_chars": len(jd), "core_chars": sum(len(core.text) for core in cores),
            "supplementary": supplementary, "max_chunk_chars": max(len(chunk["text"]) for chunk in chunks),
            "requirement_groups": list(GROUPS), "top_k": 2,
            "max_api_calls": MAX_CALLS, "max_output_tokens_per_chat": MAX_OUTPUT_TOKENS,
            "conservative_cost_limit_usd": MAX_COST_USD,
            "email_occurrences_in_prepared_text": len(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", raw_input)),
            "redaction_applied": False, "blocked_network_attempts": len(attempts),
            "core_audits": [{key: value for key, value in item.items() if not key.startswith("missing_")} for item in audits],
            "limitations": [
                "Character comparisons do not establish semantic correctness or current qualification status.",
                "Certificate score presence is a lexical check, not verified label/value association.",
                "Matching transmits selected core text and retrieved chunks, potentially including personal identity fields.",
                "Preparation is offline; no live API or production Chroma access has occurred.",
            ],
        }
        write_json(run_dir / "plan.json", plan)
    print(json.dumps(plan, ensure_ascii=True, indent=2))


class BudgetedClient:
    """Use real OpenAI responses with bounded calls, output, and conservative cost."""

    def __init__(self, run_dir, prior_calls=None):
        from dotenv import load_dotenv
        import httpx
        from openai import OpenAI

        load_dotenv()
        self.client = OpenAI(
            base_url="https://api.openai.com/v1", max_retries=0, timeout=60,
            http_client=httpx.Client(trust_env=False),
        )
        self.run_dir = run_dir
        self.calls = list(prior_calls or [])
        self.reserved_cost = sum(item["reserved_cost_usd"] for item in self.calls)
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=self.parse))
        self.embeddings = SimpleNamespace(create=self.embed)

    def reserve(self, kind, text, output_tokens=0):
        # UTF-8 bytes deliberately overestimate BPE tokens for this bounded pilot
        byte_bound = len(text.encode("utf-8")) + (2048 if kind == "chat" else 256)
        upper_cost = (byte_bound * (0.40 if kind == "chat" else 0.02) + output_tokens * 1.60) / 1_000_000
        if len(self.calls) >= MAX_CALLS or self.reserved_cost + upper_cost > MAX_COST_USD:
            raise ValueError("Scenario call/cost limit would be exceeded")
        self.reserved_cost += upper_cost
        record = {"kind": kind, "reserved_cost_usd": upper_cost, "status": "started"}
        self.calls.append(record)
        write_json(self.run_dir / "api_usage.json", self.calls)
        return record

    def parse(self, **kwargs):
        kwargs.update(max_completion_tokens=MAX_OUTPUT_TOKENS, store=False)
        text = json.dumps(kwargs["messages"], ensure_ascii=False) + json.dumps(kwargs["response_format"].model_json_schema())
        record = self.reserve("chat", text, MAX_OUTPUT_TOKENS)
        response = self.client.chat.completions.parse(**kwargs)
        record.update(status="success", usage=response.usage.model_dump() if response.usage else None)
        parsed = response.choices[0].message.parsed
        if parsed is not None:
            write_json(self.run_dir / f"chat_response_{len(self.calls)}.json", parsed.model_dump())
        write_json(self.run_dir / "api_usage.json", self.calls)
        return response

    def embed(self, **kwargs):
        record = self.reserve("embedding", json.dumps(kwargs["input"], ensure_ascii=False))
        response = self.client.embeddings.create(**kwargs)
        record.update(status="success", usage=response.usage.model_dump())
        write_json(self.run_dir / "api_usage.json", self.calls)
        return response


def read_prepared(run_dir):
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(OUTPUT_ROOT.resolve()):
        raise ValueError("Scenario directory must stay inside the ignored output root")
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    if digest(run_dir / "prepared.json") != plan["prepared_sha256"]:
        raise ValueError("Prepared input changed after review; prepare and review again")
    prepared = json.loads((run_dir / "prepared.json").read_text(encoding="utf-8"))
    for source, expected in prepared["source_hashes"].items():
        if digest(Path(source)) != expected:
            raise ValueError("A selected source changed; prepare and review again")
    return prepared


def inspect_resume(run_dir):
    """Validate cached artifacts locally before any continuation is authorized."""
    from jobmatch.jobs.models import JobDescription
    from jobmatch.rag.storage import create_chroma_client

    run_dir = run_dir.resolve()
    prepared = read_prepared(run_dir)
    if (run_dir / "matching_result.json").exists() or not (run_dir / "run_error.json").is_file():
        raise ValueError("Continuation requires the original failed, incomplete attempt")
    calls = json.loads((run_dir / "api_usage.json").read_text(encoding="utf-8"))
    if len(calls) != 2 or [item["kind"] for item in calls] != ["embedding", "chat"] or any(item["status"] != "success" for item in calls):
        raise ValueError("Only the verified two-request stopping point can be resumed")
    if not (run_dir / "chroma" / "chroma.sqlite3").is_file():
        raise ValueError("Cached isolated database is missing; do not recreate it")
    with create_chroma_client(path=str(run_dir / "chroma")) as database:
        collection = database.get_collection("jobmatch_scenario")
        cached = collection.get(include=["documents", "metadatas"])
        actual = {
            item_id: (text, metadata["source_path"], metadata["chunk_index"])
            for item_id, text, metadata in zip(cached["ids"], cached["documents"], cached["metadatas"], strict=True)
        }
        expected = {
            f"scenario:{index}": (item["text"], item["source_path"], item["chunk_index"])
            for index, item in enumerate(prepared["chunks"])
        }
        if actual != expected:
            raise ValueError("Cached collection does not match the reviewed supplementary sources")
    selected = JobDescription.model_validate_json((run_dir / "selected_job.json").read_text(encoding="utf-8"))
    if len(selected.requirements) != len(GROUPS):
        raise ValueError("Cached requirement count changed")
    extracted = JobDescription.model_validate_json((run_dir / "chat_response_2.json").read_text(encoding="utf-8"))
    for requirement, expression in zip(selected.requirements, GROUPS.values(), strict=True):
        candidates = [item for item in extracted.requirements if re.search(expression, item.description, re.I)]
        if candidates != [requirement]:
            raise ValueError("Cached requirement selection differs from the successful extraction")
    return {
        "cached_chunks": len(expected), "cached_requirements": len(selected.requirements),
        "new_api_calls": 7, "reused_successful_requests": 2,
        "new_document_embedding_requests": 0, "new_jd_extraction_requests": 0,
        "conservative_remaining_budget_usd": MAX_COST_USD - sum(item["reserved_cost_usd"] for item in calls),
    }


def run(run_dir, resume=False):
    run_dir = run_dir.resolve()
    prepared = read_prepared(run_dir)
    prior_calls = []
    if resume:
        inspect_resume(run_dir)
        prior_calls = json.loads((run_dir / "api_usage.json").read_text(encoding="utf-8"))
        output_dir = run_dir / "continuation"
        # a new directory preserves the failed attempt and prevents repeated paid resumes
        output_dir.mkdir(exist_ok=False)
    else:
        output_dir = run_dir
    # prevent silently repeating a paid run, including after a partial failure
    with (output_dir / "run_started.txt").open("x", encoding="utf-8") as marker:
        marker.write("Single authorized scenario run started\n")

    with (output_dir / "run.log").open("w", encoding="utf-8") as log, ExitStack() as stack:
        stack.enter_context(redirect_stdout(log))
        stack.enter_context(redirect_stderr(log))
        from jobmatch.document.models import CoreDocument
        from jobmatch.jobs import extractor
        from jobmatch.jobs.models import JobDescription
        from jobmatch.matching import analyzer
        from jobmatch.matching.retriever import retrieve_job_requirements
        from jobmatch.rag import retrieval
        from jobmatch.rag.storage import create_chroma_client

        client = BudgetedClient(output_dir, prior_calls=prior_calls)
        stack.callback(client.client.close)
        for module in (extractor, analyzer, retrieval):
            stack.enter_context(patch.object(module, "OpenAI", return_value=client))
        chunks = prepared["chunks"]
        chroma_path = str(run_dir / "chroma")
        collection_name = "jobmatch_scenario"
        database = create_chroma_client(path=chroma_path)
        stack.callback(database.close)
        if resume:
            selected_job = JobDescription.model_validate_json((run_dir / "selected_job.json").read_text(encoding="utf-8"))
        else:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=[item["text"] for item in chunks])
            collection = database.create_collection(collection_name, embedding_function=None)
            collection.add(
                ids=[f"scenario:{index}" for index in range(len(chunks))],
                embeddings=[item.embedding for item in response.data],
                documents=[item["text"] for item in chunks],
                metadatas=[{key: item[key] for key in ("source_file", "source_path", "chunk_index", "method")} for item in chunks],
            )
            job = extractor.extract_job_description(prepared["jd_text"], model=MODEL)
            selected = []
            for group, expression in GROUPS.items():
                candidates = [item for item in job.requirements if re.search(expression, item.description, re.I)]
                if len(candidates) != 1:
                    raise ValueError(f"Requirement group {group} did not resolve uniquely; no guessing permitted")
                selected.append(candidates[0])
            selected_job = job.model_copy(update={"requirements": selected})
            write_json(output_dir / "selected_job.json", selected_job.model_dump())
        core_documents = [CoreDocument.model_validate(item) for item in prepared["core_documents"]]
        evidence = retrieve_job_requirements(
            selected_job, top_k=2, strategy="source", chroma_path=chroma_path,
            collection_name=collection_name,
            included_source_paths={item["source_path"] for item in chunks},
            excluded_source_paths={item.source_path for item in core_documents},
        )
        write_json(output_dir / "retrieved_evidence.json", evidence)
        result = analyzer.analyze_matches(
            evidence, model=MODEL, core_documents=core_documents, confirmed_jd_text=prepared["jd_text"],
        )
        write_json(output_dir / "matching_result.json", result.model_dump())
        summary = {
            "status": "completed", "requirements_evaluated": len(result.matches),
            "status_counts": dict(Counter(item.status for item in result.matches)),
            "citation_source_counts": dict(Counter(citation.source_type for item in result.matches for citation in item.supporting_evidence)),
            "validation_warnings": result.validation_warnings,
            "api_calls": len(client.calls), "reserved_cost_bound_usd": client.reserved_cost,
            "api_calls_this_attempt": len(client.calls) - len(prior_calls),
            "reused_successful_requests": len(prior_calls),
        }
        write_json(output_dir / "run_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "inspect-resume", "run", "resume"])
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.run_dir is None:
        parser.error("run requires --run-dir and prior informed user authorization")
    else:
        try:
            if args.mode == "inspect-resume":
                with ExitStack() as stack:
                    attempts = offline(stack)
                    summary = inspect_resume(args.run_dir)
                    summary["blocked_network_attempts"] = len(attempts)
                write_json(args.run_dir / "resume_plan.json", summary)
                print(json.dumps(summary, indent=2))
            else:
                run(args.run_dir, resume=args.mode == "resume")
        except Exception as exc:
            if args.run_dir.resolve().is_relative_to(OUTPUT_ROOT.resolve()) and args.run_dir.is_dir():
                error_dir = args.run_dir / "continuation" if args.mode == "resume" else args.run_dir
                if error_dir.is_dir():
                    error_path = error_dir / ("inspect_error.json" if args.mode == "inspect-resume" else "run_error.json")
                    if not error_path.exists():
                        write_json(error_path, {"type": type(exc).__name__, "message": str(exc)})
            print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "details": "Private run_error.json; no automatic retry"}))
            raise SystemExit(1)
