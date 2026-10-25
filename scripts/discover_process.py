"""Discover and render a PM4Py frequency DFG from the dbt-normalized event log."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd
import pm4py
from google.cloud import bigquery
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.visualization.dfg.variants import frequency as dfg_frequency_vis


PROJECT_ID_PATTERN = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]\Z")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def resolve_graphviz(parser: argparse.ArgumentParser) -> tuple[str, str]:
    """Find Graphviz and return the dot executable path and version string."""
    configured_dot = os.environ.get("GRAPHVIZ_DOT")
    dot_path = configured_dot if configured_dot and Path(configured_dot).is_file() else shutil.which("dot")
    if dot_path is None:
        default_bin = Path(r"C:\Program Files\Graphviz\bin")
        candidate = default_bin / "dot.exe"
        if candidate.is_file():
            dot_path = str(candidate)
    if dot_path is not None:
        os.environ["PATH"] = str(Path(dot_path).parent) + os.pathsep + os.environ.get("PATH", "")
    if dot_path is None:
        parser.error(
            "Graphviz 'dot' was not found. Install it with winget install "
            "--id Graphviz.Graphviz --exact."
        )
    version_result = subprocess.run(
        [dot_path, "-V"], capture_output=True, text=True, check=True
    )
    version_text = (version_result.stderr or version_result.stdout).strip()
    return dot_path, version_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="care-flow-512415")
    parser.add_argument("--graph", default="outputs/process_map.png")
    parser.add_argument("--dot", default="outputs/process_map.gv")
    parser.add_argument("--report", default="reports/process_discovery.json")
    args = parser.parse_args()
    if not PROJECT_ID_PATTERN.fullmatch(args.project):
        parser.error("--project must be a valid Google Cloud project ID.")
    dot_executable, graphviz_version = resolve_graphviz(parser)
    project = args.project
    relation = f"{project}.careflow_week2.fct_event_log"
    metadata_relation = f"{project}.careflow.case_metadata"

    client = bigquery.Client(project=project)
    df = client.query(
        f"SELECT Case_ID, Activity_Name, Timestamp FROM `{relation}`"
    ).to_dataframe()
    if df.empty:
        raise ValueError(f"Normalized event log `{relation}` is empty")
    required = ["Case_ID", "Activity_Name", "Timestamp"]
    if df[required].isna().any().any():
        raise ValueError(f"Normalized event log `{relation}` contains null required fields")

    # BigQuery TIMESTAMP values must arrive timezone-aware. Refuse to silently
    # interpret a naive datetime as UTC or local time.
    timestamps = pd.to_datetime(df["Timestamp"], errors="raise")
    if not isinstance(timestamps.dtype, pd.DatetimeTZDtype):
        raise TypeError(
            "Timestamp must be timezone-aware from BigQuery; refusing to infer a timezone."
        )
    df["Timestamp"] = timestamps
    ties = int(df.duplicated(["Case_ID", "Timestamp"], keep=False).sum())
    df = df.sort_values(["Case_ID", "Timestamp", "Activity_Name"], kind="stable")
    pm_frame = df.rename(
        columns={
            "Case_ID": "case:concept:name",
            "Activity_Name": "concept:name",
            "Timestamp": "time:timestamp",
        }
    )
    event_log = pm4py.convert_to_event_log(pm_frame)

    # Discover the directly-follows graph and start/end frequencies from this log.
    dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)
    activity_counts = Counter(
        event["concept:name"] for trace in event_log for event in trace
    )
    params = {
        dfg_frequency_vis.Parameters.START_ACTIVITIES: start_activities,
        dfg_frequency_vis.Parameters.END_ACTIVITIES: end_activities,
        dfg_frequency_vis.Parameters.FORMAT: "png",
        dfg_frequency_vis.Parameters.RANKDIR: "LR",
        dfg_frequency_vis.Parameters.GRAPH_TITLE: "CareFlow observed frequency DFG — PM4Py",
    }
    gviz = dfg_visualizer.apply(
        dfg,
        log=event_log,
        activities_count=dict(activity_counts),
        parameters=params,
    )
    graph_path = Path(args.graph)
    dot_path = Path(args.dot)
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    dot_path.parent.mkdir(parents=True, exist_ok=True)
    # Both artifacts come from the same PM4Py DFG visualizer object.
    dfg_visualizer.save(gviz, str(dot_path))
    dfg_visualizer.save(gviz, str(graph_path))
    if graph_path.read_bytes()[:8] != PNG_SIGNATURE:
        raise ValueError(f"Graphviz did not produce a valid PNG at {graph_path}")
    dot_source = dot_path.read_text(encoding="utf-8")
    if not dot_source.strip() or not dot_source.lstrip().startswith("digraph"):
        raise ValueError(f"PM4Py did not produce valid Graphviz source at {dot_path}")

    incomplete = next(
        iter(
            client.query(
                f"SELECT COUNT(DISTINCT m.Case_ID) AS n "
                f"FROM `{metadata_relation}` m "
                f"JOIN `{relation}` e USING (Case_ID) "
                "WHERE m.Is_Incomplete = TRUE"
            ).result()
        )
    ).n
    traces = Counter(
        tuple(event["concept:name"] for event in trace) for trace in event_log
    )
    result = {
        "source_relation": relation,
        "pm4py_version": pm4py.__version__,
        "discovery_algorithm": "PM4Py frequency directly-follows graph (DFG)",
        "event_count": len(df),
        "case_count": int(df["Case_ID"].nunique()),
        "incomplete_cases_with_observed_events": int(incomplete),
        "activities": sorted(activity_counts),
        "activity_event_counts": dict(sorted(activity_counts.items())),
        "directly_follows_edges": len(dfg),
        "start_activities": start_activities,
        "end_activities": end_activities,
        "timestamp_dtype": str(df["Timestamp"].dtype),
        "timestamp_source": "BigQuery TIMESTAMP; timezone-aware connector values preserved",
        "case_timestamp_tie_events": ties,
        "exact_trace_counts": [
            {"activities": list(trace), "cases": count}
            for trace, count in traces.most_common(10)
        ],
        "graph_png": str(graph_path),
        "pm4py_visualizer_export": str(dot_path),
        "graph_png_bytes": graph_path.stat().st_size,
        "graphviz_source_bytes": dot_path.stat().st_size,
        "graphviz_dot": dot_executable,
        "graphviz_version": graphviz_version,
        "ordering_note": (
            "Events sort by case and timestamp; activity-name tie-break is only "
            "serialization and does not establish clinical order."
        ),
        "interpretation_note": (
            "Exact trace counts are complete event sequences. The DFG represents "
            "observed adjacent activity frequencies, not clinical correctness."
        ),
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
