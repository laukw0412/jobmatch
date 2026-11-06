"""Inspect selected PDFs locally without exposing their text to the terminal."""

import argparse
from contextlib import ExitStack
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from datetime import datetime
import json
import os
from pathlib import Path
import re
import socket
from unittest.mock import patch

import pymupdf

from jobmatch.document.context import DOCUMENTS_DIR
from jobmatch.document.context import load_core_documents


def normalized_words(text: str) -> set[str]:
    return {word.casefold() for word in re.findall(r"\w+", text) if len(word) > 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", nargs="+", required=True)
    args = parser.parse_args()

    # validate every input before creating outputs or reading document contents
    paths = list(dict.fromkeys(Path(value).resolve() for value in args.core))
    for path in paths:
        if not path.is_relative_to(DOCUMENTS_DIR.resolve()) or path.suffix.lower() != ".pdf" or not path.is_file():
            raise ValueError("Select existing PDFs inside data/documents/.")

    output_root = DOCUMENTS_DIR.parent / "test_outputs" / "core_validation"
    output_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir.mkdir(parents=True, exist_ok=False)
    report = {"network_policy": "blocked", "documents": []}
    network_attempts = []

    def block_network(*args, **kwargs):
        network_attempts.append("blocked")
        raise OSError("Network access is disabled for local document validation.")

    with (output_dir / "parser.log").open("w", encoding="utf-8") as log, ExitStack() as stack:
        stack.enter_context(redirect_stdout(log))
        stack.enter_context(redirect_stderr(log))
        stack.enter_context(patch.dict(os.environ, {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
        }))
        stack.enter_context(patch.object(socket.socket, "connect", block_network))
        stack.enter_context(patch.object(socket.socket, "connect_ex", block_network))
        stack.enter_context(patch.object(socket.socket, "sendto", block_network))
        stack.enter_context(patch.object(socket, "create_connection", block_network))
        stack.enter_context(patch.object(socket, "getaddrinfo", block_network))

        for index, path in enumerate(paths, start=1):
            item = {"source_file": path.name, "source_path": str(path), "status": "failed"}
            report["documents"].append(item)
            try:
                with pymupdf.open(path) as pdf:
                    pages = [page.get_text() for page in pdf]
                native = "\n".join(pages)
                (output_dir / f"{index}_native.txt").write_text(native, encoding="utf-8")
                core = load_core_documents([path])[0]
                (output_dir / f"{index}_parsed.md").write_text(core.text, encoding="utf-8")

                native_words = normalized_words(native)
                parsed_words = normalized_words(core.text)
                missing_words = sorted(native_words - parsed_words)
                compact_parsed = re.sub(r"\W", "", core.text).casefold()
                compact_native = re.sub(r"\W", "", native).casefold()
                native_numbers = set(re.findall(r"\d+(?:[./:-]\d+)*", native))
                parsed_numbers = set(re.findall(r"\d+(?:[./:-]\d+)*", core.text))
                missing_numbers = sorted(native_numbers - parsed_numbers)
                item.update(
                    status="parsed",
                    pages=len(pages),
                    native_empty_pages=sum(not page.strip() for page in pages),
                    native_chars=len(native),
                    parsed_chars=len(core.text),
                    native_word_coverage=round(len(native_words & parsed_words) / len(native_words), 4) if native_words else None,
                    missing_native_word_count=len(missing_words),
                    missing_native_number_count=len(missing_numbers),
                    remaining_word_differences_after_format_normalization=sum(word not in compact_parsed for word in missing_words),
                    native_word_characters=len(compact_native),
                    parsed_word_characters=len(compact_parsed),
                    missing_native_words=missing_words,
                    missing_native_numbers=missing_numbers,
                )
            except Exception as exc:
                # keep potentially sensitive error details in the ignored report only
                item["error"] = str(exc)
                item["error_type"] = type(exc).__name__

    report["blocked_network_attempts"] = len(network_attempts)
    report["limitations"] = [
        "Native text is a comparison baseline, not authoritative ground truth.",
        "Word/number differences can reflect formatting rather than factual loss.",
        "No semantic matching, RAG, OCR accuracy, or live provider behavior was verified.",
        "Inspect the private parser log to identify Docling versus fallback behavior.",
    ]
    (output_dir / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    safe_keys = {"source_file", "status", "pages", "native_empty_pages", "native_chars", "parsed_chars", "native_word_coverage", "missing_native_word_count", "missing_native_number_count", "remaining_word_differences_after_format_normalization", "native_word_characters", "parsed_word_characters", "error_type"}
    print(json.dumps({
        "output_dir": str(output_dir),
        "blocked_network_attempts": len(network_attempts),
        "documents": [{key: value for key, value in item.items() if key in safe_keys} for item in report["documents"]],
    }, ensure_ascii=True, indent=2))
    if any(item["status"] != "parsed" for item in report["documents"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
