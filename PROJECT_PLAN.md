# Cross-Platform Download Utility: Project Plan

## 1. Project Requirements and Features

### Supported Backends
- aria2 (multi-protocol downloader) **(Done: RPC + portable fetch)**
- Mega (cloud storage and downloads) **(Done: portable fetch + basic add)**
- (Optional: add more in future)

### Core Features
- Add, pause, resume, and remove downloads **(Done in CLI/manager)**
- Download queue management **(Done: persisted queue/history file)**
- Progress tracking and notifications **(Partial: aria2 progress via RPC; no notifications yet)**
- Support for multiple simultaneous downloads **(Partial: aria2 supports concurrent RPC jobs)**
- Backend selection per download **(Done: auto + --backend override)**
- Error handling and retry logic **(Partial: fallback direct-download optional, port retry)**
- Download history/log **(Partial: queue/history persisted; no reporting UI)**
- Settings for backend configuration (e.g., aria2 RPC, Mega credentials) **(Done: config CLI + .downloader_config.json for aria2 secret/port and Mega creds)**

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
- Add download: `downloader add <url> [options]` **(Done)**
- List downloads: `downloader list` **(Done)**
- Pause/resume/remove: `downloader pause|resume|remove <id>` **(Done)**
- View progress: `downloader status <id>` **(Done)**
- Watch live progress: `downloader status <id> --follow` or `downloader watch` **(Not started)**
- Configure backends: `downloader config [aria2|mega] [options]`; show current config: `downloader config show` **(Done: config CLI implemented)**

### Future GUI User Flow (to be designed)

---

## 4. Backend Integration Plan

### aria2
- Primary: use aria2c via RPC (aria2c --enable-rpc) for better control; fallback to subprocess CLI if RPC unavailable. **(Done: RPC + optional direct-download fallback)**
- Detect aria2c availability at runtime. If not found, offer to auto-download a portable version to the program directory (user prompt or CLI flag: --fetch-backend). Use official binaries for each OS/arch. Always prefer local binaries in the program directory before searching system PATH. **(Done: get-aria2 portable for Windows, search order prefers portable)**
- Map core operations to RPC/CLI: add URI, pause, unpause, remove, query status/progress. **(Partial: add/status; pause/resume/remove via manager only for proc-based jobs)**

### Mega
- Use megacmd (mega-get, mega-login, etc.) via subprocess; detect presence. If not found, offer to auto-download a portable version to the program directory (user prompt or CLI flag: --fetch-backend). Use official binaries for each OS/arch. Always prefer local binaries in the program directory before searching system PATH. **(Done: get-mega portable for Windows; basic add)**
- Store Mega credentials/tokens securely in config (avoid plaintext where possible; at minimum, file perms 600 on Unix, readable by user only on Windows). **(Not started)**

### Abstraction Layer
- backends.py exposes a uniform interface (add, pause, resume, remove, status) regardless of provider. **(Done: interface present; pause/resume not fully implemented per backend)**
- Each backend implements capability detection so CLI/GUI can report what is available and why. **(Not started: detection/reporting)**
- Backend selection rules:
	- Mega: URLs matching mega:// or https://mega.nz/... (including file/folder patterns) route to the Mega backend by default. **(Done)**
	- aria2: default for http/https, ftp/sftp, and magnet links (magnet:?xt=...). **(Partial: http/https implemented)**
	- Future backends: add pattern-based routing in a single map for maintainability. **(Not started)**
- Allow explicit override via CLI flag (e.g., --backend mega|aria2) and via config default backend. **(Done for CLI override; config not started)**

---


## 5. Core Logic Implementation

### Modular Core Structure
- All download management logic will be implemented in reusable Python modules (e.g., downloader/core/manager.py, downloader/core/backends.py). **(Done)**
- Both CLI and GUI will import and use these modules directly. **(Done for CLI; GUI future)**
- No business logic in CLI or GUI layers—only user interaction and presentation. **(Mostly done; CLI contains portable download helpers)**

#### Example Core Modules
- manager.py: Handles download queue, state, and operations (add, pause, resume, remove, status)
- backends.py: Abstraction layer for different downloaders (aria2, mega, etc.)
- config.py: Handles configuration and persistence
- utils.py: Shared utilities (e.g., progress formatting, error handling)

#### Persistence and IDs
- Config and state stored in user config dir (e.g., platformdirs) using JSON or TOML; queue/history persisted to disk. **(Partial: JSON state at project root; config not implemented)**
- Download IDs: generate stable UUIDs; backend-specific IDs mapped internally. **(Done)**

### Benefits
- Ensures CLI and GUI always operate on the same data and logic
- Simplifies maintenance and future feature additions
- Enables easy testing of core logic without UI dependencies

---

## 6. GUI Implementation (to be detailed)

---

## 7. Testing Plan
- Unit tests for core modules (manager, backends abstraction, config, utils). **(Not started)**
- Integration tests against aria2 (RPC and CLI fallback) and megacmd where available; otherwise mock subprocess calls. **(Not started)**
- CLI smoke tests for primary commands (add/list/status/watch/pause/resume/remove/config). **(Not started)**
- Cross-platform matrix (Windows/macOS/Linux) for critical paths. **(Not started)**

---

## 8. Packaging and Distribution
- Source-first: pip install from repo with requirements.txt. **(Partial: requirements.txt present)**
- Optional binaries: PyInstaller bundles per platform for users without Python. **(Not started)**
- Document external dependencies (aria2c, megacmd) and provide install guidance per OS. **(Partial: README covers portable fetch)**

