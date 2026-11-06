def main():
    try:
        from jobmatch.ui.app import main as launch
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            raise SystemExit("PySide6 is required. Use the jobmatch environment and install its GUI dependencies.") from None
        raise
    return launch()

if __name__ == "__main__":
    raise SystemExit(main())
