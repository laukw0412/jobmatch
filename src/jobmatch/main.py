from jobmatch.document.loader import load_document


def main():
    document = load_document(r"data\documents\拼图 学生证.pdf")

    print("--------------------------------------")
    print(f"Source: {document.source_file}")
    print(f"Type: {document.file_type}")
    print("--------------------------------------")
    print(document.text)

if __name__ == "__main__":
    main()