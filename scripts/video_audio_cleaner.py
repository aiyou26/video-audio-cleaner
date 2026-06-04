#!/usr/bin/env python3
"""Clean video or audio by calling FFmpeg, Demucs, and DeepFilterNet.

This script intentionally does not bundle model weights. It calls installed tools and lets
those tools manage pretrained models.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Optional

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg", ".opus"}


class CleanerError(RuntimeError):
    pass


def run_command(command: list[str], label: str) -> None:
    print(f"\n== {label} ==")
    print(" ".join(str(part) for part in command))
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        raise CleanerError(f"command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise CleanerError(f"{label} failed with exit code {exc.returncode}") from exc


def require_command(command: str, install_hint: str) -> None:
    if shutil.which(command) is None:
        raise CleanerError(f"missing dependency: {command}. install hint: {install_hint}")


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def safe_stem(path: Path) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in path.stem).strip("._-") or "media"


def extract_audio(input_path: Path, work_dir: Path) -> Path:
    require_command("ffmpeg", "install ffmpeg and make sure it is in PATH")
    output_audio = work_dir / "input_audio.wav"
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "2",
            "-ar",
            "44100",
            str(output_audio),
        ],
        "extract audio from video",
    )
    return output_audio


def mux_audio_into_video(input_video: Path, processed_audio: Path, output_video: Path) -> Path:
    require_command("ffmpeg", "install ffmpeg and make sure it is in PATH")
    output_video.parent.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_video),
            "-i",
            str(processed_audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_video),
        ],
        "mux processed audio back into video",
    )
    return output_video


def copy_audio(processed_audio: Path, output_audio: Path) -> Path:
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    if processed_audio.resolve() != output_audio.resolve():
        shutil.copy2(processed_audio, output_audio)
    return output_audio


def find_named_file(root: Path, filename: str) -> Path:
    candidates = sorted(root.rglob(filename), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise CleanerError(f"could not find {filename} under {root}")
    return candidates[0]


def run_demucs(audio_path: Path, work_dir: Path) -> tuple[Path, Path]:
    demucs_out = work_dir / "demucs"
    demucs_out.mkdir(parents=True, exist_ok=True)
    run_command(
        [
            sys.executable,
            "-m",
            "demucs",
            "--two-stems=vocals",
            "-o",
            str(demucs_out),
            str(audio_path),
        ],
        "separate vocals with demucs",
    )
    vocals = find_named_file(demucs_out, "vocals.wav")
    no_vocals = find_named_file(demucs_out, "no_vocals.wav")
    return vocals, no_vocals


def list_audio_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for ext in AUDIO_EXTENSIONS:
        files.extend(root.rglob(f"*{ext}"))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def run_deepfilter(audio_path: Path, work_dir: Path) -> Path:
    require_command("deepFilter", "python -m pip install -U deepfilternet")
    deepfilter_out = work_dir / "deepfilter"
    deepfilter_out.mkdir(parents=True, exist_ok=True)
    before = {p.resolve() for p in list_audio_files(deepfilter_out)}
    start = time.time()
    run_command(
        [
            "deepFilter",
            str(audio_path),
            "-o",
            str(deepfilter_out),
        ],
        "enhance speech with deepfilternet",
    )
    after = list_audio_files(deepfilter_out)
    new_files = [p for p in after if p.resolve() not in before and p.stat().st_mtime >= start - 1]
    if new_files:
        return new_files[0]
    if after:
        return after[0]
    raise CleanerError(f"deepFilter finished but no output audio was found in {deepfilter_out}")


def build_output_path(input_path: Path, output_dir: Path, mode: str, video_output: bool) -> Path:
    stem = safe_stem(input_path)
    if video_output:
        suffix = input_path.suffix if input_path.suffix.lower() in VIDEO_EXTENSIONS else ".mp4"
        return output_dir / f"{stem}_{mode}{suffix}"
    return output_dir / f"{stem}_{mode}.wav"


def process(input_path: Path, mode: str, output_dir: Path, replacement_audio: Optional[Path], keep_workdir: bool) -> Path:
    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise CleanerError(f"input file does not exist: {input_path}")

    if mode == "replace-audio":
        if not is_video(input_path):
            raise CleanerError("replace-audio requires a video input file")
        if replacement_audio is None:
            raise CleanerError("replace-audio requires --replacement-audio")
        replacement_audio = replacement_audio.expanduser().resolve()
        if not replacement_audio.exists():
            raise CleanerError(f"replacement audio does not exist: {replacement_audio}")
        out = build_output_path(input_path, output_dir, mode, True)
        return mux_audio_into_video(input_path, replacement_audio, out)

    if not is_video(input_path) and not is_audio(input_path):
        raise CleanerError(f"unsupported file type: {input_path.suffix}")

    work_dir = output_dir / f".{safe_stem(input_path)}_{mode}_work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    source_audio = extract_audio(input_path, work_dir) if is_video(input_path) else input_path

    try:
        if mode == "remove-vocals":
            _, no_vocals = run_demucs(source_audio, work_dir)
            processed_audio = no_vocals
        elif mode == "extract-vocals":
            vocals, _ = run_demucs(source_audio, work_dir)
            processed_audio = vocals
        elif mode == "clean-speech":
            vocals, _ = run_demucs(source_audio, work_dir)
            processed_audio = run_deepfilter(vocals, work_dir)
        elif mode == "denoise":
            processed_audio = run_deepfilter(source_audio, work_dir)
        else:
            raise CleanerError(f"unsupported mode: {mode}")

        if is_video(input_path):
            output_path = build_output_path(input_path, output_dir, mode, True)
            result = mux_audio_into_video(input_path, processed_audio, output_path)
        else:
            output_path = build_output_path(input_path, output_dir, mode, False)
            result = copy_audio(processed_audio, output_path)

        return result
    finally:
        if not keep_workdir and work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean video/audio using ffmpeg, demucs, and deepfilternet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="input video or audio file")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["remove-vocals", "extract-vocals", "clean-speech", "denoise", "replace-audio"],
        help="operation to run",
    )
    parser.add_argument("--output-dir", default="output", help="directory for final outputs")
    parser.add_argument("--replacement-audio", help="audio file used by replace-audio mode")
    parser.add_argument("--keep-workdir", action="store_true", help="keep temporary files for debugging")
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = process(
            input_path=Path(args.input),
            mode=args.mode,
            output_dir=Path(args.output_dir),
            replacement_audio=Path(args.replacement_audio) if args.replacement_audio else None,
            keep_workdir=args.keep_workdir,
        )
    except CleanerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Tip: run `python scripts/check_setup.py` to check dependencies.", file=sys.stderr)
        return 1
    print(f"\nDone. Output: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
