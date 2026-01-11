# aria2 backend implementation (stub)
import subprocess
import sys
import os

class Aria2Backend:
    def __init__(self, binary_path=None):
        self.binary_path = binary_path or self._find_aria2c()

    def _find_aria2c(self):
        # Prefer local binary, then system PATH
        local = os.path.join(os.path.dirname(sys.argv[0]), 'aria2c.exe' if os.name == 'nt' else 'aria2c')
        if os.path.isfile(local):
            return local
        return 'aria2c'  # fallback to PATH

    def add(self, url, options=None, return_proc=False, progress_callback=None):
        # Start a download using aria2c CLI
        cmd = [self.binary_path, url]
        if options:
            cmd.extend(options)
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if not return_proc:
                for line in proc.stdout:
                    # Try to parse progress percentage from line
                    if progress_callback:
                        import re
                        m = re.search(r'(\d+)%', line)
                        if m:
                            progress_callback(int(m.group(1)))
            else:
                return proc
        except Exception as e:
            print(f"[aria2] Failed to start: {e}")
            raise

    def pause(self, download_id):

    def resume(self, download_id):

    def remove(self, download_id):

    def status(self, download_id=None):
