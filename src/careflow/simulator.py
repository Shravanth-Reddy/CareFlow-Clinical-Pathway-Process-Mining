
import random
from datetime import timedelta

from careflow.config import (
    RANDOM_SEED,
    EXTENDED_ACTIVITY_PROBABILITY,
    ACTIVITY_DURATIONS,
    LONG_WAIT_PROPORTION,
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

from careflow.config import BOTTLENECK_TRANSITIONS, BOTTLENECK_WEIGHT


def select_long_wait_transitions(pathways, rng):
    """Select an exact count of transitions using weighted sampling."""

    eligible = []

    for case_id, pathway in pathways.items():
        for index in range(len(pathway) - 1):
            from_activity = pathway[index]
            to_activity = pathway[index + 1]

            weight = (
                BOTTLENECK_WEIGHT
                if (from_activity, to_activity) in BOTTLENECK_TRANSITIONS
                else 1
            )

            eligible.append(
                (case_id, from_activity, to_activity, weight)
            )

    target_count = round(len(eligible) * LONG_WAIT_PROPORTION)

    if target_count > len(eligible):
        raise ValueError("Long-wait target exceeds eligible transitions.")

    remaining = eligible.copy()
    selected = set()

    for _ in range(target_count):
        total_weight = sum(item[3] for item in remaining)
        draw = rng.uniform(0, total_weight)
        cumulative_weight = 0

        for item in remaining:
            cumulative_weight += item[3]

            if draw <= cumulative_weight:
                selected.add(item[:3])
                remaining.remove(item)
                break

    return selected
