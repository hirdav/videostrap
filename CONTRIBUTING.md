# Contributing to VideoStrap

Thanks for your interest in improving VideoStrap! This is a small, focused tool, so the bar for contributing is low — bug fixes, docs improvements, and small features are all welcome.

## Getting set up

```bash
git clone https://github.com/hirdav/videostrap.git
cd videostrap
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5050` and confirm the app loads before making changes.

## Making a change

1. Open an issue first for anything non-trivial (new modes, engine changes, UI redesigns) so we can align on the approach before you invest time.
2. Fork the repo and create a branch off `master`: `git checkout -b fix/short-description`.
3. Keep changes focused — one feature or fix per pull request.
4. Match the existing style:
   - `app.py`: plain Flask, no new frameworks/ORMs; keep the in-memory job model unless the issue says otherwise.
   - `static/index.html`: stays a single-file, zero-build-step frontend — please don't introduce a build pipeline or framework.
5. Test manually against a few real video files (different container formats if you touch extraction logic) and both engines (`ffmpeg` and `opencv`) if your change affects extraction.
6. Update `README.md` if you change behavior, add an API field, or add a mode/format.

## Pull requests

- Describe **what** changed and **why** in the PR description.
- Reference the related issue (`Fixes #123`) if there is one.
- Keep the diff minimal — avoid unrelated formatting or refactors bundled with a feature/fix.
- CI runs a basic syntax/lint check on `app.py`; make sure it's green before requesting review.

## Reporting bugs

Please use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

- OS and Python version
- Whether you're using the FFmpeg or OpenCV engine
- Video format/codec, if relevant
- Steps to reproduce and what you expected instead

## Feature requests

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml). Check the Roadmap section in `README.md` first — your idea might already be tracked there.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be kind, be constructive.
