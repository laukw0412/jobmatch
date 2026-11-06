from dotenv import load_dotenv
from openai import OpenAI

from jobmatch.jobs.models import JobDescription


SYSTEM_PROMPT = """
You are a job description information extraction assistant.

Extract structured information for the primary job posting only.

Rules:
1. Identify the primary job title, company, and location.
2. Extract responsibilities separately from candidate requirements.
3. Extract all explicitly stated candidate requirements.
4. Classify each requirement using the provided categories.
5. Preserve required and preferred qualifications.
6. Preserve OR conditions such as "PyTorch or TensorFlow".
7. Preserve exact years of experience, degrees, and certifications.
8. Ignore navigation menus, buttons, login messages, and advertisements.
9. Ignore similar jobs, recommended jobs, and unrelated job postings.
10. Do not invent requirements or infer unstated qualifications.
11. Do not treat development environments as mandatory requirements.
12. Preserve the original meaning of each requirement.
13. Use null for unknown basic information.
14. Do not evaluate candidate suitability.
15. Do not guess missing requirements from incomplete text.
"""



def extract_job_description(
    jd_text: str,
    model: str = "gpt-4.1-mini",
    *,
    client: OpenAI | None = None,
) -> JobDescription:
    if not jd_text.strip():
        raise ValueError("Job description cannot be empty.")

    if client is None:
        load_dotenv()
        client = OpenAI()

    response = client.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": jd_text,
            },
        ],
        response_format=JobDescription,
        store=False,
    )

    result = response.choices[0].message.parsed

    if result is None:
        raise ValueError("Failed to extract job description.")

    return result
