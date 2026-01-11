# Mega backend implementation (stub)
import subprocess
import sys
import os

class MegaBackend:
    def __init__(self, binary_path=None):
        self.binary_path = binary_path or self._find_megacmd()

    def _find_megacmd(self):
        # Prefer local binary, then system PATH
        local = os.path.join(os.path.dirname(sys.argv[0]), 'mega-get.exe' if os.name == 'nt' else 'mega-get')
        if os.path.isfile(local):
            return local
        return 'mega-get'  # fallback to PATH

    def add(self, url, options=None):
        print(f"[mega] Adding download: {url}")
        cmd = [self.binary_path, url]
        if options:
            cmd.extend(options)
        try:
            subprocess.Popen(cmd)
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
