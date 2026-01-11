# Cross-Platform Downloader

A highly functional, cross-platform download utility with CLI and GUI (future) frontends for aria2 and Mega.

## Features
- Add, pause, resume, remove downloads
- Automatic backend selection (aria2 or Mega) based on URL
- Portable: auto-downloads aria2/megacmd if not present
- Modular core for easy GUI integration

## Usage

```sh
python -m downloader.cli add <url> [--backend aria2|mega]
python -m downloader.cli list
python -m downloader.cli pause <id>
python -m downloader.cli resume <id>
python -m downloader.cli remove <id>
python -m downloader.cli status [id]
```

## Requirements
- Python 3.7+
- aria2c and/or megacmd (auto-downloaded if missing)

## Roadmap
- Download queue persistence
- Progress tracking
- GUI frontend (PySide6/PyQt5)
- More backends

