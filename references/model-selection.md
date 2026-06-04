# Model Selection Guide

Use this reference when deciding which operation to run.

## remove-vocals

Goal: remove singing or prominent vocals and keep accompaniment/background music.

Primary tool: Demucs with `--two-stems=vocals`.

Output to use: `no_vocals.wav`.

Best for:

- songs
- music videos
- karaoke-style accompaniment extraction

Limitations:

- background vocals may remain
- reverb tails may remain
- some instruments may be damaged if they overlap with vocals

## extract-vocals

Goal: keep vocals or voice and remove most accompaniment.

Primary tool: Demucs with `--two-stems=vocals`.

Output to use: `vocals.wav`.

Best for:

- vocal extraction
- speech extraction from media with music
- preparing voice material for further denoising

## clean-speech

Goal: keep speech while reducing background music and noise.

Primary tools:

1. Demucs to isolate vocals/speech.
2. DeepFilterNet to enhance and denoise the isolated speech.

Best for:

- short video voiceover with background music
- interviews with music bed
- educational videos with background music
- social media videos where speech should be clearer

Limitations:

- if speech is much quieter than music, artifacts may be strong
- music can leak into vocals stem
- speech may become less natural after enhancement

## denoise

Goal: reduce noise without separating vocals from music.

Primary tool: DeepFilterNet.

Best for:

- fan noise
- mild room noise
- hiss
- meeting recordings
- podcast/interview cleanup

Limitations:

- not designed to remove loud music behind speech
- may not remove other speakers or complex background sound

## replace-audio

Goal: put a processed audio track back into the original video.

Primary tool: FFmpeg.

Best for:

- manual workflows
- replacing a video track after external editing
- keeping video stream unchanged while updating audio
