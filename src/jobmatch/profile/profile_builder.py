"""
LLM-based profile construction from merged evidence.
"""

from openai import OpenAI

from jobmatch.profile.evidence import MergedEvidenceSet
from jobmatch.profile.models import ProfileContent
from jobmatch.llm.openai_usage import track_openai_usage
from jobmatch.llm.config import MODEL

def build_profile(
    evidence: MergedEvidenceSet
) -> ProfileContent:

    client = OpenAI()

    # Convert merged evidence into text for profile construction
    record_texts = []

    for index, record in enumerate(evidence.records, start=1):
        text = (
            f"Record {index}\n"
            f"Category: {record.category}\n"
            f"Content: {record.content}\n"
            f"Source files: {', '.join(record.source_files)}"
        )

        record_texts.append(text)

    evidence_text = "\n\n".join(record_texts)

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "developer",
                "content": (
                    "Build a structured candidate profile from the provided merged evidence. "
                    "Use only information supported by the evidence. "
                    "Do not invent or assume missing factual information. "
                    "Organize information into the most appropriate profile sections. "
                    "Research, employment experience, and projects should remain distinct. "
                    "Do not create multiple research entries for different aspects of the same research work. "
                    "Methods, tools, evaluation metrics, and technical details belonging to the same research "
                    "should be organized inside a single Research entry when appropriate. "
                    "Do not duplicate the same academic work across Research and Project. "
                    "If evidence describes the same academic research, keep it only in Research unless "
                    "there is clear evidence that it was also a separate project. "
                    "When multiple evidence records describe the same fact with different levels of detail, "
                    "preserve the most specific supported information rather than replacing it with a weaker description. "
                    "When multiple evidence records describe different proficiency levels for the same language, "
                    "preserve the strongest explicitly supported level, such as Native over Fluent. "
                    "Information may be reorganized across fields when its meaning is clear. "
                    "Avoid unnecessary duplication across profile sections. "
                    "If information required by the schema is not supported by the evidence, "
                    "use an empty list, None, or another schema-supported empty value as appropriate. "
                    "Do not perform job-match assessment."
                ),
            },
            {
                "role": "user",
                "content": evidence_text,
            },
        ],
        text_format=ProfileContent,
    )

    track_openai_usage(
        response=response,
        model=MODEL,
    )

    return response.output_parsed