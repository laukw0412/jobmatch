from pydantic import ValidationError
from src.jobmatch.profile.schema import ProfileContent


def validate_profile(profile):
    try:
        # Validate the input profile structure and field types;
        # raises ValidationError if against the profile schema
        ProfileContent.model_validate(profile)

    except ValidationError as error:
        raise ValueError(
            f"Invalid profile data:\n{error}"
        ) from error

    return True