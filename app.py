"""
Video to Images - Local Tool
Flask backend that handles video upload and frame extraction.
Supports three extraction modes:
  - Every N seconds (time interval)
  - Every N frames (frame interval)
  - Total N frames (evenly distributed)
Extraction engines: FFmpeg (default, fastest) or OpenCV (fallback)
"""

import os
import re
import json
import uuid
import shutil
import subprocess
import threading
import time
from pathlib import Path

import cv2
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder="static")

# All uploads and outputs live under ./data/
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

for d in [UPLOAD_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# In-memory job store: {job_id: {...}}
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_video_info(path: Path) -> dict:
    """Return duration (seconds), fps, total frame count via OpenCV."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return {
        "fps": round(fps, 3),
        "total_frames": total_frames,
        "duration": round(duration, 2),
        "width": width,
        "height": height,
    }


def update_job(job_id: str, **kwargs):
    with jobs_lock:
        jobs[job_id].update(kwargs)


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------

def extract_with_ffmpeg(video_path: Path, out_dir: Path, mode: str, value: float,
                        fmt: str, quality: int, job_id: str):
    """
    Use FFmpeg for extraction. Fastest and most codec-compatible.
    mode: 'interval_sec' | 'interval_frame' | 'total_frames'
    """
    info = get_video_info(video_path)
    fps = info["fps"]
    total = info["total_frames"]
    duration = info["duration"]

    # Build the select filter expression
    if mode == "interval_sec":
        # Extract one frame every `value` seconds
        vf = f"fps=1/{value}"
        expected = int(duration / value) + 1
    elif mode == "interval_frame":
        # Extract every Nth frame
        n = max(1, int(value))
        vf = f"select='not(mod(n\\,{n}))',setpts=N/FRAME_RATE/TB"
        expected = total // n
    elif mode == "total_frames":
        # Evenly distribute N frames over duration
        n = int(value)
        interval = duration / n if n > 0 else 1
        vf = f"fps=1/{interval:.6f}"
        expected = n
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Quality flag depends on format
    if fmt == "jpg":
        quality_flag = ["-q:v", str(max(1, min(31, 32 - quality // 3)))]  # ffmpeg: 1=best, 31=worst
        ext = "jpg"
    elif fmt == "png":
        quality_flag = ["-compression_level", str(9 - quality // 12)]
        ext = "png"
    else:
        quality_flag = ["-q:v", "2"]
        ext = "jpg"

    out_pattern = str(out_dir / f"frame_%05d.{ext}")

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", vf,
        *quality_flag,
        "-vsync", "vfr",
        out_pattern,
        "-y",
    ]

    update_job(job_id, status="extracting", expected=expected, extracted=0)

    proc = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )

    # Poll output directory to track progress
    while proc.poll() is None:
        extracted = len(list(out_dir.glob(f"*.{ext}")))
        update_job(job_id, extracted=extracted)
        time.sleep(0.3)

    proc.wait()
    extracted = len(list(out_dir.glob(f"*.{ext}")))

    if proc.returncode != 0:
        err = proc.stderr.read() if proc.stderr else "FFmpeg error"
        raise RuntimeError(f"FFmpeg failed: {err}")

    return extracted


def extract_with_opencv(video_path: Path, out_dir: Path, mode: str, value: float,
                        fmt: str, quality: int, job_id: str):
    """
    OpenCV fallback extractor. Slower but works without FFmpeg.
    """
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Determine which frame indices to extract
    if mode == "interval_sec":
        step = max(1, int(fps * value))
        indices = set(range(0, total, step))
    elif mode == "interval_frame":
        step = max(1, int(value))
        indices = set(range(0, total, step))
    elif mode == "total_frames":
        n = max(1, int(value))
        indices = set(int(i * total / n) for i in range(n))
    else:
        raise ValueError(f"Unknown mode: {mode}")

    expected = len(indices)
    update_job(job_id, status="extracting", expected=expected, extracted=0)

    ext = "jpg" if fmt == "jpg" else "png"
    encode_params = []
    if fmt == "jpg":
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    elif fmt == "png":
        encode_params = [cv2.IMWRITE_PNG_COMPRESSION, max(0, min(9, 9 - quality // 12))]

    frame_num = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_num in indices:
            out_path = out_dir / f"frame_{saved:05d}.{ext}"
            cv2.imwrite(str(out_path), frame, encode_params)
            saved += 1
            update_job(job_id, extracted=saved)
        frame_num += 1

    cap.release()
    return saved


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def run_extraction(job_id: str, video_path: Path, out_dir: Path,
                   mode: str, value: float, fmt: str, quality: int, engine: str):
    try:
        if engine == "ffmpeg":
            count = extract_with_ffmpeg(video_path, out_dir, mode, value, fmt, quality, job_id)
        else:
            count = extract_with_opencv(video_path, out_dir, mode, value, fmt, quality, job_id)

        # Build file list for download manifest
        ext = "jpg" if fmt == "jpg" else "png"
        files = sorted([f.name for f in out_dir.glob(f"*.{ext}")])
        update_job(job_id, status="done", extracted=count, files=files)

    except Exception as e:
        update_job(job_id, status="error", error=str(e))
    finally:
        # Clean up uploaded video to save space
        try:
            video_path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    f = request.files["video"]
    if not f.filename or not allowed_video(f.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    job_id = str(uuid.uuid4())
    ext = Path(f.filename).suffix.lower()
    video_path = UPLOAD_DIR / f"{job_id}{ext}"
    f.save(str(video_path))

    try:
        info = get_video_info(video_path)
    except Exception as e:
        video_path.unlink(missing_ok=True)
        return jsonify({"error": f"Could not read video: {e}"}), 400

    with jobs_lock:
        jobs[job_id] = {
            "status": "uploaded",
            "video_path": str(video_path),
            "info": info,
            "extracted": 0,
            "expected": 0,
            "files": [],
        }

    return jsonify({"job_id": job_id, "info": info})


@app.route("/api/extract", methods=["POST"])
def start_extraction():
    data = request.json or {}
    job_id = data.get("job_id")
    mode = data.get("mode", "interval_sec")      # interval_sec | interval_frame | total_frames
    value = float(data.get("value", 1.0))
    fmt = data.get("format", "jpg")              # jpg | png
    quality = int(data.get("quality", 85))       # 1-100
    engine = data.get("engine", "ffmpeg")        # ffmpeg | opencv

    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "Unknown job ID"}), 404
    if job["status"] not in ("uploaded", "done", "error"):
        return jsonify({"error": "Job already running"}), 409

    video_path = Path(job["video_path"])
    if not video_path.exists():
        return jsonify({"error": "Video file missing - please re-upload"}), 400

    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clear previous output if re-running
    for old in out_dir.iterdir():
        old.unlink()

    update_job(job_id, status="queued", extracted=0, expected=0, files=[])

    thread = threading.Thread(
        target=run_extraction,
        args=(job_id, video_path, out_dir, mode, value, fmt, quality, engine),
        daemon=True,
    )
    thread.start()

    return jsonify({"status": "started"})


@app.route("/api/status/<job_id>")
def job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job"}), 404

    safe = {k: v for k, v in job.items() if k != "video_path"}
    return jsonify(safe)


@app.route("/api/download/<job_id>/<filename>")
def download_frame(job_id: str, filename: str):
    # Sanitize filename to prevent path traversal
    filename = Path(filename).name
    if not re.match(r'^frame_\d+\.(jpg|png)$', filename):
        return jsonify({"error": "Invalid filename"}), 400
    out_dir = OUTPUT_DIR / job_id
    return send_from_directory(str(out_dir), filename, as_attachment=True)


@app.route("/api/download-zip/<job_id>")
def download_zip(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "Job not ready"}), 400

    out_dir = OUTPUT_DIR / job_id
    zip_path = DATA_DIR / f"{job_id}.zip"

    shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(out_dir))

    def generate():
        with open(zip_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk
        zip_path.unlink(missing_ok=True)

    return Response(
        generate(),
        mimetype="application/zip",
        headers={"Content-Disposition": f"attachment; filename=frames_{job_id[:8]}.zip"},
    )


@app.route("/api/preview/<job_id>/<filename>")
def preview_frame(job_id: str, filename: str):
    filename = Path(filename).name
    if not re.match(r'^frame_\d+\.(jpg|png)$', filename):
        return jsonify({"error": "Invalid filename"}), 400
    out_dir = OUTPUT_DIR / job_id
    return send_from_directory(str(out_dir), filename)


@app.route("/api/cleanup/<job_id>", methods=["DELETE"])
def cleanup_job(job_id: str):
    out_dir = OUTPUT_DIR / job_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    with jobs_lock:
        jobs.pop(job_id, None)
    return jsonify({"status": "cleaned"})


if __name__ == "__main__":
    print("\n  Video to Images - Local Tool")
    print("  Open http://localhost:5050 in your browser\n")
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
