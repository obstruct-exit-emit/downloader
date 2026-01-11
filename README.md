# Cross-Platform Downloader

Command-line download helper for aria2 and MEGAcmd with portable binaries, queue persistence, and backend auto-selection.

## Highlights
- Add, pause, resume, remove, and inspect downloads from a single CLI.
- Auto-select backend: HTTP/HTTPS defaults to aria2; Mega links use MEGAcmd (override with `--backend`).
- Portable binaries: `get-aria2` and `get-mega` fetch Windows-ready executables into the repo tree.
- Persistent queue: `.downloader_state.json` keeps IDs/history across runs.

## Prerequisites
- Python 3.8+ recommended.
- Windows: `get-aria2` and `get-mega` download portable binaries automatically.
- Other platforms: provide `aria2c` or `mega-get` in PATH (portable helpers are Windows-only right now).

## Setup
```sh
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Quick start
```sh
# (Windows) fetch portable aria2
python -m downloader.cli get-aria2

# Add a download (auto-selects aria2 unless URL is a mega link)
python -m downloader.cli add https://example.com/file.iso

# List queue
python -m downloader.cli list

# Show detailed status for one ID
python -m downloader.cli status <id>

# Remove a job
python -m downloader.cli remove <id>
```

## CLI reference
- `add <url> [--backend aria2|mega]` — enqueue and start a download. Stores an ID; aria2 uses RPC, Mega uses `mega-get`.
- `pause <id>` — suspend a process-backed download (best-effort for Mega; aria2 pause not implemented yet).
- `resume <id>` — resume a paused process (best-effort for Mega; aria2 resume not implemented yet).
- `remove <id>` — terminate a process (when tracked) and drop it from the queue.
- `status [id]` — show one download or the whole queue.
- `list` — refresh lightweight status and print the queue (same output as `status`).
- `aria2-progress <gid>` — query aria2 RPC for a specific GID’s progress.
- `aria2-list` — list active aria2 downloads via RPC.
- `get-aria2` — download and place `aria2c.exe` under `downloader/` (Windows only).
- `get-mega` — download MEGAcmd installer, copy binaries to `downloader/mega_portable/MEGAcmd`, and uninstall the system copy to stay portable.

Run `python -m downloader.cli --help` for the latest options and descriptions.

## Downloads, state, and locations
- Download directory: `downloads/` at the project root (auto-created).
- State file: `.downloader_state.json` at the project root (queue + history).
- Portable aria2 binary (Windows): `downloader/aria2c.exe` after `get-aria2`.
- Portable MEGAcmd bundle (Windows): `downloader/mega_portable/MEGAcmd/` after `get-mega`.

## Backend notes
- aria2
	- Uses RPC on `http://localhost:6800/jsonrpc` with secret `secret123` by default.
	- CLI auto-starts an aria2 RPC daemon if not already reachable and points downloads to `downloads/`.
	- Progress helpers: `aria2-progress` and `aria2-list` call RPC directly.
- MEGAcmd
	- Uses `mega-get` (or the `.bat` wrapper) for downloads.
	- Authenticate once with `mega-login <email> <password>` using the bundled shell if needed; credentials are managed by MEGAcmd.

## Troubleshooting
- aria2 RPC not reachable: ensure port 6800 is free; rerun `get-aria2` to refresh the binary; delete any stray aria2 processes and retry.
- Mega commands fail: open `downloader/mega_portable/MEGAcmd/mega-login.bat` (or run via cmd) to sign in; verify files exist under `downloader/mega_portable/MEGAcmd`.
- Reset state: stop downloads, then delete `.downloader_state.json` and re-run commands to start fresh.

## Roadmap
- Pause/resume support for aria2 RPC jobs.
- Rich progress output and notifications.
- GUI frontend (Qt/PySide).

