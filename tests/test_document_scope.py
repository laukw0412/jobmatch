"""Read-only JobMatch diagnostic: inventory, document scope, and deduplication."""

import argparse
import chromadb
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.reranker import rerank_chunks
from jobmatch.matching.retriever import is_duplicate
from jobmatch.rag.retrieval import retrieve_chunks


PRIMARY_RESUME = "KA WANG LAU Resume (EN).docx"
SUPPORTING_DOCUMENTS = {
    "職務経歴書_劉嘉泓.pdf",
    "履歴書_劉嘉泓.xls",
    "外国語（英語）試験成績証明書.pdf",
    "N1 unofficial.png",
    "出身大学及び出身大学院の成績証明書.pdf",
}
EXCLUDED_TEST_DOCUMENTS = {"two_column_resume_sample.docx"}

JOB_PATH = ROOT / "data" / "test_structured_job.json"
DOCUMENT_DIR = ROOT / "data" / "documents"
OUTPUT_DIR = ROOT / "data" / "diagnostics"



def get_diagnostic_collection():
    """Open the existing document collection without creating or indexing."""
    chroma_path = ROOT / "data" / "chroma"
    collection_name = "jobmatch_documents"

    if not chroma_path.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found: {chroma_path}"
        )

    client = chromadb.PersistentClient(path=str(chroma_path))
    available = [item.name for item in client.list_collections()]
    if collection_name not in available:
        raise ValueError(
            f"Collection '{collection_name}' not found. "
            f"Available collections: {available}"
        )

    return client.get_collection(name=collection_name)


def classify_document(filename: str) -> str:
    """Assign rough diagnostic groups without changing the index."""
    lower = filename.casefold()
    if filename in EXCLUDED_TEST_DOCUMENTS or "sample" in lower:
        return "sample"
    if "resume" in lower or "履歴書" in filename:
        return "resume_version"
    if "職務経歴書" in filename:
        return "career_history"
    if any(term in lower for term in ("n1", "英語", "証明書", "成績", "学生证")):
        return "certificate_or_record"
    return "other"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    """Save a local diagnostic report."""
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def inventory(collection) -> tuple[set[str], int]:
    """Inspect indexed sources and local files without modifying data."""
    local_files = sorted(
        path.name for path in DOCUMENT_DIR.iterdir() if path.is_file()
        and path.name != ".gitkeep"
    ) if DOCUMENT_DIR.exists() else []

    stored = collection.get(include=["metadatas"])
    metadata = stored.get("metadatas") or []
    source_counts = Counter()
    for item in metadata:
        item = item or {}
        name = item.get("source_file") or Path(item.get("source_path", "")).name
        source_counts[name or "<unknown>"] += 1

    rows = []
    for name in sorted(set(local_files) | set(source_counts)):
        rows.append({
            "source_file": name,
            "document_group": classify_document(name),
            "local_file_exists": name in local_files,
            "indexed_chunks": source_counts[name],
            "in_curated_scope": name == PRIMARY_RESUME or name in SUPPORTING_DOCUMENTS,
        })

    write_csv(
        OUTPUT_DIR / "01_index_inventory.csv",
        rows,
        ["source_file", "document_group", "local_file_exists",
         "indexed_chunks", "in_curated_scope"],
    )

    print("\n[Round 1] Document and ChromaDB inventory")
    print(f"Local files: {len(local_files)} | Indexed chunks: {collection.count()}")
    for row in rows:
        print(f"  {row['indexed_chunks']:>3} chunks | {row['document_group']:<22} | {row['source_file']}")

    indexed_names = set(source_counts)
    curated_names = {PRIMARY_RESUME} | SUPPORTING_DOCUMENTS
    unavailable = sorted(curated_names - indexed_names)
    if unavailable:
        print("\nWARNING: Curated files not found in the current index:")
        for name in unavailable:
            print(f"  - {name}")
    print("Curated scope is a TEST, not a judgment about newest/most authoritative versions.")
    return indexed_names, collection.count()


def choose_chunks(chunks: list[dict], names: set[str] | None) -> list[dict]:
    """Apply source filtering before selecting the retrieval candidate pool."""
    return [
        item for item in chunks
        if item.get("source_file") not in EXCLUDED_TEST_DOCUMENTS
        and (names is None or item.get("source_file") in names)
    ]


def keep_distinct(ranked: list[dict], limit: int) -> list[dict]:
    """Apply the current conservative duplicate function to ranked chunks."""
    selected = []
    for chunk in ranked:
        if len(selected) >= limit:
            break
        if not is_duplicate(chunk, selected):
            selected.append(chunk)
    return selected


