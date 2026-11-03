"""Read-only diagnosis of vector recall, source competition, and category routing."""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import chromadb

from jobmatch.jobs.models import JobDescription
from jobmatch.matching.reranker import rerank_chunks
from jobmatch.rag.retrieval import retrieve_chunks

COLLECTION_NAME = "jobmatch_documents"
JOB_PATH = ROOT / "data" / "test_structured_job.json"
OUTPUT_DIR = ROOT / "data" / "diagnostics"
EXCLUDED_FILES = {"two_column_resume_sample.docx"}

# This is a diagnostic hypothesis, not a production routing policy.
PREFERRED_CATEGORIES = {
    "education": {"resume", "academic_record"},
    "language": {"language_record", "resume", "career_history"},
    "technical": {"resume", "career_history"},
    "research": {"resume", "career_history"},
    "interest": {"resume", "career_history"},
}


def document_category(filename: str) -> str:
    """Apply explicit categories to the documents in the current test corpus."""
    name = filename.casefold()
    if filename in EXCLUDED_FILES or "sample" in name:
        return "sample"
    if "外国語" in filename or "n1" in name:
        return "language_record"
    if "出身大学" in filename or "成績証明" in filename or "学生证" in filename:
        return "academic_record"
    if "職務経歴書" in filename:
        return "career_history"
    if "resume" in name or "履歴書" in filename:
        return "resume"
    return "other"


def requirement_type(description: str) -> str:
    """Route only the selected diagnostic requirements, without LLM calls."""
    q = description.casefold()
    if any(term in q for term in ("english", "japanese language", "jlpt", "n1", "n2")):
        return "language"
    if any(term in q for term in ("master", "ph.d", "phd", "bachelor", "degree")):
        return "education"
    if any(term in q for term in ("anime", "entertainment", "culture", "interest")):
        return "interest"
    if any(term in q for term in ("publication", "research", "problem-solving")):
        return "research"
    return "technical"


def unique_sources_with_quota(chunks: list[dict], n: int, max_per_file: int = 3) -> list[dict]:
    """Cap each source in the initial selection, then fill remaining slots."""
    counts: Counter[str] = Counter()
    selected: list[dict] = []
    selected_ids: set[tuple] = set()
    for item in chunks:
        source = item.get("source_file", "")
        if counts[source] >= max_per_file:
            continue
        selected.append(item)
        counts[source] += 1
        selected_ids.add((source, item.get("chunk_index")))
        if len(selected) >= n:
            return selected
    for item in chunks:
        key = (item.get("source_file", ""), item.get("chunk_index"))
        if key not in selected_ids:
            selected.append(item)
            selected_ids.add(key)
        if len(selected) >= n:
            break
    return selected


def category_pool(chunks: list[dict], n: int, requirement: str) -> list[dict]:
    """Reserve up to 10/15 for likely document categories; keep broad fallback."""
    preferred = PREFERRED_CATEGORIES[requirement_type(requirement)]
    chosen = [x for x in chunks if document_category(x.get("source_file", "")) in preferred]
    others = [x for x in chunks if document_category(x.get("source_file", "")) not in preferred]
    preferred_budget = max(1, round(n * 2 / 3))
    proposed = unique_sources_with_quota(chosen, preferred_budget, 3)
    keys = {(x.get("source_file"), x.get("chunk_index")) for x in proposed}
    # Include fallback evidence even when preferred categories dominate.
    for item in others + chosen:
        key = (item.get("source_file"), item.get("chunk_index"))
        if key not in keys:
            proposed.append(item)
            keys.add(key)
        if len(proposed) >= n:
            break
    return proposed[:n]


