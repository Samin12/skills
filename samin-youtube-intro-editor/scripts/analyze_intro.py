#!/usr/bin/env python3
"""Analyze a YouTube intro with ffprobe/ffmpeg and write reusable review artifacts."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys


def run(args: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--duration", type=float, default=90.0)
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--scene-threshold", type=float, default=0.22)
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.is_file():
        parser.error(f"input does not exist: {source}")
    args.out.mkdir(parents=True, exist_ok=True)

    metadata_raw = run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)],
        capture=True,
    ).stdout
    metadata = json.loads(metadata_raw)
    (args.out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    columns = 6
    rows = max(1, int(args.duration / args.interval / columns + 0.999))
    contact = args.out / "contact-sheet.jpg"
    run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-t", str(args.duration), "-i", str(source),
            "-vf", f"fps=1/{args.interval},scale=320:-2,tile={columns}x{rows}:padding=4:margin=4:color=0x111111",
            "-frames:v", "1", str(contact),
        ]
    )

    scene = run(
        [
            "ffmpeg", "-hide_banner", "-t", str(args.duration), "-i", str(source),
            "-filter:v", f"select='gt(scene,{args.scene_threshold})',showinfo", "-f", "null", "-",
        ],
        capture=True,
    )
    cuts = [float(value) for value in re.findall(r"pts_time:([0-9.]+)", scene.stderr)]
    (args.out / "scene-cuts.json").write_text(json.dumps({"threshold": args.scene_threshold, "cuts": cuts}, indent=2) + "\n")

    summary = {
        "input": str(source),
        "analyzed_seconds": args.duration,
        "cut_count": len(cuts),
        "mean_seconds_per_cut": round(args.duration / max(1, len(cuts)), 2),
        "contact_sheet": str(contact),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"command failed: {exc.cmd}", file=sys.stderr)
        raise SystemExit(exc.returncode)
