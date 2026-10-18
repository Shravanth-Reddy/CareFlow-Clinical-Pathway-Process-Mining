
import random
from datetime import datetime

from careflow.config import DIRECT_PATHWAY
from careflow.simulator import generate_visit_timeline


def test_direct_visit_timeline():
    rng = random.Random(42)
    arrival_time = datetime(2026, 1, 5, 9, 0, 0)

    events = generate_visit_timeline(
        "CF0001",
        DIRECT_PATHWAY,
        arrival_time,
        rng,
    )

    assert len(events) == len(DIRECT_PATHWAY)

    for index, event in enumerate(events):
        assert event["Case_ID"] == "CF0001"
        assert event["Activity_Name"] == DIRECT_PATHWAY[index]
        assert event["End_Timestamp"] > event["Start_Timestamp"]

        if index > 0:
            previous_event = events[index - 1]
            assert (
                event["Start_Timestamp"]
                >= previous_event["End_Timestamp"]
            )

    for event in events:
        print(event)

    print("Direct visit timeline test passed!")


if __name__ == "__main__":
    test_direct_visit_timeline()