def add_rows(
    rows: list[dict], requirement_id: int, requirement: str,
    approach: str, chunks: list[dict], candidate_count: int,
) -> None:
    """Record outputs for human relevance and fact-duplication labeling."""
    for rank, item in enumerate(chunks, 1):
        snippet = re.sub(r"\s+", " ", item.get("text", ""))[:500]
        rows.append({
            "requirement_id": requirement_id,
            "requirement": requirement,
            "approach": approach,
            "rank": rank,
            "candidate_pool_size": candidate_count,
            "source_file": item.get("source_file", ""),
            "chunk_index": item.get("chunk_index", ""),
            "rerank_score": f"{item.get('rerank_score', 0):.8f}",
            "text_preview": snippet,
            "human_relevance_0_1_2": "",
            "human_fact_id": "",
            "human_notes": "",
        })


def compare(job: JobDescription, index_count: int, requirement_ids: list[int], pool_size: int, top_k: int) -> None:
    """Compare full corpus, curated scope, and current deduplication."""
    curated = {PRIMARY_RESUME} | SUPPORTING_DOCUMENTS
    rows = []
    summary = []

    for requirement_id in requirement_ids:
        if not 1 <= requirement_id <= len(job.requirements):
            raise ValueError(f"Invalid requirement id: {requirement_id}")

        requirement = job.requirements[requirement_id - 1]
        query = requirement.description
        # Retrieve from the WHOLE index before filtering so curated sources
        # are not silently lost due to a full-corpus Top-15 cutoff.
        retrieved = retrieve_chunks(
            query=query,
            top_k=index_count,
            include_embeddings=True,
        )

        full = choose_chunks(retrieved, None)[:pool_size]
        scoped = choose_chunks(retrieved, curated)[:pool_size]

        # Rerank each candidate set without deduplication, isolating scope.
        full_ranked = rerank_chunks(query, full) if full else []
        scoped_ranked = rerank_chunks(query, scoped) if scoped else []

        approaches = [
            ("A_all_documents", full_ranked[:top_k], len(full)),
            ("B_curated_documents", scoped_ranked[:top_k], len(scoped)),
            ("C_curated_plus_dedup", keep_distinct(scoped_ranked, top_k), len(scoped)),
        ]

        print(f"\n[Round 2/3] R{requirement_id}: {query}")
        for name, selected, candidate_count in approaches:
            add_rows(rows, requirement_id, query, name, selected, candidate_count)
            unique_files = len({item.get("source_file") for item in selected})
            print(f"  {name}: pool={candidate_count}, selected={len(selected)}, distinct_files={unique_files}")
            for item in selected:
                print(f"    {item.get('rerank_score', 0):.6f} | {item.get('source_file', '')} | chunk {item.get('chunk_index', '')}")
            summary.append({
                "requirement_id": requirement_id,
                "approach": name,
                "candidate_pool_size": candidate_count,
                "selected_count": len(selected),
                "distinct_source_files": unique_files,
                "note": "Human relevance/fact-duplication labels are needed for quality conclusions.",
            })

    write_csv(
        OUTPUT_DIR / "02_evidence_comparison.csv",
        rows,
        ["requirement_id", "requirement", "approach", "rank",
         "candidate_pool_size", "source_file", "chunk_index", "rerank_score",
         "text_preview", "human_relevance_0_1_2", "human_fact_id", "human_notes"],
    )
    write_csv(
        OUTPUT_DIR / "03_comparison_summary.csv",
        summary,
        ["requirement_id", "approach", "candidate_pool_size",
         "selected_count", "distinct_source_files", "note"],
    )
    print("\nReports:")
    print("  data/diagnostics/01_index_inventory.csv")
    print("  data/diagnostics/02_evidence_comparison.csv")
    print("  data/diagnostics/03_comparison_summary.csv")
    print("\nHuman labels: relevance 0=irrelevant, 1=partial/contextual, 2=direct;")
    print("use the same fact_id for repeats of the SAME underlying experience within a requirement.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", nargs="+", type=int, default=[1, 7, 8, 15])
    parser.add_argument("--pool-size", type=int, default=15)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()

    if args.pool_size < 1 or args.top_k < 1:
        parser.error("--pool-size and --top-k must be positive")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    collection = get_diagnostic_collection()
    _, count = inventory(collection)
    if args.inventory_only:
        return
    if count == 0:
        raise ValueError("ChromaDB collection is empty. No indexing is performed.")
    job = JobDescription.model_validate_json(JOB_PATH.read_text(encoding="utf-8"))
    compare(job, count, args.requirements, args.pool_size, args.top_k)


if __name__ == "__main__":
    main()
