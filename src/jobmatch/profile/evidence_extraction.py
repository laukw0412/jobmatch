"""
LLM-based evidence extraction from source documents.
"""

from openai import OpenAI

from jobmatch.document.models import DocumentContent
from jobmatch.profile.evidence import EvidenceSet
from jobmatch.llm.openai_usage import track_openai_usage
from jobmatch.llm.config import MODEL


def normalize_text(text: str) -> str:
    text = text.replace("*", "")
    return " ".join(text.split())


def verify_evidence(
    evidence: EvidenceSet,
    document_content: DocumentContent
) -> EvidenceSet:

    for record in evidence.records:
        record.source_file = document_content.source_file
        record.file_type = document_content.file_type

        strict_match = record.source_text in document_content.text

        normalized_match = (
            normalize_text(record.source_text)
            in normalize_text(document_content.text)
        )

        record.source_verified = strict_match or normalized_match

    return evidence


def extract_evidence(
    document_content: DocumentContent
) -> EvidenceSet:

    client = OpenAI()

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": (
                    "Extract useful candidate information from the provided document. "
                    "Preserve information explicitly stated or directly supported by the document. "
                    "Do not invent unsupported facts. "
                    "Each evidence record should preserve the original supporting text. "
                    "Use broad categories only when reasonably clear. "
                    "If the category is ambiguous, leave it null rather than forcing a classification. "
                    "Do not deduplicate, consolidate, or normalize information across records. "
                    "Do not perform job-match assessment."
                ),
            },
            {
                "role": "user",
                "content": document_content.text,
            },
        ],
        text_format=EvidenceSet,
    )

    track_openai_usage(
        response=response,
        model=MODEL,
    )

    evidence = response.output_parsed

    return verify_evidence(
    evidence=evidence,
    document_content=document_content
)