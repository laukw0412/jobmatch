from openai import OpenAI

from jobmatch.document.models import DocumentContent
from jobmatch.profile.draft_models import DraftProfile
from jobmatch.llm.openai_usage import track_openai_usage


MODEL = "gpt-5.4-nano"
client = OpenAI()

def extract_profile(
        # Expected input type (type hint, not runtime enforcement)
        document_content: DocumentContent
# Expected return type
) -> DraftProfile:

    # parse() returns structured output instead of free-form text
    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                # Developer instruction: how the model should work
                "role": "developer",
                "content": (
                    "Extract candidate information from the provided document. "
                    "Only extract information explicitly stated or directly supported by the document. "
                    "Do not invent or assume missing factual information. "
                    "If information is not supported by the document, leave the corresponding field "
                    "as None or an empty list. "
                    "Follow explicit document section headings when assigning information to profile sections. "
                    "Do not duplicate the same entry across multiple profile sections. "
                    "Preserve the original meaning of the document while organizing the information "
                    "into the provided schema. "
                    "Do not perform job-match assessment or infer additional candidate qualifications."
                )
            },
            {
                # User input: the actual extracted document text
                "role": "user",
                "content": document_content.text
            }
        ],
        # Require output to follow the DraftProfile schema
        text_format=DraftProfile
    )

    track_openai_usage(
        response=response,
        model=MODEL
    )

    return response.output_parsed