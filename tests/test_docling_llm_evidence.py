from jobmatch.document.loader import load_document
from jobmatch.profile.evidence_extraction import extract_evidence


# Load the document.
# DOCX/PDF should use Docling as the primary extraction method.
document = load_document(
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (EN).docx"
)

print("Document loaded:")
print(document.source_file)
print(document.file_type)

print()
print("Document text:")
print(document.text)

# Extract evidence from the document using the LLM.
evidence = extract_evidence(document)

print()
print("Document Evidence:")
print(evidence.model_dump_json(indent=2))

# Count source verification results.
verified_count = sum(
    record.source_verified
    for record in evidence.records
)

total_count = len(evidence.records)
unverified_count = total_count - verified_count

print()
print("Evidence Verification:")
print(f"Total: {total_count}")
print(f"Verified: {verified_count}")
print(f"Unverified: {unverified_count}")

# Display unverified evidence for inspection.
if unverified_count > 0:
    print()
    print("Unverified Evidence:")

    for record in evidence.records:
        if not record.source_verified:
            print()
            print(record.source_text)