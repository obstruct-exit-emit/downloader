# aria2 backend implementation
import os
import json
import time
import ssl
import socket
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from .utils import ensure_download_dir, PROJECT_ROOT

DEFAULT_RPC_SECRET = "secret123"

class Aria2Backend:
    def __init__(self, binary_path=None, rpc_port=6800, rpc_secret=DEFAULT_RPC_SECRET, allow_direct_fallback=None):
        self.binary_path = binary_path or self._find_aria2c()
        self.rpc_port = rpc_port
        self.rpc_url = f'http://localhost:{self.rpc_port}/jsonrpc' if rpc_port else None
        self.rpc_secret = rpc_secret
        self.aria2c_proc = None
        if allow_direct_fallback is None:
            env_val = os.getenv("ARIA2_DIRECT_FALLBACK", "").lower()
            allow_direct_fallback = env_val in ("1", "true", "yes", "on")
        self.allow_direct_fallback = bool(allow_direct_fallback)

    def _is_socket_permission_error(self, err):
        msg = str(err or "").lower()
        return (
            "forbidden by its access permissions" in msg
            or "winerror 10013" in msg
            or "error 10013" in msg
        )

    def _spawn_cli_download(self, url, downloads_dir, options=None, return_proc=False):
        """Fallback to standalone aria2c (no RPC) when RPC sockets are blocked."""
        options = options or {}
        args = [
            self.binary_path,
            "--check-certificate=false",
            "--enable-rpc=false",
            "-d",
            downloads_dir,
        ]
        out_name = options.get("out") or options.get("filename")
        if out_name:
            args += ["-o", out_name]
        args.append(url)

        try:
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, text=True)
            print("[aria2] Started standalone aria2c (no RPC) due to socket permissions block.")
            return proc if return_proc else proc.pid
        except Exception as e:
            print(f"[aria2] Standalone aria2c failed: {e}")
            if self.allow_direct_fallback:
                return self._direct_download(url, downloads_dir)
            raise

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

    def _candidate_ports(self):
        ports = []
        if self.rpc_port:
            ports.append(self.rpc_port)
        # Common alternates
        ports.extend([6800, 6880, 6999])
        # Last resort: find a free ephemeral port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", 0))
                ports.append(s.getsockname()[1])
        except Exception:
            pass
        # Remove duplicates while preserving order
        deduped = []
        for p in ports:
            if p not in deduped:
                deduped.append(p)
        return deduped

    def _ensure_rpc(self, downloads_dir):
        """Ensure an aria2 RPC server is reachable; start one if needed, trying alternate ports on permission errors."""
        if not os.path.isfile(self.binary_path):
            raise RuntimeError(f"aria2c binary not found at {self.binary_path}")

        ports_to_try = self._candidate_ports()
        last_error = None

        for port in ports_to_try:
            self.rpc_port = port
            self.rpc_url = f'http://localhost:{self.rpc_port}/jsonrpc'
            try:
                if self._rpc_ping():
                    return
            except RuntimeError as auth_err:
                # Port in use with different secret; try another port
                last_error = auth_err
                continue

            # If child process exists, terminate before retrying
            if self.aria2c_proc and self.aria2c_proc.poll() is None:
                try:
                    self.aria2c_proc.terminate()
                except Exception:
                    pass
                self.aria2c_proc = None

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
                except RuntimeError as auth_err:
                    last_error = auth_err
                    break
                except Exception:
                    time.sleep(0.5)
            # If process died, capture output and try next port
            if self.aria2c_proc.poll() is not None:
                try:
                    output = (self.aria2c_proc.stdout.read() or "").strip()
                except Exception:
                    output = ""
                last_error = RuntimeError(f"aria2 RPC failed to start on port {self.rpc_port} (exit {self.aria2c_proc.returncode}). Output: {output}")
                self.aria2c_proc = None
                continue

        if last_error:
            raise last_error
        raise RuntimeError("aria2 RPC server not reachable after trying alternate ports")

    def _find_aria2c(self):
        # Prefer portable binary in aria2_portable, then project tree, then PATH
        exe_name = 'aria2c.exe' if os.name == 'nt' else 'aria2c'
        candidates = [
            os.fspath(PROJECT_ROOT / 'downloader' / 'aria2_portable' / exe_name),
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
        options = (options or {}).copy()
        options.setdefault("dir", downloads_dir)
        options.setdefault("check-certificate", "false")

        try:
            # Ensure aria2 RPC is running (start if not)
            self._ensure_rpc(downloads_dir)
        except Exception as ensure_err:
            if self._is_socket_permission_error(ensure_err):
                print("[aria2] RPC start blocked by socket permissions; switching to standalone aria2c.")
                return self._spawn_cli_download(url, downloads_dir, options, return_proc=return_proc)
            raise

        # Add download via RPC, specifying the download directory per-download
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
                # If RPC immediately reports a permission error, fall back to direct download when allowed
                try:
                    status = self.get_status(gid)
                    err_msg = (status or {}).get('errorMessage') if isinstance(status, dict) else None
                    if err_msg and self._is_socket_permission_error(err_msg):
                        print("aria2 RPC blocked by socket permissions; switching to standalone aria2c.")
                        return self._spawn_cli_download(url, downloads_dir, options, return_proc=return_proc)
                    if self.allow_direct_fallback and err_msg and 'forbidden by its access permissions' in err_msg:
                        print("aria2 RPC blocked by socket permissions; using direct download fallback.")
                        return self._direct_download(url, downloads_dir)
                except Exception:
                    # ignore status probe failures
                    pass
                return gid
        except Exception as e:
            print(f"[aria2] Failed to add download via RPC: {e}")
            if self._is_socket_permission_error(e):
                print("[aria2] RPC call blocked by socket permissions; switching to standalone aria2c.")
                return self._spawn_cli_download(url, downloads_dir, options, return_proc=return_proc)
            if self.allow_direct_fallback:
                try:
                    return self._direct_download(url, downloads_dir)
                except Exception as fallback_err:
                    print(f"[aria2] Fallback direct download failed: {fallback_err}")
            raise

    def _direct_download(self, url, downloads_dir):
        """Synchronous direct download as a fallback when aria2 RPC cannot start or connect."""
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path) or "download.bin"
        dest = os.path.join(downloads_dir, filename)
        # Avoid overwriting an existing file with the same name
        if os.path.exists(dest):
            base, ext = os.path.splitext(filename)
            dest = os.path.join(downloads_dir, f"{base}_1{ext}")
        print(f"[aria2] Falling back to direct download -> {dest}")
        with urllib.request.urlopen(url) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
        print(f"[aria2] Direct download completed: {dest}")
        return "direct-download"

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
