# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository documentation: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue/PR templates, and a CI syntax-check workflow.

## [1.0.0] - 2026-07-17

### Added

- Drag-and-drop web UI for extracting frames from video
- Three extraction modes: every N seconds, every N frames, and total N frames (evenly distributed)
- JPEG and PNG output with adjustable quality
- FFmpeg extraction engine with automatic OpenCV fallback
- Live progress reporting during extraction
- Per-frame and ZIP download endpoints
- Automatic cleanup of uploaded video after extraction starts, plus a manual job-cleanup endpoint
