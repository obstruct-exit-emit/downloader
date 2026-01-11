# Cross-Platform Download Utility: Project Plan

## 1. Project Requirements and Features

### Supported Backends
- aria2 (multi-protocol downloader)
- Mega (cloud storage and downloads)
- (Optional: add more in future)

### Core Features
- Add, pause, resume, and remove downloads
- Download queue management
- Progress tracking and notifications
- Support for multiple simultaneous downloads
- Backend selection per download
- Error handling and retry logic
- Download history/log
- Settings for backend configuration (e.g., aria2 RPC, Mega credentials)

### UI/UX Expectations
- Simple, modern, and intuitive interface
- Add download via URL or file
- View and manage active/completed downloads
- Settings panel for backend configuration
- Cross-platform look and feel

### Platform Support
- Windows
- macOS
- Linux

---


## 2. Tech Stack and Architecture
- Programming language(s): Python 3.x (best cross-platform, runs without compiling)
- Initial focus: Fully functional CLI utility
- CLI framework: argparse or click for robust command-line interface
- Code structure: Modular, with all core logic in reusable modules, so both CLI and GUI can call the same functions/classes directly
- Backend integration: Python subprocess module to call aria2/mega CLI, or use Python libraries/wrappers if available
- Packaging/build tools: requirements.txt for dependencies; PyInstaller (optional, for standalone executables if needed)
- GUI (future): PySide6 (Qt for Python) or PyQt5 (native look and feel on all platforms), implemented as a frontend that directly uses the same core logic as the CLI (no separate instances or daemons needed)

---


## 3. CLI and UI Mockups / User Flow

### CLI User Flow (MVP)
- Add download: `downloader add <url> [options]`
- List downloads: `downloader list`
- Pause/resume/remove: `downloader pause|resume|remove <id>`
- View progress: `downloader status <id>`
- Watch live progress: `downloader status <id> --follow` or `downloader watch`
- Configure backends: `downloader config [aria2|mega] [options]`; show current config: `downloader config show`

### Future GUI User Flow (to be designed)

---

## 4. Backend Integration Plan

### aria2
- Primary: use aria2c via RPC (aria2c --enable-rpc) for better control; fallback to subprocess CLI if RPC unavailable.
- Detect aria2c availability at runtime. If not found, offer to auto-download a portable version to the program directory (user prompt or CLI flag: --fetch-backend). Use official binaries for each OS/arch. Always prefer local binaries in the program directory before searching system PATH.
- Map core operations to RPC/CLI: add URI, pause, unpause, remove, query status/progress.

### Mega
- Use megacmd (mega-get, mega-login, etc.) via subprocess; detect presence. If not found, offer to auto-download a portable version to the program directory (user prompt or CLI flag: --fetch-backend). Use official binaries for each OS/arch. Always prefer local binaries in the program directory before searching system PATH.
- Store Mega credentials/tokens securely in config (avoid plaintext where possible; at minimum, file perms 600 on Unix, readable by user only on Windows).

### Abstraction Layer
- backends.py exposes a uniform interface (add, pause, resume, remove, status) regardless of provider.
- Each backend implements capability detection so CLI/GUI can report what is available and why.
- Backend selection rules:
	- Mega: URLs matching mega:// or https://mega.nz/... (including file/folder patterns) route to the Mega backend by default.
	- aria2: default for http/https, ftp/sftp, and magnet links (magnet:?xt=...).
	- Future backends: add pattern-based routing in a single map for maintainability.
- Allow explicit override via CLI flag (e.g., --backend mega|aria2) and via config default backend.

---


## 5. Core Logic Implementation

### Modular Core Structure
- All download management logic will be implemented in reusable Python modules (e.g., downloader/core/manager.py, downloader/core/backends.py).
- Both CLI and GUI will import and use these modules directly.
- No business logic in CLI or GUI layers—only user interaction and presentation.

#### Example Core Modules
- manager.py: Handles download queue, state, and operations (add, pause, resume, remove, status)
- backends.py: Abstraction layer for different downloaders (aria2, mega, etc.)
- config.py: Handles configuration and persistence
- utils.py: Shared utilities (e.g., progress formatting, error handling)

#### Persistence and IDs
- Config and state stored in user config dir (e.g., platformdirs) using JSON or TOML; queue/history persisted to disk.
- Download IDs: generate stable UUIDs; backend-specific IDs mapped internally.

### Benefits
- Ensures CLI and GUI always operate on the same data and logic
- Simplifies maintenance and future feature additions
- Enables easy testing of core logic without UI dependencies

---

## 6. GUI Implementation (to be detailed)

---

## 7. Testing Plan
- Unit tests for core modules (manager, backends abstraction, config, utils).
- Integration tests against aria2 (RPC and CLI fallback) and megacmd where available; otherwise mock subprocess calls.
- CLI smoke tests for primary commands (add/list/status/watch/pause/resume/remove/config).
- Cross-platform matrix (Windows/macOS/Linux) for critical paths.

---

## 8. Packaging and Distribution
- Source-first: pip install from repo with requirements.txt.
- Optional binaries: PyInstaller bundles per platform for users without Python.
- Document external dependencies (aria2c, megacmd) and provide install guidance per OS.

