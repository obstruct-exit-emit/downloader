
# Cross-Platform Downloader

Command-line and PyQt GUI download helper for aria2 and MEGAcmd with portable binaries, queue persistence, backend auto-selection, and real-time progress tracking.

## Highlights
- Add, pause, resume, remove, and inspect downloads from a single CLI or GUI.
- True pause/resume support for aria2 RPC jobs (GID) and process-backed jobs (PID).
- PyQt GUI frontend: add downloads, view progress, and refresh status for all backends.
- Real-time progress bar and refresh button in GUI, integrated with CLI and state file.
- Auto-select backend: HTTP/HTTPS defaults to aria2; Mega links use MEGAcmd (override with `--backend`).
- Portable binaries: `get-aria2` and `get-mega` fetch Windows-ready executables into the repo tree.
- Resilient aria2: RPC auto-start with port retry; auto-falls back to standalone aria2c (no RPC) when sockets are blocked.
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

# Launch the PyQt GUI
python downloader/gui/main_window.py
```


## GUI reference
- Add a download by entering a URL and clicking "Download".
- View all downloads in a table with progress, status, backend, and controls.
- Pause/resume supported for aria2 RPC jobs (GID) and process-backed jobs (PID).
- Remove jobs from the list, or remove and delete the downloaded file.
- Progress is tracked for all backends (aria2, Mega, direct-download) and updates to 100% when completed.
- The GUI reads the state file and uses CLI commands to show real-time status.

## CLI reference
- `add <url> [--backend aria2|mega]` — enqueue and start a download. Stores an ID; aria2 uses RPC, Mega uses `mega-get`.
- `pause <id>` — pause a download (supported for aria2 RPC jobs (GID) and process-backed jobs (PID)).
- `resume <id>` — resume a paused download (supported for aria2 RPC jobs (GID) and process-backed jobs (PID)).
- `remove <id>` — terminate a process (when tracked) and drop it from the queue.
- `status [id]` — show one download or the whole queue.
- `list` — refresh lightweight status and print the queue (same output as `status`).
- `aria2-progress <gid>` — query aria2 RPC for a specific GID’s progress.
- `aria2-list` — list active aria2 downloads via RPC.
- `get-aria2` — download and place `aria2c.exe` under `downloader/aria2_portable/` (Windows only).
- `get-mega` — download MEGAcmd installer, copy binaries to `downloader/mega_portable/MEGAcmd`, and uninstall the system copy to stay portable.
- `get-7zip` — download portable 7zr.exe to `downloader/7zip_portable/` (Windows only).
- `config show` — print current stored settings (aria2/Mega); secrets are masked.
- `config aria2 [--rpc-secret ...] [--rpc-port ...]` — set aria2 RPC secret/port.
- `config mega [--email ...] [--password ...]` — set Mega credentials.
- `--aria2-direct-fallback / --no-aria2-direct-fallback` — global flags to enable/disable direct download fallback (defaults to env/disabled). Direct fallback is now the last resort; standalone aria2c is preferred when RPC sockets are blocked.

Run `python -m downloader.cli --help` for the latest options and descriptions.

## Downloads, state, and locations
- Download directory: `downloads/` at the project root (auto-created).
- State file: `.downloader_state.json` at the project root (queue + history).
- Portable aria2 binary (Windows): `downloader/aria2_portable/aria2c.exe` after `get-aria2`.
- Portable MEGAcmd bundle (Windows): `downloader/mega_portable/MEGAcmd/` after `get-mega`.
- Portable 7-Zip (Windows): `downloader/7zip_portable/7zr.exe` after `get-7zip`.
- Config file: `.downloader_config.json` in the user config directory if available (falls back to project root) for aria2 RPC secret/port and Mega credentials; `config show` masks secrets. Port is validated (1-65535) on set.

## Fallback behavior
- Default flow: start/connect to aria2 RPC, trying ports 6800, 6880, 6999, then an ephemeral port.
- If RPC binding or calls fail with socket permission errors (e.g., WinError 10013), the CLI automatically switches to standalone aria2c (no RPC) and continues the download, tracking it by PID.
- Optional direct-download fallback: enable per run with `--aria2-direct-fallback` or via env `ARIA2_DIRECT_FALLBACK=1` (true/yes/on). This is only used when both RPC and standalone aria2c are unavailable. Jobs completed this way show `GID=direct-download`.

## Backend notes
- aria2
	- Uses RPC on `http://localhost:6800/jsonrpc` with secret `secret123` by default.
	- CLI auto-starts an aria2 RPC daemon if not already reachable and points downloads to `downloads/`.
	- Progress helpers: `aria2-progress` and `aria2-list` call RPC directly.
	- RPC startup will retry alternate local ports (6800, 6880, 6999, then ephemeral) if binding/auth fails; if sockets are blocked by permissions, the CLI falls back to standalone aria2c (no RPC).
- MEGAcmd
	- Uses `mega-get` (or the `.bat` wrapper) for downloads.
	- Authenticate once with `mega-login <email> <password>` using the bundled shell if needed; credentials are managed by MEGAcmd.

## Troubleshooting
- aria2 RPC not reachable: ensure port 6800 is free. The CLI will auto-try alternate ports; if sockets are blocked, it will switch to standalone aria2c. If both fail, rerun `get-aria2`, check firewall rules, or run with `--aria2-direct-fallback` as a last resort.
- Mega commands fail: open `downloader/mega_portable/MEGAcmd/mega-login.bat` (or run via cmd) to sign in; verify files exist under `downloader/mega_portable/MEGAcmd`.
- Reset state: stop downloads, then delete `.downloader_state.json` and re-run commands to start fresh.


## Roadmap
- True pause/resume support for aria2 RPC jobs (GID) and process-backed jobs (PID).
- Rich progress output and notifications.
- GUI frontend (PyQt):
	- Add downloads via URL
	- Table view for all downloads with progress, status, backend, and controls
	- Pause/resume/remove for all supported jobs
	- Remove and delete file option
	- Progress bar and refresh button for all backends
	- Reads state file and uses CLI for real-time updates
	- Auto-refresh, downloads list, settings panel

