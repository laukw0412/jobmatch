from openai import OpenAI

from jobmatch.profile.evidence import Evidence, MergedEvidenceSet
from jobmatch.llm.openai_usage import track_openai_usage
from jobmatch.llm.config import MODEL


def merge_evidence(
        records: list [Evidence]
) -> MergedEvidenceSet:

    client = OpenAI()

    # Convert EvidenceRecord objects into text that can be reviewed together
    record_texts = []

    for index, record in enumerate(records, start=1):
        text = (
            f"Record {index}\n"
            f"Category: {record.category}\n"
            f"Content: {record.content}\n"
            f"Source file: {record.source_file}\n"
            f"Source verified: {record.source_verified}"
        )
        record_texts.append(text)
    
    evidence_text = "\n\n".join(record_texts)

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": (
                    "Consolidate candidate evidence collected from multiple documents. "
                    "Identify records that describe the same candidate fact even when "
                    "they are written in different languages or use different wording. "
                    "Merge complementary information when it describes the same fact. "
                    "Do not discard unique information. "
                    "Do not invent information that is not supported by the provided evidence. "
                    "If two records genuinely conflict, preserve both rather than choosing one. "
                    "Use broad categories only when reasonably clear. "
                    "Do not perform job-match assessment."
                ),
            },
            {
                "role": "user",
                "content": evidence_text,
            },
        ],
        text_format=MergedEvidenceSet,
    )

    track_openai_usage(
        response=response,
        model=MODEL,
    )

    return response.output_parsed