from jobmatch.document.loader import load_document
from jobmatch.profile.extractor import extract_profile


document = load_document(
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (EN).docx"
)

print("Document loaded:")
print(document.source_file)
print(document.file_type)

profile = extract_profile(document)

print()
print("Draft Profile:")
print(profile.model_dump_json(indent=2))