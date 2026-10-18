
import random
from datetime import timedelta

from careflow.config import (
    RANDOM_SEED,
    EXTENDED_ACTIVITY_PROBABILITY,
    ACTIVITY_DURATIONS,
)


def generate_activity_duration(activity_name, rng):
    """
    Generate an activity duration in whole minutes.

    Ordinary duration: triangular distribution.
    Extended duration: uniform integer distribution.
    """
    ordinary_min, ordinary_mode, ordinary_max, extended_min, extended_max = (
        ACTIVITY_DURATIONS[activity_name]
    )

    # Decide whether this activity gets an extended duration.
    is_extended = rng.random() < EXTENDED_ACTIVITY_PROBABILITY

    if is_extended:
        duration = rng.randint(extended_min, extended_max)
    else:
        duration = round(
            rng.triangular(
                ordinary_min,
                ordinary_max,
                ordinary_mode,
            )
        )

    return duration, is_extended


if __name__ == "__main__":
    rng = random.Random(RANDOM_SEED)

    for activity in ACTIVITY_DURATIONS:
        duration, is_extended = generate_activity_duration(activity, rng)

        print(
            f"{activity}: {duration} minutes "
            f"| Extended: {is_extended}"
        )


from careflow.config import (
    ORDINARY_WAIT_MIN,
    ORDINARY_WAIT_MODE,
    ORDINARY_WAIT_MAX,
    LONG_WAIT_MIN,
    LONG_WAIT_MODE,
    LONG_WAIT_MAX,
)


def generate_waiting_time(rng, is_long_wait=False):
    """Generate an ordinary or injected long wait in whole minutes."""

    if is_long_wait:
        minimum = LONG_WAIT_MIN
        mode = LONG_WAIT_MODE
        maximum = LONG_WAIT_MAX
    else:
        minimum = ORDINARY_WAIT_MIN
        mode = ORDINARY_WAIT_MODE
        maximum = ORDINARY_WAIT_MAX

    wait = round(rng.triangular(minimum, maximum, mode))

    return wait

