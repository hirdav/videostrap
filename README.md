# 🎬 VideoStrap — Video to Frames for LLMs & AI Video Tools

**Turn any video into reference images — locally, in seconds.**

Multimodal LLMs (Claude, GPT-4o, Gemini) and AI video generators (Runway, Pika, Kling, Luma, Sora) all need **reference images** — but they don't accept raw video, or they need specific frames to work from. VideoStrap bridges that gap: drop in a video, get clean, evenly-sampled frames out.

Runs **100% locally**. No cloud. No accounts. No upload limits. Your footage never leaves your machine.

[![CI](https://github.com/hirdav/videostrap/actions/workflows/ci.yml/badge.svg)](https://github.com/hirdav/videostrap/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-win%20%7C%20mac%20%7C%20linux-lightgrey.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## Table of contents

- [Why?](#why)
- [Features](#features)
- [Quick start](#quick-start)
- [Example: frames for an LLM prompt](#example-frames-for-an-llm-prompt)
- [How it works](#how-it-works)
- [API](#api)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Why?

| You want to… | How VideoStrap helps |
|---|---|
| **Ask an LLM about a video** | Most vision models take images, not video. Extract N evenly-spaced frames and send those instead. |
| **Generate video from a reference** | Image-to-video tools (Runway, Pika, Kling, Luma) need a starting frame. Pull the exact frame you want. |
| **Build a style/character reference set** | Sample a whole video into a frame grid to feed consistency workflows (LoRA training, IP-Adapter, character sheets). |
| **Create vision datasets** | Batch-extract frames at fixed intervals for labeling, fine-tuning, or evals. |
| **Storyboard existing footage** | Get a compact visual summary of a long video at a glance. |

## Features

- 🖱️ **Drag & drop web UI** — no command-line flags to memorize
- ⏱️ **Three extraction modes**
  - **Every N seconds** — e.g. 1 frame per second
  - **Every N frames** — e.g. every 30th frame
  - **Total N frames** — exactly N frames, evenly distributed (perfect for LLM context limits)
- 🖼️ **JPEG or PNG output** with adjustable quality
- ⚡ **Two engines**: FFmpeg (fast, any codec) with automatic OpenCV fallback
- 📊 **Live progress bar** while extracting
- 📦 **Download frames individually or as a ZIP**
- 🔒 **Private by design** — everything happens on `localhost`; uploads are deleted right after extraction
- 🎞️ Supports MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V

## Quick start

**Requirements:** Python 3.9+, pip, and (recommended) FFmpeg on your `PATH`.

```bash
# 1. Clone
git clone https://github.com/hirdav/videostrap.git
cd videostrap

# 2. Install Python deps
pip install -r requirements.txt

# 3. Install FFmpeg (recommended — OpenCV fallback works without it)
# macOS:            brew install ffmpeg
# Ubuntu/Debian:    sudo apt install ffmpeg
# Windows:          winget install ffmpeg   (or https://ffmpeg.org/download.html)

# 4. Run
python app.py
```

Open **http://localhost:5050** — drop in a video, pick a mode, hit Extract.

> Tip: a Python virtual environment (`python -m venv venv && source venv/bin/activate`) keeps these dependencies isolated from the rest of your system.

## Example: frames for an LLM prompt-

Want to ask Claude or GPT-4o *"what happens in this video?"*

1. Set mode to **Total N frames** → `10`
2. Format **JPEG**, quality ~80 (keeps token cost down)
3. Extract, download the ZIP
4. Attach the frames to your prompt: *"These are 10 evenly-spaced frames from a video. Describe what happens."*

Want a **starting frame for image-to-video** generation? Use **Every N seconds** → `1`, preview the grid in your browser, and download the single frame that best matches your shot.

## How it works

```
videostrap/
  app.py              # Flask backend — upload, extract, progress, download
  static/index.html    # Single-file frontend (zero build step)
  requirements.txt
  data/
    uploads/          # Temp video storage (deleted after extraction starts)
    outputs/<job_id>/ # Extracted frames, one folder per job
```

- **FFmpeg engine** (default): builds an `fps`/`select` filter per mode — fastest and handles any codec
- **OpenCV engine** (fallback): pure Python frame stepping — works when FFmpeg isn't installed
- Each job gets an isolated output directory; a cleanup endpoint removes it when you're done

## API

The UI is just a client for a small JSON API — script it if you like:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/upload` | POST | Upload video (`multipart`, field `video`) → `job_id` + video info |
| `/api/extract` | POST | Start extraction: `{job_id, mode, value, format, quality, engine}` |
| `/api/status/<job_id>` | GET | Poll progress: `{status, extracted, expected, files}` |
| `/api/download-zip/<job_id>` | GET | All frames as a ZIP |
| `/api/download/<job_id>/<file>` | GET | Single frame |
| `/api/cleanup/<job_id>` | DELETE | Delete job output |

Modes: `interval_sec` · `interval_frame` · `total_frames` — formats: `jpg` · `png` — engines: `ffmpeg` · `opencv`

<details>
<summary>Example: scripting the API with curl</summary>

```bash
# 1. Upload a video
curl -s -F "video=@clip.mp4" http://localhost:5050/api/upload
# → {"job_id": "...", "info": {...}}

# 2. Start extraction (10 evenly-spaced JPEG frames)
curl -s -X POST http://localhost:5050/api/extract \
  -H "Content-Type: application/json" \
  -d '{"job_id":"<job_id>","mode":"total_frames","value":10,"format":"jpg","quality":85,"engine":"ffmpeg"}'

# 3. Poll status
curl -s http://localhost:5050/api/status/<job_id>

# 4. Download the ZIP once status is "done"
curl -s -o frames.zip http://localhost:5050/api/download-zip/<job_id>
```

</details>

## Configuration

VideoStrap has no config file by design — everything is set per-request through the UI or API. A couple of things worth knowing:

- Default port is **5050** — change it at the bottom of `app.py` (`app.run(..., port=5050)`)
- Uploads and outputs live under `./data/` (git-ignored, safe to delete when the app isn't running)
- Set `engine` to `opencv` in the API/UI if FFmpeg isn't installed or isn't on `PATH`

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ffmpeg: command not found` | FFmpeg isn't installed or not on `PATH` — install it (see Quick start) or switch the engine to **OpenCV** in the UI |
| Upload fails with "Unsupported file type" | Container/extension isn't in the supported list (MP4, MOV, AVI, MKV, WebM, FLV, WMV, M4V) — try re-exporting/re-muxing the file |
| Extraction seems stuck at 0% | Very large files can take a moment to probe — check the terminal running `app.py` for FFmpeg/OpenCV errors |
| Port 5050 already in use | Another process is using it — stop it, or change the port in `app.py` |
| Frames look corrupted/black | Some codecs aren't fully supported by the OpenCV fallback — install FFmpeg for broader codec coverage |

## FAQ

**Does any of my video leave my machine?**
No. VideoStrap runs entirely on `localhost` — there's no network call, cloud upload, or telemetry.

**Can I run this on a server and share it with others?**
It's built as a local, single-user tool (in-memory job store, no auth). Don't expose it directly to the public internet — put it behind your own auth/proxy if you need remote access.

**Why do I get slightly different frame counts than requested?**
Frame extraction depends on the video's actual FPS/keyframes; `total_frames` mode targets an even distribution but the exact count can vary by ±1 depending on rounding.

## Roadmap

Ideas that would fit well — see [CONTRIBUTING.md](CONTRIBUTING.md) if you'd like to pick one up:

- Scene-change detection mode (extract only on cuts)
- Timestamp overlay / filename with timecodes
- Batch mode for multiple videos
- Contact-sheet (grid montage) export

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Contributing

Issues and PRs welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines before opening a pull request.

## Security

Found a security issue? Please see [SECURITY.md](SECURITY.md) for how to report it responsibly.

## License

[MIT](LICENSE) — use it, fork it, ship it.

---

**If VideoStrap saved you time, a ⭐ helps others find it.**
