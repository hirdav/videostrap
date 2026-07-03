# 🎬 VideoStrap — Video to Frames for LLMs & AI Video Tools

**Turn any video into reference images — locally, in seconds.**

Multimodal LLMs (Claude, GPT-4o, Gemini) and AI video generators (Runway, Pika, Kling, Luma, Sora) all need **reference images** — but they don't accept raw video, or they need specific frames to work from. VideoStrap bridges that gap: drop in a video, get clean, evenly-sampled frames out.

Runs **100% locally**. No cloud. No accounts. No upload limits. Your footage never leaves your machine.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-win%20%7C%20mac%20%7C%20linux-lightgrey.svg)

---

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

```bash
# 1. Clone
git clone https://github.com/<your-username>/videostrap.git
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

## Example: frames for an LLM prompt

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
  static/index.html   # Single-file frontend (zero build step)
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

## Notes

- The uploaded video is deleted from disk as soon as extraction starts
- Frames live in `data/outputs/<job_id>/` until you clean up
- Default port is **5050** — change it at the bottom of `app.py`
- This is a local tool; don't expose it to the public internet as-is

## Contributing

Issues and PRs welcome! Ideas that would fit well:

- Scene-change detection mode (extract only on cuts)
- Timestamp overlay / filename with timecodes
- Batch mode for multiple videos
- Contact-sheet (grid montage) export

## License

[MIT](LICENSE) — use it, fork it, ship it.

---

**If VideoStrap saved you time, a ⭐ helps others find it.**
