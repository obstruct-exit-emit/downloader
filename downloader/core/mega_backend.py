# Mega backend implementation (stub)
import subprocess
import sys
import os

class MegaBackend:
    def __init__(self, binary_path=None):
        self.binary_path = binary_path or self._find_megacmd()

    def _find_megacmd(self):
        # Prefer local binary, then system PATH
        exe_name = 'mega-get.exe' if os.name == 'nt' else 'mega-get'
        local = os.path.join(os.path.dirname(sys.argv[0]), exe_name)
        if os.path.isfile(local):
            return local
        return exe_name  # fallback to PATH

    def add(self, url, options=None, return_proc=False):
        print(f"[mega] Adding download: {url}")
        if not os.path.isfile(self.binary_path):
            raise RuntimeError(f"mega-get binary not found at {self.binary_path}")
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
            proc = subprocess.Popen(cmd)
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
