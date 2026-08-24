from jobmatch.document.loader import load_document
from jobmatch.profile.evidence_extraction import extract_evidence
from jobmatch.profile.evidence_merge import merge_evidence


file_paths = [
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (EN).pdf",
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (JP).pdf",
]

all_records = []

for file_path in file_paths:
    document = load_document(file_path)
    evidence = extract_evidence(document)

    all_records.extend(evidence.records)

print()
print("=" * 80)
print("Before consolidation:")
print(f"Records: {len(all_records)}")

merged = merge_evidence(all_records)

print()
print("=" * 80)
print("After consolidation:")
print(f"Records: {len(merged.records)}")

print()
print(merged.model_dump_json(indent=2))