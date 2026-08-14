#!/usr/bin/env python3
"""Validate Project-time to media-offset arithmetic for copied B-roll extracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RANGE_FIELDS = (
    "donor_project_ms",
    "donor_media_ms",
    "desired_project_ms",
    "expected_media_ms",
    "destination_project_ms",
)


def fail(message: str) -> None:
    raise ValueError(message)


def read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).expanduser().read_text())


def read_range(item: dict[str, Any], field: str, label: str) -> tuple[int, int]:
    value = item.get(field)
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(isinstance(part, int) for part in value)
        or value[1] <= value[0]
    ):
        fail(f"{label} {field} must be [start_ms, end_ms] increasing integers")
    return value[0], value[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", help="JSON file path, or - to read JSON from stdin")
    parser.add_argument("--tolerance-ms", type=int, default=2)
    args = parser.parse_args()
    if args.tolerance_ms < 0:
        parser.error("--tolerance-ms must be non-negative")

    data = read_json(args.ledger)
    extracts = data.get("extractions") if isinstance(data, dict) else None
    if not isinstance(extracts, list) or not extracts:
        fail("extractions must be a non-empty array")

    results: list[dict[str, Any]] = []
    for index, item in enumerate(extracts):
        label = f"extraction {index + 1}"
        if not isinstance(item, dict):
            fail(f"{label} must be an object")
        name = item.get("name", label)
        if not isinstance(name, str) or not name.strip():
            fail(f"{label} name must be non-empty text")
        ranges = {field: read_range(item, field, label) for field in RANGE_FIELDS}
        speed = item.get("speed", 1)
        if not isinstance(speed, (int, float)) or isinstance(speed, bool) or speed <= 0:
            fail(f"{label} speed must be a positive number")

        donor_project = ranges["donor_project_ms"]
        donor_media = ranges["donor_media_ms"]
        desired_project = ranges["desired_project_ms"]
        expected_media = ranges["expected_media_ms"]
        destination = ranges["destination_project_ms"]

        if desired_project[0] < donor_project[0] or desired_project[1] > donor_project[1]:
            fail(f"{label} desired_project_ms falls outside donor_project_ms")

        donor_project_duration = donor_project[1] - donor_project[0]
        donor_media_duration = donor_media[1] - donor_media[0]
        predicted_donor_media_duration = round(donor_project_duration * float(speed))
        if abs(donor_media_duration - predicted_donor_media_duration) > args.tolerance_ms:
            fail(
                f"{label} donor durations disagree: Project {donor_project_duration} ms at "
                f"{speed}x predicts {predicted_donor_media_duration} media ms, got {donor_media_duration}"
            )

        computed_media = (
            donor_media[0] + round((desired_project[0] - donor_project[0]) * float(speed)),
            donor_media[0] + round((desired_project[1] - donor_project[0]) * float(speed)),
        )
        if any(
            abs(actual - computed) > args.tolerance_ms
            for actual, computed in zip(expected_media, computed_media)
        ):
            fail(
                f"{label} expected_media_ms {list(expected_media)} does not match computed "
                f"{list(computed_media)}"
            )

        desired_duration = desired_project[1] - desired_project[0]
        destination_duration = destination[1] - destination[0]
        if abs(destination_duration - desired_duration) > args.tolerance_ms:
            fail(
                f"{label} destination duration {destination_duration} ms does not match "
                f"desired Project duration {desired_duration} ms"
            )

        results.append(
            {
                "name": name.strip(),
                "computed_media_ms": list(computed_media),
                "destination_duration_ms": destination_duration,
                "valid": True,
            }
        )

    print(json.dumps({"valid": True, "extractions": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        raise SystemExit(1)
