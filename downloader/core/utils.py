# Shared utilities (progress formatting, paths)
from pathlib import Path

# Project root is two levels up from this file (core -> downloader -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
STATE_PATH = PROJECT_ROOT / ".downloader_state.json"


def ensure_download_dir() -> Path:
    """Create the downloads directory if missing and return its path."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return DOWNLOADS_DIR


def format_progress(percent: float) -> str:
    # Format progress for display with two decimals
    return f"{percent:.2f}%"
