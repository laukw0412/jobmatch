from jobmatch.document.loader import load_document


document = load_document(
    r"E:\Projects\jobmatch\data\documents\拼图 学生证.pdf"
)

print()
print("Document loaded:")
print(document.source_file)
print(document.file_type)

print()
print("Extracted text:")
print(document.text)