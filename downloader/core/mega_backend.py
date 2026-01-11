# Mega backend implementation (stub)
import subprocess
import sys
import os
from pathlib import Path
from .utils import PROJECT_ROOT

class MegaBackend:
    def __init__(self, binary_path=None):
        self.binary_path = binary_path or self._find_megacmd()

    def _find_megacmd(self):
        # Prefer bundled binaries, then user install, then PATH
        exe_name = 'mega-get.exe' if os.name == 'nt' else 'mega-get'
        bat_name = 'mega-get.bat'
        candidates = [
            Path(PROJECT_ROOT) / 'downloader' / 'mega_portable' / 'MEGAcmd' / exe_name,
            Path(PROJECT_ROOT) / 'downloader' / 'mega_portable' / exe_name,
            Path(PROJECT_ROOT) / 'mega_portable' / 'MEGAcmd' / exe_name,
            Path(PROJECT_ROOT) / 'mega_portable' / exe_name,
            Path(os.path.dirname(sys.argv[0])) / exe_name,
        ]
        # Common MEGAcmd default install location on Windows
        if os.name == 'nt':
            local_appdata = os.getenv('LOCALAPPDATA')
            if local_appdata:
                base = Path(local_appdata) / 'MEGAcmd'
                candidates.extend([
                    base / exe_name,
                    base / bat_name,
                ])
        # Allow .bat fallback
        candidates.extend([
            Path(PROJECT_ROOT) / 'downloader' / 'mega_portable' / 'MEGAcmd' / bat_name,
            Path(PROJECT_ROOT) / 'downloader' / 'mega_portable' / bat_name,
            Path(PROJECT_ROOT) / 'mega_portable' / 'MEGAcmd' / bat_name,
            Path(PROJECT_ROOT) / 'mega_portable' / bat_name,
            Path(os.path.dirname(sys.argv[0])) / bat_name,
        ])
        for cand in candidates:
            if cand and os.path.isfile(cand):
                return os.fspath(cand)
        return exe_name  # fallback to PATH

    def add(self, url, options=None, return_proc=False):
        print(f"[mega] Adding download: {url}")
        if not os.path.isfile(self.binary_path):
            raise RuntimeError(f"mega-get binary not found at {self.binary_path}")

        from .utils import ensure_download_dir
        downloads_dir = os.fspath(ensure_download_dir())

        is_bat = self.binary_path.lower().endswith('.bat')
        if is_bat:
            cmd = ["cmd.exe", "/c", self.binary_path, url]
        else:
            cmd = [self.binary_path, url]

        if options:
            if isinstance(options, (list, tuple)):
                cmd.extend(options)
            elif isinstance(options, dict):
                for k, v in options.items():
                    cmd.append(str(k))
                    if v is not None:
                        cmd.append(str(v))
            else:
                cmd.append(str(options))

        try:
            proc = subprocess.Popen(cmd, cwd=downloads_dir)
            return proc if return_proc else None
        except Exception as e:
            print(f"[mega] Failed to start: {e}")
            raise

    def pause(self, download_id):
        print(f"[mega] Pausing: {download_id}")

    def resume(self, download_id):
        print(f"[mega] Resuming: {download_id}")

    def remove(self, download_id):
        print(f"[mega] Removing: {download_id}")

    def status(self, download_id=None):
        print(f"[mega] Status: {download_id if download_id else 'all'}")
