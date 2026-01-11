# Download manager: handles queue, state, and operations

from .aria2_backend import Aria2Backend, DEFAULT_RPC_SECRET
from .mega_backend import MegaBackend
from .persistence import Persistence
import re

class DownloadManager:
    def __init__(self):
        self.aria2 = Aria2Backend(rpc_secret=DEFAULT_RPC_SECRET)
        self.mega = MegaBackend()
        self.persistence = Persistence()
        data = self.persistence.load()
        self.queue = data.get('queue', [])
        self.history = data.get('history', [])

    def _select_backend(self, url, backend=None):
        if backend:
            backend = backend.lower()
            if backend == 'aria2':
                return self.aria2
            elif backend == 'mega':
                return self.mega
        # Auto-select based on URL
        if url.startswith('mega://') or re.match(r'https://mega\.nz/', url):
            return self.mega
        return self.aria2

    def add(self, url, backend=None, options=None):
        b = self._select_backend(url, backend)
        download_id = self.persistence.generate_id()
        backend_name = backend or b.__class__.__name__
        job = {
            'id': download_id,
            'url': url,
            'backend': backend_name,
            'status': 'queued',
            'pid': None,
            'gid': None
        }
        self.queue.append(job)
        self.persistence.save(self.queue, self.history)
        try:
            # Start the process and store its PID or GID
            result = b.add(url, options, return_proc=True)
            if b.__class__.__name__.lower().startswith('aria2') and isinstance(result, str):
                job['gid'] = result
                job['status'] = 'started'
                print(f"Added download {download_id} ({url}) using {job['backend']} (GID: {job['gid']})")
            elif result and hasattr(result, 'pid'):
                job['pid'] = result.pid
                job['status'] = 'started'
                print(f"Added download {download_id} ({url}) using {job['backend']} (PID: {job['pid']})")
            else:
                job['status'] = 'started'
                print(f"Added download {download_id} ({url}) using {job['backend']}")
        except Exception as e:
            job['status'] = 'error'
            print(f"Failed to start download {download_id}: {e}")
        self.persistence.save(self.queue, self.history)


    def pause(self, download_id):
        job = next((j for j in self.queue if j['id'] == download_id), None)
        if job and job.get('pid'):
            try:
                import os, sys
                if os.name == 'nt':
                    # Windows: suspend process using ctypes
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(0x0002 | 0x0400, False, job['pid'])
                    if handle:
                        kernel32.SuspendThread(handle)
                        kernel32.CloseHandle(handle)
                else:
                    import signal
                    os.kill(job['pid'], signal.SIGSTOP)
                job['status'] = 'paused'
                print(f"Paused download {download_id} (PID: {job['pid']})")
            except Exception as e:
                print(f"Failed to pause download {download_id}: {e}")
        self.persistence.save(self.queue, self.history)

    def resume(self, download_id):
        job = next((j for j in self.queue if j['id'] == download_id), None)
        if job and job.get('pid'):
            try:
                import os, sys
                if os.name == 'nt':
                    # Windows: resume process using ctypes
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(0x0002 | 0x0400, False, job['pid'])
                    if handle:
                        kernel32.ResumeThread(handle)
                        kernel32.CloseHandle(handle)
                else:
                    import signal
                    os.kill(job['pid'], signal.SIGCONT)
                job['status'] = 'started'
                print(f"Resumed download {download_id} (PID: {job['pid']})")
            except Exception as e:
                print(f"Failed to resume download {download_id}: {e}")
        self.persistence.save(self.queue, self.history)

    def remove(self, download_id):
        job = next((j for j in self.queue if j['id'] == download_id), None)
        if job and job.get('pid'):
            try:
                import os
                if os.name == 'nt':
                    import signal
                    os.kill(job['pid'], signal.SIGTERM)
                else:
                    import signal
                    os.kill(job['pid'], signal.SIGTERM)
                print(f"Terminated download {download_id} (PID: {job['pid']})")
            except Exception as e:
                print(f"Failed to terminate download {download_id}: {e}")
        self.queue = [j for j in self.queue if j['id'] != download_id]
        self.persistence.save(self.queue, self.history)

    def status(self, download_id=None):
        if download_id:
            jobs = [j for j in self.queue if j['id'] == download_id]
        else:
            jobs = self.queue
        if not jobs:
            print("No downloads yet. Use 'add <url>' to start one.")
            return
        for job in jobs:
            gid_part = f" GID={job['gid']}" if job.get('gid') else ''
            pid_part = f" PID={job['pid']}" if job.get('pid') else ''
            print(f"{job['id']}: {job['url']} [{job['backend']}] {job['status']}{gid_part}{pid_part}")

    def refresh(self):
        """Refresh job statuses for simple backends (mega: mark complete if process exited)."""
        changed = False
        for job in self.queue:
            if job['backend'].lower() == 'mega' and job.get('status') == 'started':
                pid = job.get('pid')
                if pid:
                    try:
                        import psutil  # optional dependency
                        if not psutil.pid_exists(pid):
                            job['status'] = 'completed'
                            changed = True
                    except ImportError:
                        # Fallback: if pid not found via OS
                        try:
                            import os, signal
                            os.kill(pid, 0)
                        except OSError:
                            job['status'] = 'completed'
                            changed = True
        if changed:
            self.persistence.save(self.queue, self.history)
