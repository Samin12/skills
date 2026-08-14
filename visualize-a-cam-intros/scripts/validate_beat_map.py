#!/usr/bin/env python3
"""Validate a timed intro visualization beat map."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


PRESENTATIONS = {"fullscreen", "a-cam-pip", "split", "graphic", "a-cam-reset"}
REQUIRED_TEXT = ("claim", "visual", "source", "proof")


def fail(message: str) -> None:
    raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("beat_map", type=Path)
    parser.add_argument(
        "--require-continuous",
        action="store_true",
        help="fail when any part of range_ms is not covered by an explicit beat",
    )
    args = parser.parse_args()

    data = json.loads(args.beat_map.expanduser().read_text())
    project_range = data.get("range_ms")
    beats = data.get("beats")

    if not isinstance(project_range, list) or len(project_range) != 2:
        fail("range_ms must be [start_ms, end_ms]")
    range_start, range_end = project_range
    if not all(isinstance(value, int) for value in project_range) or range_end <= range_start:
        fail("range_ms values must be increasing integers")
    if not isinstance(beats, list) or not beats:
        fail("beats must be a non-empty array")

    previous_end = range_start
    sources: Counter[str] = Counter()
    warnings: list[str] = []

    for index, beat in enumerate(beats):
        label = f"beat {index + 1}"
        if not isinstance(beat, dict):
            fail(f"{label} must be an object")
        start_ms = beat.get("start_ms")
        end_ms = beat.get("end_ms")
        if not isinstance(start_ms, int) or not isinstance(end_ms, int):
            fail(f"{label} start_ms and end_ms must be integers")
        if end_ms <= start_ms:
            fail(f"{label} has an empty or reversed range")
        if start_ms < range_start or end_ms > range_end:
            fail(f"{label} falls outside range_ms")
        if start_ms < previous_end:
            fail(f"{label} overlaps the preceding beat")
        if start_ms > previous_end:
            message = f"uncovered gap: {previous_end}-{start_ms} ms"
            if args.require_continuous:
                fail(message)
            warnings.append(message)
        previous_end = end_ms

        for field in REQUIRED_TEXT:
            value = beat.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"{label} requires non-empty {field}")
        presentation = beat.get("presentation")
        if presentation not in PRESENTATIONS:
            fail(f"{label} presentation must be one of {sorted(PRESENTATIONS)}")
        sources[beat["source"].strip()] += 1

    if previous_end < range_end:
        message = f"uncovered gap: {previous_end}-{range_end} ms"
        if args.require_continuous:
            fail(message)
        warnings.append(message)
    for source, count in sources.items():
        if count >= 3:
            warnings.append(f"source used {count} times; confirm each use adds new proof: {source}")

    result = {
        "valid": True,
        "range_ms": project_range,
        "beat_count": len(beats),
        "covered_ms": sum(beat["end_ms"] - beat["start_ms"] for beat in beats),
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        raise SystemExit(1)
