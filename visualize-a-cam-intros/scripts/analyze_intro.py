#!/usr/bin/env python3
"""Probe an intro render and generate contact-sheet and defect evidence."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import subprocess
import sys


def run(args: list[str], capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=capture)


def detect_times(stderr: str, pattern: str) -> list[float]:
    return [float(value) for value in re.findall(pattern, stderr)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--scene-threshold", type=float, default=0.22)
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    if not source.is_file():
        parser.error(f"input does not exist: {source}")
    if args.interval <= 0:
        parser.error("--interval must be positive")
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    metadata = json.loads(
        run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source)],
            capture=True,
        ).stdout
    )
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    full_duration = float(metadata.get("format", {}).get("duration", 0.0))
    duration = full_duration if args.duration is None else min(args.duration, full_duration)
    if duration <= 0:
        parser.error("unable to determine a positive duration")

    columns = 6
    frame_count = max(1, math.ceil(duration / args.interval))
    rows = max(1, math.ceil(frame_count / columns))
    contact = out / "contact-sheet.jpg"
    run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-t", str(duration), "-i", str(source),
            "-vf", f"fps=1/{args.interval},scale=320:-2,tile={columns}x{rows}:padding=4:margin=4:color=0x111111",
            "-frames:v", "1", str(contact),
        ]
    )

    scene = run(
        [
            "ffmpeg", "-hide_banner", "-t", str(duration), "-i", str(source),
            "-filter:v", f"select='gt(scene,{args.scene_threshold})',showinfo", "-f", "null", "-",
        ],
        capture=True,
        check=False,
    )
    cuts = detect_times(scene.stderr, r"pts_time:([0-9.]+)")

    defects = run(
        [
            "ffmpeg", "-hide_banner", "-t", str(duration), "-i", str(source),
            "-vf", "blackdetect=d=0.08:pix_th=0.05,freezedetect=n=-55dB:d=0.8", "-an", "-f", "null", "-",
        ],
        capture=True,
        check=False,
    )
    black_starts = detect_times(defects.stderr, r"black_start:([0-9.]+)")
    black_ends = detect_times(defects.stderr, r"black_end:([0-9.]+)")
    freeze_starts = detect_times(defects.stderr, r"freeze_start: ([0-9.]+)")
    freeze_ends = detect_times(defects.stderr, r"freeze_end: ([0-9.]+)")

    video_streams = [stream for stream in metadata.get("streams", []) if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in metadata.get("streams", []) if stream.get("codec_type") == "audio"]
    primary = video_streams[0] if video_streams else {}
    report = {
        "input": str(source),
        "analyzed_seconds": duration,
        "video": {
            "codec": primary.get("codec_name"),
            "width": primary.get("width"),
            "height": primary.get("height"),
            "pixel_format": primary.get("pix_fmt"),
            "frame_rate": primary.get("avg_frame_rate") or primary.get("r_frame_rate"),
        },
        "audio_stream_count": len(audio_streams),
        "scene_cuts_seconds": cuts,
        "black_segments": list(zip(black_starts, black_ends)),
        "freeze_segments": list(zip(freeze_starts, freeze_ends)),
        "contact_sheet": str(contact),
    }
    (out / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"command failed: {exc.cmd}", file=sys.stderr)
        raise SystemExit(exc.returncode)
