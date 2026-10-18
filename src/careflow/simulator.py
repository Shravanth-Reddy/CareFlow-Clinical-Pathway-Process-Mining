
import random
from datetime import timedelta
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



def create_activity_event(case_id, activity_name, start_time, rng):
    """Create one timestamped activity event."""

    duration, is_extended = generate_activity_duration(
        activity_name, rng
    )

    end_time = start_time + timedelta(minutes=duration)

    event = {
        "Case_ID": case_id,
        "Activity_Name": activity_name,
        "Start_Timestamp": start_time,
        "End_Timestamp": end_time,
    }

    return event, is_extended


def generate_visit_timeline(case_id, pathway, arrival_time, rng):
    """Generate timestamped events for one ordered patient pathway."""

    events = []
    current_start = arrival_time

    for index, activity_name in enumerate(pathway):
        event, is_extended = create_activity_event(
            case_id,
            activity_name,
            current_start,
            rng,
        )

        events.append(event)

        # Prepare the start time of the next activity.
        if index < len(pathway) - 1:
            waiting_time = generate_waiting_time(rng)
            current_start = (
                event["End_Timestamp"]
                + timedelta(minutes=waiting_time)
            )

    return events