def save_csv(filename: str, rows: list[dict], fields: list[str]) -> Path:
    path = OUTPUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", nargs="+", type=int, default=[1, 8, 15])
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--pool-small", type=int, default=15)
    parser.add_argument("--pool-large", type=int, default=30)
    parser.add_argument("--show-toefl", action="store_true", help="Print TOEFL chunk text locally")
    args = parser.parse_args()
    if args.top_k < 1 or args.pool_small < 1 or args.pool_large <= args.pool_small:
        parser.error("Require top-k >= 1 and pool-large > pool-small >= 1")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(ROOT / "data" / "chroma"))
    collection = client.get_collection(name=COLLECTION_NAME)
    count = collection.count()
    if count == 0:
        raise ValueError("Collection is empty. No indexing will be performed.")
    job = JobDescription.model_validate_json(JOB_PATH.read_text(encoding="utf-8"))

    detail_rows: list[dict] = []
    summary_rows: list[dict] = []
    toefl_rows: list[dict] = []

    print(f"Collection: {COLLECTION_NAME}; indexed chunks: {count}")
    print("Read-only: this script never indexes, updates, or deletes records.\n")

    for req_id in args.requirements:
        if not 1 <= req_id <= len(job.requirements):
            raise ValueError(f"Unknown requirement ID: {req_id}")
        query = job.requirements[req_id - 1].description

        # Query entire collection once. Slicing its vector-ranked results
        # reproduces the small/large candidate pools without extra embeddings.
        retrieved = retrieve_chunks(query=query, top_k=count, include_embeddings=False)
        eligible = [
            {**x, "vector_rank": pos, "document_category": document_category(x.get("source_file", ""))}
            for pos, x in enumerate(retrieved, start=1)
            if x.get("source_file") not in EXCLUDED_FILES
        ]
        small = eligible[:args.pool_small]
        large = eligible[:args.pool_large]
        diversified = unique_sources_with_quota(eligible, args.pool_small, max_per_file=3)
        routed = category_pool(eligible, args.pool_small, query)
        pools = [
            ("A_vector_top15", small),
            ("B_vector_top30", large),
            ("C_source_balanced15", diversified),
            ("D_category_routed15", routed),
        ]
        print(f"R{req_id}: {query}")
        print(f"  Vector candidates available (excluding sample): {len(eligible)}")
        for strategy, candidates in pools:
            ranked = rerank_chunks(query=query, chunks=candidates)[:args.top_k] if candidates else []
            print(f"  {strategy}: pool={len(candidates)}; top-{len(ranked)} sources={len(set(x.get('source_file') for x in ranked))}")
            for rank, chunk in enumerate(ranked, start=1):
                source = chunk.get("source_file", "")
                index = chunk.get("chunk_index", "")
                vector_rank = chunk["vector_rank"]
                print(f"    #{rank}  vector_rank={vector_rank:>2}  rerank={chunk['rerank_score']:.6f}  {source} | chunk {index}")
                detail_rows.append({
                    "requirement_id": req_id,
                    "requirement": query,
                    "strategy": strategy,
                    "rank": rank,
                    "vector_rank": vector_rank,
                    "rerank_score": f"{chunk['rerank_score']:.8f}",
                    "source_file": source,
                    "document_category": chunk["document_category"],
                    "chunk_index": index,
                    "text": chunk.get("text", ""),
                    "human_relevance_0_1_2": "",
                    "human_fact_id": "",
                })
            summary_rows.append({
                "requirement_id": req_id,
                "strategy": strategy,
                "candidate_pool_size": len(candidates),
                "selected_count": len(ranked),
                "distinct_source_files": len({x.get("source_file") for x in ranked}),
                "max_initial_vector_rank_in_top5": max((x["vector_rank"] for x in ranked), default=0),
                "direct_evidence_count_manual": "",
                "distinct_facts_count_manual": "",
            })

        if req_id == 8:
            for x in eligible:
                if "外国語（英語）試験成績証明書" in x.get("source_file", ""):
                    toefl_rows.append({
                        "vector_rank": x["vector_rank"],
                        "source_file": x.get("source_file", ""),
                        "chunk_index": x.get("chunk_index", ""),
                        "text": x.get("text", ""),
                        "contains_actual_score_manual": "",
                    })
                    if args.show_toefl:
                        print(f"\n[TOEFL chunk {x.get('chunk_index')}, vector rank {x['vector_rank']}]\n{x.get('text', '')}\n")
        print()

    detail = save_csv("04_recall_detail.csv", detail_rows, [
        "requirement_id", "requirement", "strategy", "rank", "vector_rank", "rerank_score",
        "source_file", "document_category", "chunk_index", "text", "human_relevance_0_1_2", "human_fact_id",
    ])
    summary = save_csv("05_recall_summary.csv", summary_rows, [
        "requirement_id", "strategy", "candidate_pool_size", "selected_count",
        "distinct_source_files", "max_initial_vector_rank_in_top5",
        "direct_evidence_count_manual", "distinct_facts_count_manual",
    ])
    print("Saved:", detail, "and", summary, sep="\n  ")
    if toefl_rows:
        toefl = save_csv("06_toefl_chunks.csv", toefl_rows, [
            "vector_rank", "source_file", "chunk_index", "text", "contains_actual_score_manual"
        ])
        print("  ", toefl)
    print("CSV files contain private document text. Keep data/diagnostics/ in .gitignore.")


if __name__ == "__main__":
    main()
