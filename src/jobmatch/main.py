from jobmatch.document.loader import load_document


def main():
    document = load_document(r"data\documents\N1 unofficial.png")

    print("--------------------------------------")
    print(f"Source: {document.source_file}")
    print(f"Type: {document.file_type}")
    print("--------------------------------------")
    print(document.text)

if __name__ == "__main__":
    main()