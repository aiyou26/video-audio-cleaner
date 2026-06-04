# Video Audio Cleaner Skill 使用说明

这个 Skill 用来帮助 Agent 处理视频或音频里的声音。它适合新手使用：你只需要告诉 Agent 你想做什么，或者从菜单里选一个操作。

它可以做这些事情：

1. 去人声，保留伴奏或背景音乐
2. 提取人声，只保留 vocals 或对白
3. 去背景音乐，尽量保留说话声
4. 给说话声音降噪、增强清晰度
5. 把处理好的音频重新放回视频

重要说明：这个 Skill 不会把大模型权重打包进去。它会调用你电脑或服务器上安装好的工具，例如 FFmpeg、Demucs、DeepFilterNet。第一次运行模型时，相关依赖可能会自动下载预训练模型。

## 适合哪些文件？

常见视频：

- `.mp4`
- `.mov`
- `.mkv`
- `.webm`

常见音频：

- `.wav`
- `.mp3`
- `.m4a`
- `.flac`
- `.aac`
- `.ogg`

## 操作菜单

使用者可以自选操作：

### 1. remove-vocals：去人声，保留伴奏

适合：歌曲、MV、带人声的音乐视频。

结果：输出一个人声尽量被去掉的音频或视频。

示例：

```bash
python scripts/video_audio_cleaner.py song.mp4 --mode remove-vocals
```

### 2. extract-vocals：提取人声

适合：只想要歌声、人声、对白素材。

结果：输出只保留人声的音频或视频。

示例：

```bash
python scripts/video_audio_cleaner.py song.mp4 --mode extract-vocals
```

### 3. clean-speech：保留说话声，降低背景音乐

适合：短视频口播、采访、课程视频、播客视频，里面有背景音乐但你想保留讲话。

它会先提取人声，再做人声增强。

示例：

```bash
python scripts/video_audio_cleaner.py interview.mp4 --mode clean-speech
```

### 4. denoise：只降噪，不做人声/伴奏分离

适合：风扇声、底噪、电流声、轻微环境噪声、会议录音不清晰。

示例：

```bash
python scripts/video_audio_cleaner.py noisy.wav --mode denoise
```

### 5. replace-audio：替换视频音轨

适合：你已经有一段处理好的音频，想把它放回原视频。

示例：

```bash
python scripts/video_audio_cleaner.py original.mp4 --mode replace-audio --replacement-audio fixed.wav
```

### 6. check-setup：检查环境

适合：第一次使用，不知道电脑有没有装好依赖。

示例：

```bash
python scripts/check_setup.py
```

## 第一次使用：安装依赖

### 第 1 步：安装 FFmpeg

FFmpeg 用来从视频里抽出音频，也用来把处理好的音频放回视频。

Windows 推荐用 `winget` 安装。打开 PowerShell，然后运行：

```bash
winget install --id Gyan.FFmpeg -e
```

安装完成后，关闭当前终端，重新打开 PowerShell，再检查：

```bash
ffmpeg -version
ffprobe -version
```

已验证可用版本：`FFmpeg 8.1.1`。如果命令提示“找不到 ffmpeg”，通常是 PATH 还没刷新，先重新打开终端；仍不行再重启电脑。

macOS 用户可以用 Homebrew：

```bash
brew install ffmpeg
```

Linux 用户可以用：

```bash
sudo apt update
sudo apt install ffmpeg
```

### 第 2 步：安装 Python 依赖

建议使用 Python 3.10 或 3.11。

进入 Skill 文件夹后运行：

```bash
python -m pip install -r requirements.txt
```

如果你在 Windows 上遇到 `torchcodec`、`torchaudio`、`FFmpeg 8` 相关报错，优先使用这个已验证的兼容安装方案：

```bash
python -m pip install -r requirements-windows-known-good.txt
```

这个文件会把 `torch` 和 `torchaudio` 固定到 `2.5.1`。这是前面实际处理时验证过的绕过方案：当 `torchcodec` 与 FFmpeg 8 不兼容时，降级到 `torchaudio==2.5.1` 可以避免走 TorchCodec 路径。

如果你只想先用去人声功能，至少安装：

```bash
python -m pip install -U demucs
```

如果你想用降噪和人声增强，安装：

```bash
python -m pip install -U deepfilternet
```

### 可选：TorchCodec 与 FFmpeg 8

这个 Skill 默认**不需要安装 TorchCodec**。它直接调用系统里的 `ffmpeg` / `ffprobe` 命令来抽音频和封装视频，这样最稳，也最容易排查问题。

前面版本实际处理时遇到过一个兼容性问题：

```text
torchcodec 与 FFmpeg 8 不兼容
```

已验证的处理办法是：

```bash
python -m pip install torch==2.5.1 torchaudio==2.5.1
```

