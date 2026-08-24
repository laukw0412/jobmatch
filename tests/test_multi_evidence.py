from jobmatch.document.loader import load_document
from jobmatch.profile.evidence_extraction import extract_evidence


all_records = []
file_paths = [
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (EN).pdf",
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (JP).pdf",
]

for file_path in file_paths:
    document = load_document(file_path)

    print()
    print("=" * 80)
    print("Document loaded:")
    print(document.source_file)
    print(document.file_type)

    evidence = extract_evidence(document)

    print()
    print("Evidence count:")
    print(len(evidence.records))

    all_records.extend(evidence.records)

print()
print("=" * 80)
print("Combined Evidence")
print(f"Total records: {len(all_records)}")

for index, record in enumerate(all_records, start=1):
    print()
    print(f"Record {index}")
    print(f"Category: {record.category}")
    print(f"Content: {record.content}")
    print(f"Source file: {record.source_file}")
    print(f"Verified: {record.source_verified}")