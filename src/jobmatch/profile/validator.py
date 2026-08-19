from pydantic import ValidationError
from jobmatch.profile.models import PersonalProfile


def validate_profile(profile):
    try:
        PersonalProfile.model_validate(profile)

    except ValidationError as error:
        raise ValueError(
            f"Invalid profile data:\n{error}"
        ) from error

    return True