或者直接运行：

```bash
python -m pip install -r requirements-windows-known-good.txt
```

简单理解：普通用户不需要 TorchCodec；如果遇到它和 FFmpeg 8 的报错，就绕开 TorchCodec，使用 `torchaudio==2.5.1` 这条稳定路径。

只有当你要把视频/音频解码成 PyTorch tensor 做二次开发时，才考虑安装 TorchCodec：

```bash
python -m pip install -r requirements-optional-torchcodec.txt
```

本 Skill 的建议是：

- 只做去人声、提取人声、降噪、封装视频：不用 TorchCodec，直接用 FFmpeg CLI。
- Windows ：先用 `winget install --id Gyan.FFmpeg -e` 安装 FFmpeg，再装 `requirements-windows-known-good.txt`。
- 已验证组合：`FFmpeg 8.1.1` + `torch==2.5.1` + `torchaudio==2.5.1`。
- 要做 PyTorch 张量级音视频处理：再单独研究 TorchCodec 与本机 FFmpeg/PyTorch 的兼容表。

## 最常用的 4 个命令

### 去掉视频里的人声

```bash
python scripts/video_audio_cleaner.py input.mp4 --mode remove-vocals
```

### 只提取视频里的人声

```bash
python scripts/video_audio_cleaner.py input.mp4 --mode extract-vocals
```

### 去背景音乐，尽量保留讲话

```bash
python scripts/video_audio_cleaner.py input.mp4 --mode clean-speech
```

### 只给录音降噪

```bash
python scripts/video_audio_cleaner.py input.wav --mode denoise
```

## 输出文件在哪里？

默认会输出到 `output/` 文件夹。

如果输入是视频，输出通常是新的视频文件，例如：

```text
output/input_clean-speech.mp4
```

如果输入是音频，输出通常是新的音频文件，例如：

```text
output/input_clean-speech.wav
```

你也可以指定输出文件夹：

```bash
python scripts/video_audio_cleaner.py input.mp4 --mode clean-speech --output-dir my_output
```

## Agent 使用方式示例

你可以这样对 Agent 说：

```text
帮我处理这个视频，去掉人声，保留背景音乐。
```

或者：

```text
这个视频背景音乐太大，我想保留说话声，帮我处理。
```

或者：

```text
我不知道该选哪个模式，你先给我菜单。
```

## 常见问题

### 运行很慢正常吗？

正常。音频分离模型比较吃算力。视频越长，处理越慢。没有 GPU 时会更慢。

### 为什么效果不是完全干净？

人声和音乐经常在同一频段重叠，模型只能尽量分离，不可能保证 100% 完美。强混响、合唱、掌声、游戏声、压缩很严重的视频都会影响效果。

### 第一次运行为什么会下载东西？

Demucs 和 DeepFilterNet 可能需要下载预训练模型。这是正常现象。

### 我只想降噪，不想改变背景音乐怎么办？

请选择 `denoise`，不要选 `remove-vocals` 或 `clean-speech`。

### 我想去背景音乐，保留讲话，应该选哪个？

优先选 `clean-speech`。

### 我想去掉歌声，保留伴奏，应该选哪个？

选 `remove-vocals`。

### Windows 上提示 TorchCodec / FFmpeg 8 报错怎么办？

优先不要装 TorchCodec。这个 Skill 的主流程不需要它。

按这个顺序处理：

```bash
python -m pip uninstall -y torchcodec
python -m pip install torch==2.5.1 torchaudio==2.5.1
python -m pip install -r requirements-windows-known-good.txt
python scripts/check_setup.py
```

前面实际处理时，`torchcodec` 与 FFmpeg 8 不兼容的问题就是通过降级 `torchaudio` 到 `2.5.1` 解决的。

### Windows 上没有 FFmpeg 怎么办？

用 PowerShell 运行：

```bash
winget install --id Gyan.FFmpeg -e
```

安装完成后重新打开 PowerShell，再运行：

```bash
ffmpeg -version
```

前面实际处理时，已通过 `winget` 安装 `FFmpeg 8.1.1` 并跑通。

## 推荐工作流

如果你不确定选哪个，可以按这个顺序判断：

1. 想去掉歌声，保留音乐：选 `remove-vocals`
2. 想只要歌声或人声：选 `extract-vocals`
3. 想保留讲话，降低背景音乐：选 `clean-speech`
4. 只是觉得录音有噪声：选 `denoise`
5. 已经处理好音频，要放回视频：选 `replace-audio`

## 注意事项

- 不建议处理特别长的视频，先截取一小段测试效果。
- 不要反复压缩同一个文件，音质会变差。
- 商业使用前请确认原视频、音乐和模型依赖的许可证。
- 这个 Skill 只提供处理流程，不保证任何版权或授权问题。
