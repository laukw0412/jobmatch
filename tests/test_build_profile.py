
"""
first run:
python E:/Projects/jobmatch/tests/test_build_profile.py --no-cache
later:
python E:/Projects/jobmatch/tests/test_build_profile.py
"""

import argparse
from pathlib import Path

from jobmatch.document.loader import load_document
from jobmatch.profile.evidence import MergedEvidenceSet
from jobmatch.profile.evidence_extraction import extract_evidence
from jobmatch.profile.evidence_merge import merge_evidence
from jobmatch.profile.profile_builder import build_profile

# Command-line arguments
parser = argparse.ArgumentParser()

parser.add_argument(
    "--no-cache",
    action="store_true",
    help="Ignore cached merged evidence and regenerate it."
)

args = parser.parse_args()

# Cache is enabled by default
USE_CACHE = not args.no_cache

# Source documents
file_paths = [
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (EN).pdf",
    r"E:\Projects\jobmatch\data\documents\KA WANG LAU Resume (JP).pdf",
]

# Cache file
merged_evidence_path = Path(
    r"E:\Projects\jobmatch\data\test_outputs\merged_evidence.json"
)

# Step 1 & 2: Get merged evidence
if USE_CACHE and merged_evidence_path.exists():
    print("Using cached merged evidence.")

    merged_evidence = MergedEvidenceSet.model_validate_json(
        merged_evidence_path.read_text(encoding="utf-8")
    )

else:
    print("Generating new merged evidence.")

    all_records = []

    # Step 1: Load documents and extract evidence
    for file_path in file_paths:
        document = load_document(file_path)
        evidence = extract_evidence(document)

        all_records.extend(evidence.records)

    print()
    print("=" * 80)
    print("Evidence extraction:")
    print(f"Records: {len(all_records)}")

    # Step 2: Merge evidence
    merged_evidence = merge_evidence(all_records)

    print()
    print("=" * 80)
    print("Evidence merge:")
    print(f"Records: {len(merged_evidence.records)}")

    # Save merged evidence to cache
    merged_evidence_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged_evidence_path.write_text(
        merged_evidence.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print()
    print(f"Merged evidence saved to: {merged_evidence_path}")

# Step 3: Build final profile
profile = build_profile(merged_evidence)

print()
print("=" * 80)
print("Profile Content:")
print()
print(profile.model_dump_json(indent=2))