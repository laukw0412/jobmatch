from pydantic import ValidationError
from jobmatch.profile.models import PersonalProfile


def validate_profile(profile):
    try:
        # Validate the input profile structure and field types;
        # raises ValidationError if against the profile schema
        PersonalProfile.model_validate(profile)

    except ValidationError as error:
        raise ValueError(
            f"Invalid profile data:\n{error}"
        ) from error

    return True