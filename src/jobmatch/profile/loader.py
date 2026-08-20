import json
from jobmatch.profile.validator import validate_profile


def load_profile(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        profile = json.load(file) # json => dict

    validate_profile(profile) # validate data

    return profile