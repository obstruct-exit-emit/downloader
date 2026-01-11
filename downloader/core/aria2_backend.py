# aria2 backend implementation (stub)
import subprocess
import sys
import os

DEFAULT_RPC_SECRET = "secret123"


import json
import urllib.request
import time
import urllib.error
import ssl
from .utils import ensure_download_dir, DOWNLOADS_DIR, PROJECT_ROOT

class Aria2Backend:
    def __init__(self, binary_path=None, rpc_port=6800, rpc_secret=DEFAULT_RPC_SECRET):
        self.binary_path = binary_path or self._find_aria2c()
        self.rpc_port = rpc_port
        self.rpc_url = f'http://localhost:{self.rpc_port}/jsonrpc'
        self.rpc_secret = rpc_secret
        self.aria2c_proc = None

    def _rpc_ping(self):
        payload = {
            "jsonrpc": "2.0",
            "id": "ping",
            "method": "aria2.getVersion",
            "params": [f"token:{self.rpc_secret}"]
        }
        try:
            req = urllib.request.Request(
                self.rpc_url,
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=2):
                return True
        except urllib.error.HTTPError as he:
            if he.code == 401:
                raise RuntimeError("aria2 RPC reachable but authentication failed; check rpc-secret") from he
            return False
        except Exception:
            return False

    def _ensure_rpc(self, downloads_dir):
        """Ensure an aria2 RPC server is reachable; start one if needed."""
        if not os.path.isfile(self.binary_path):
            raise RuntimeError(f"aria2c binary not found at {self.binary_path}")
        try:
            if self._rpc_ping():
                return
        except RuntimeError:
            # Secret mismatch but server is up; surface immediately
            raise

        # If we think we have a child process but it is dead/unreachable, terminate it and restart
        if self.aria2c_proc and self.aria2c_proc.poll() is None:
            try:
                self.aria2c_proc.terminate()
            except Exception:
                pass
            self.aria2c_proc = None

        if self.aria2c_proc is None or self.aria2c_proc.poll() is not None:
            rpc_cmd = [
                self.binary_path,
                '--enable-rpc',
                f'--rpc-listen-port={self.rpc_port}',
                '--rpc-listen-all=false',
                '--check-certificate=false',
                f'--rpc-secret={self.rpc_secret}',
                f'--dir={downloads_dir}'
            ]
            self.aria2c_proc = subprocess.Popen(rpc_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            # Wait for RPC server to start
            for _ in range(10):
                try:
                    if self._rpc_ping():
                        return
                except RuntimeError:
                    raise
                except Exception:
                    time.sleep(0.5)
            # If we reach here, startup failed; include any aria2 output to help troubleshoot
            if self.aria2c_proc.poll() is not None:
                try:
                    output = (self.aria2c_proc.stdout.read() or "").strip()
                except Exception:
                    output = ""
                raise RuntimeError(f"aria2 RPC failed to start (exit {self.aria2c_proc.returncode}). Output: {output}")
        raise RuntimeError("aria2 RPC server not reachable")

    def _find_aria2c(self):
        # Prefer bundled binary in project tree, then system PATH
        exe_name = 'aria2c.exe' if os.name == 'nt' else 'aria2c'
        candidates = [
            os.fspath(PROJECT_ROOT / 'downloader' / exe_name),
            os.fspath(PROJECT_ROOT / exe_name),
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
        return exe_name  # fallback to PATH

    def _precheck_url(self, url):
        """Lightweight reachability check before handing off to aria2.

        For http/https, issue a HEAD (or byte-range GET fallback) with certificate checks disabled
        to mirror aria2's default `--check-certificate=false`. Other schemes are skipped.
        """
        if not (url.startswith("http://") or url.startswith("https://")):
            return

        ctx = None
        if url.startswith("https://"):
            try:
                ctx = ssl._create_unverified_context()
            except Exception:
                ctx = None

        def _try_request(method, headers=None):
            req = urllib.request.Request(url, method=method, headers=headers or {})
            with urllib.request.urlopen(req, timeout=5, context=ctx):
                return True

        try:
            _try_request("HEAD")
            return
        except urllib.error.HTTPError as he:
            if he.code not in (400, 403, 405):
                raise RuntimeError(f"URL precheck failed: HTTP {he.code}") from he
            # HEAD refused, fall through to range GET fallback
        except Exception:
            # Connection-level failure on HEAD; try range GET next
            pass

        # Fallback: tiny range GET to detect reachability
        try:
            _try_request("GET", {"Range": "bytes=0-0"})
            return
        except Exception as e:
            raise RuntimeError(f"URL precheck failed (range GET): {e}") from e

    def add(self, url, options=None, return_proc=False, progress_callback=None):
        # Basic reachability check before spinning up aria2/RPC
        self._precheck_url(url)
        downloads_dir = os.fspath(ensure_download_dir())
        # Ensure aria2 RPC is running (start if not)
        self._ensure_rpc(downloads_dir)
        # Add download via RPC, specifying the download directory per-download
        options = (options or {}).copy()
        options.setdefault("dir", downloads_dir)
        options.setdefault("check-certificate", "false")
        payload = {
            "jsonrpc": "2.0",
            "id": "addUri",
            "method": "aria2.addUri",
            "params": [f"token:{self.rpc_secret}", [url], options]
        }
        try:
            req = urllib.request.Request(self.rpc_url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                gid = result['result']
                print(f"Added download (GID: {gid}) via aria2 RPC.")
                return gid
        except Exception as e:
            print(f"[aria2] Failed to add download via RPC: {e}")
            raise

    def get_status(self, gid):
        # Query aria2c RPC for download status
        payload = {
            "jsonrpc": "2.0",
            "id": "tellStatus",
            "method": "aria2.tellStatus",
            "params": [f"token:{self.rpc_secret}", gid, ["status", "completedLength", "totalLength", "downloadSpeed", "errorCode", "errorMessage"]]
        }
        try:
            req = urllib.request.Request(self.rpc_url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                return result['result']
        except Exception as e:
            print(f"[aria2] Failed to get status via RPC: {e}")
            return None

    def pause(self, download_id):
        pass

    def resume(self, download_id):
        pass

    def remove(self, download_id):
        pass

    def status(self, download_id=None):
        pass
