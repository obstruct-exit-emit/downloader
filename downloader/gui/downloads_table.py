from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer
import os
import sys
import json

class DownloadsTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(['ID', 'URL', 'Backend', 'Status', 'Progress', 'Pause', 'Resume', 'Remove'])
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)
        self.refresh_table()
        # Auto-refresh every 3 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_table)
        self.timer.start(3000)

    def refresh_table(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        state_path = os.path.abspath(os.path.join(project_root, '.downloader_state.json'))
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            jobs = (state.get('queue') or []) + (state.get('history') or [])
        except Exception:
            jobs = []
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            self.table.setItem(row, 0, QTableWidgetItem(job.get('id', '')))
            self.table.setItem(row, 1, QTableWidgetItem(job.get('url', '')))
            self.table.setItem(row, 2, QTableWidgetItem(str(job.get('backend', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(job.get('status', '')))
            # Progress
            percent = '0'
            if job.get('status') == 'completed' or job.get('gid') == 'direct-download':
                percent = '100'
            elif job.get('gid'):
                percent = self.get_progress(job.get('gid'))
            self.table.setItem(row, 4, QTableWidgetItem(percent))
            # Pause button
            pause_btn = QPushButton('Pause')
            pause_btn.clicked.connect(lambda _, r=row: self.pause_job(r))
            self.table.setCellWidget(row, 5, pause_btn)
            # Resume button
            resume_btn = QPushButton('Resume')
            resume_btn.clicked.connect(lambda _, r=row: self.resume_job(r))
            self.table.setCellWidget(row, 6, resume_btn)
            # Remove button
            remove_btn = QPushButton('Remove')
            remove_btn.clicked.connect(lambda _, r=row: self.remove_job(r))
            self.table.setCellWidget(row, 7, remove_btn)

    def get_progress(self, gid):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'downloader.cli', 'aria2-progress', gid
            ], capture_output=True, text=True, cwd=project_root)
            output = result.stdout.strip()
            import re
            match = re.search(r'Progress: ([0-9.]+)%', output)
            if match:
                return match.group(1)
        except Exception:
            pass
        return '0'

    def _run_cli(self, args):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, '-m', 'downloader.cli', *args
            ], capture_output=True, text=True, cwd=project_root)
            return result.returncode, (result.stdout.strip() or result.stderr.strip())
        except Exception as e:
            return 1, str(e)

    def pause_job(self, row):
        job_id = self.table.item(row, 0).text()
        job = self._load_job(job_id)
        if not job:
            QMessageBox.information(self, 'Pause not supported', 'Job not found.')
            return
        if not job.get('pid') and not job.get('gid'):
            QMessageBox.information(self, 'Pause not supported', 'Pause is only available for jobs with PID or GID (aria2).')
            return
        code, out = self._run_cli(['pause', job_id])
        if code != 0:
            QMessageBox.warning(self, 'Pause failed', out or 'Pause failed')
        self.refresh_table()

    def resume_job(self, row):
        job_id = self.table.item(row, 0).text()
        job = self._load_job(job_id)
        if not job:
            QMessageBox.information(self, 'Resume not supported', 'Job not found.')
            return
        if not job.get('pid') and not job.get('gid'):
            QMessageBox.information(self, 'Resume not supported', 'Resume is only available for jobs with PID or GID (aria2).')
            return
        code, out = self._run_cli(['resume', job_id])
        if code != 0:
            QMessageBox.warning(self, 'Resume failed', out or 'Resume failed')
        self.refresh_table()

    def remove_job(self, row):
        job_id = self.table.item(row, 0).text()
        url = self.table.item(row, 1).text()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle('Remove Download')
        msg.setText(f'Remove download for URL:\n{url}')
        msg.setInformativeText('Choose an action:')
        remove_only = msg.addButton('Remove from list only', QMessageBox.AcceptRole)
        remove_and_delete = msg.addButton('Remove and delete file', QMessageBox.DestructiveRole)
        msg.addButton('Cancel', QMessageBox.RejectRole)
        msg.exec_()
        # Load job info before removal for deletion logic
        job = self._load_job(job_id)
        if msg.clickedButton() == remove_only:
            self.remove_from_list(job_id)
        elif msg.clickedButton() == remove_and_delete:
            self.remove_from_list(job_id)
            self.delete_file(job)
        self.refresh_table()

    def _load_job(self, job_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        state_path = os.path.abspath(os.path.join(project_root, '.downloader_state.json'))
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            jobs = (state.get('queue') or []) + (state.get('history') or [])
            return next((j for j in jobs if j.get('id') == job_id), None)
        except Exception:
            return None

    def remove_from_list(self, job_id):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        state_path = os.path.abspath(os.path.join(project_root, '.downloader_state.json'))
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
            queue = [j for j in state.get('queue', []) if j.get('id') != job_id]
            history = [j for j in state.get('history', []) if j.get('id') != job_id]
            with open(state_path, 'w') as f:
                json.dump({'queue': queue, 'history': history}, f)
        except Exception:
            pass

    def delete_file(self, job):
        if not job:
            return
        from pathlib import Path
        from urllib.parse import urlparse
        downloads_dir = Path(__file__).resolve().parents[2] / 'downloads'
        url = job.get('url', '')
        parsed = urlparse(url)
        filename = Path(parsed.path).name or 'download.bin'
        stem = Path(filename).stem
        candidates = []
        candidates.append(downloads_dir / filename)
        candidates.append(downloads_dir / f"{stem}.aria2")
        candidates.extend(downloads_dir.glob(f"{stem}*"))
        for path in candidates:
            try:
                if path.exists():
                    path.unlink()
                    break
            except Exception:
                continue
