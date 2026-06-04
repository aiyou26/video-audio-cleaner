---
name: video-audio-cleaner
description: clean video or audio files by removing vocals, extracting vocals or speech, reducing background music, enhancing speech clarity, or replacing a video's audio track. use when the user asks to process media files such as mp4, mov, mkv, wav, mp3, m4a, or flac for vocal removal, accompaniment extraction, speech isolation, background music reduction, denoising, or audio cleanup. when the desired operation is unclear, present the built-in operation menu and let the user choose before running scripts.
---

# Video Audio Cleaner

## Overview

Use this skill to help a user clean the audio inside a video or audio file. The skill supports beginner-friendly choices such as removing vocals, extracting vocals, reducing background music while keeping speech, and denoising speech.

Do not train models or bundle model weights in this skill. Use locally installed or environment-available tools such as `ffmpeg`, `demucs`, and `deepfilternet`. Treat TorchCodec as an optional advanced dependency only; the default workflow should use the FFmpeg command-line tools for maximum compatibility.

## Operation Menu

When the user has not clearly chosen an operation, show this menu and ask them to pick one option:

1. `remove-vocals` - 去人声，保留伴奏或背景音乐。适合歌曲、MV、带人声的音乐视频。
2. `extract-vocals` - 提取人声，只保留 vocals stem。适合想拿到歌声、人声、对白素材。
3. `clean-speech` - 保留说话声，尽量降低背景音乐和噪声。先用 Demucs 提取 vocals，再用 DeepFilterNet 增强。
4. `denoise` - 仅降噪和增强清晰度，不做人声/伴奏分离。适合采访、口播、会议录音。
5. `replace-audio` - 用一段新的音频替换原视频音轨。适合手动处理好音频后重新封装视频。
6. `check-setup` - 检查本机是否安装了 ffmpeg、demucs、deepfilternet。

If the user's wording maps clearly to one option, choose it without asking again. Examples:

- "把视频人声去掉" -> `remove-vocals`
- "只要人声" -> `extract-vocals`
- "去掉背景音乐，保留讲话" -> `clean-speech`
- "录音有杂音，帮我增强" -> `denoise`
- "把处理后的 wav 放回视频" -> `replace-audio`

## Workflow

1. Confirm the input file path and desired operation.
2. If the user is a beginner, briefly explain what the chosen operation will keep and remove.
3. Check setup with `scripts/check_setup.py` when the environment is unknown or the user asks how to install.
4. Run `scripts/video_audio_cleaner.py` with the selected mode.
5. Return the output file path and explain what was produced.
6. If quality is poor, suggest trying another mode instead of claiming perfect separation.

## Script Usage

Use the main script for actual processing:

```bash
python scripts/video_audio_cleaner.py input.mp4 --mode clean-speech --output-dir output
```

Common examples:

```bash
python scripts/video_audio_cleaner.py song.mp4 --mode remove-vocals
python scripts/video_audio_cleaner.py song.mp4 --mode extract-vocals
python scripts/video_audio_cleaner.py interview.mp4 --mode clean-speech
python scripts/video_audio_cleaner.py noisy.wav --mode denoise
python scripts/video_audio_cleaner.py original.mp4 --mode replace-audio --replacement-audio fixed.wav
```

## Tool Selection Rules

Use `references/model-selection.md` for detailed guidance. In short:

- Use Demucs for vocal/accompaniment separation.
- Use DeepFilterNet for speech denoising and clarity enhancement.
- Use FFmpeg for extracting audio and muxing processed audio back into video.
- Prefer `clean-speech` for videos that contain talking plus background music.
- Prefer `denoise` for speech with hiss, room noise, fan noise, or mild background noise.


## TorchCodec and FFmpeg 8 Guidance

The scripts must not require TorchCodec for normal user workflows. Use `ffmpeg` and `ffprobe` via subprocess for extracting audio, probing media, and muxing output. This avoids shared-library issues and keeps setup beginner-friendly.

Use this known troubleshooting rule from prior runs:

- If `torchcodec` fails with FFmpeg 8, do not make TorchCodec required. Tell the user to avoid TorchCodec for this skill and install the known-good stack: `torch==2.5.1` and `torchaudio==2.5.1`.
- On Windows, if FFmpeg is missing, recommend `winget install --id Gyan.FFmpeg -e`; prior testing used FFmpeg 8.1.1 installed this way.
- If the user specifically needs TorchCodec for PyTorch tensor-level media decoding/encoding, treat it as an advanced optional path and warn that compatibility depends on the local FFmpeg/PyTorch/TorchCodec versions.

Prefer `requirements-windows-known-good.txt` for beginners on Windows who hit TorchCodec/FFmpeg errors.

## Handling Missing Dependencies

If a command fails because a dependency is missing:

- Missing `ffmpeg`: on Windows, tell the user to run `winget install --id Gyan.FFmpeg -e`; on macOS use `brew install ffmpeg`; on Linux use the package manager.
- Missing `demucs`: tell the user to run `python -m pip install -U demucs`.
- Missing `deepFilter`: tell the user to run `python -m pip install -U deepfilternet`.
- Missing PyTorch or torchaudio: for Windows beginners, prefer `python -m pip install -r requirements-windows-known-good.txt`; for GPU users, tell them to install compatible `torch` and `torchaudio` for their CUDA environment.
- TorchCodec/FFmpeg 8 conflict: tell the user TorchCodec is optional, then use `torch==2.5.1` and `torchaudio==2.5.1` unless they explicitly need TorchCodec.

Avoid bundling model files in the skill ZIP. Model files are large and should be downloaded by the dependency or managed outside the skill.

## Quality Notes

Be honest about limitations:

- Vocal/music separation is not perfect when voices and instruments overlap heavily.
- Strong reverb, compression, crowd noise, and game audio may leave artifacts.
- `clean-speech` may sound less natural than the original, but speech should usually be clearer.
- For best results, use high-quality source audio and avoid repeatedly compressing outputs.
