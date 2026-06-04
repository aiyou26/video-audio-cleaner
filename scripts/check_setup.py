#!/usr/bin/env python3
"""Check local dependencies for the video-audio-cleaner skill."""

from __future__ import annotations

import importlib.util
import importlib.metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    fix: Optional[str] = None


def command_version(command: str, args: list[str]) -> CheckResult:
    path = shutil.which(command)
    if not path:
        return CheckResult(command, False, "not found in PATH", f"install {command} and make sure it is available in PATH")
    try:
        completed = subprocess.run([command, *args], check=False, capture_output=True, text=True, timeout=15)
        first_line = (completed.stdout or completed.stderr or "").splitlines()[0:1]
        detail = first_line[0] if first_line else path
        return CheckResult(command, True, detail)
    except Exception as exc:
        return CheckResult(command, True, f"found at {path}, but version check failed: {exc}")


def module_check(import_name: str, pip_name: str) -> CheckResult:
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return CheckResult(pip_name, False, "python package not installed", f"python -m pip install -U {pip_name}")
    return CheckResult(pip_name, True, f"module {import_name} is importable")



def package_version(distribution_name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def version_tuple(version: str) -> tuple[int, ...]:
    clean = version.split("+")[0]
    parts: list[int] = []
    for piece in clean.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts)


def is_newer_than(version: str, baseline: str) -> bool:
    left = version_tuple(version)
    right = version_tuple(baseline)
    max_len = max(len(left), len(right))
    left = left + (0,) * (max_len - len(left))
    right = right + (0,) * (max_len - len(right))
    return left > right


def parse_ffmpeg_major(detail: str) -> Optional[int]:
    match = re.search(r"ffmpeg version\s+([0-9]+)", detail, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def optional_module_check(import_name: str, pip_name: str, note: str) -> CheckResult:
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return CheckResult(pip_name, True, f"optional package not installed; {note}")
    return CheckResult(pip_name, True, f"optional module {import_name} is importable")

def print_result(result: CheckResult) -> None:
    icon = "OK" if result.ok else "MISSING"
    print(f"[{icon}] {result.name}: {result.detail}")
    if not result.ok and result.fix:
        print(f"      fix: {result.fix}")


def main() -> int:
    print("Checking video-audio-cleaner setup...\n")
    ffmpeg_result = command_version("ffmpeg", ["-version"])
    results = [
        ffmpeg_result,
        command_version("ffprobe", ["-version"]),
        command_version("deepFilter", ["--help"]),
        module_check("demucs", "demucs"),
        module_check("df", "deepfilternet"),
        module_check("torch", "torch"),
        module_check("torchaudio", "torchaudio"),
        module_check("soundfile", "soundfile"),
    ]
    optional_results = [
        optional_module_check("torchcodec", "torchcodec", "install only if you need PyTorch tensor-level media decoding/encoding"),
    ]

    for result in results:
        print_result(result)

    print("\nOptional checks:")
    for result in optional_results:
        print_result(result)

    major = parse_ffmpeg_major(ffmpeg_result.detail) if ffmpeg_result.ok else None
    torchcodec_installed = importlib.util.find_spec("torchcodec") is not None
    torchaudio_version = package_version("torchaudio")

    if major is not None:
        print(f"\nDetected FFmpeg major version: {major}")
        if major > 8:
            print("Note: normal CLI processing may still work, but TorchCodec may fail with FFmpeg versions newer than 8. Avoid TorchCodec unless you specifically need it.")
        elif major >= 8:
            print("FFmpeg 8 detected. This skill can use FFmpeg CLI normally. If TorchCodec-related errors appear, use the Windows known-good dependency file.")
        elif major >= 4:
            print("FFmpeg version is suitable for this skill's normal CLI workflow.")

    if torchaudio_version:
        print(f"Detected torchaudio version: {torchaudio_version}")
        if is_newer_than(torchaudio_version, "2.5.1"):
            print("Note: if you see TorchCodec/FFmpeg errors, install the known-good stack: torch==2.5.1 and torchaudio==2.5.1.")
        elif version_tuple(torchaudio_version) == version_tuple("2.5.1"):
            print("torchaudio 2.5.1 detected: this matches the known-good workaround for TorchCodec/FFmpeg 8 issues.")

    if torchcodec_installed:
        print("TorchCodec is installed. It is optional for this skill; uninstall it if it causes FFmpeg compatibility errors.")

    missing = [r for r in results if not r.ok]
    print()
    if missing:
        print("Some required dependencies are missing. Install the items listed above, then run this check again.")
        return 1
    print("All required dependencies appear to be available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
