from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit
from downloads_table import DownloadsTable
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Downloader GUI')
        self.setGeometry(100, 100, 400, 200)
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.url_label = QLabel('Download URL:')
        self.url_input = QLineEdit()
        self.download_button = QPushButton('Download')
        self.status_label = QLabel('Status: Ready')
        self.downloads_table = DownloadsTable()

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.download_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.downloads_table)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.download_button.clicked.connect(self.start_download)

    def start_download(self):
        import subprocess
        import os
        import re
        url = self.url_input.text()
        if not url:
            self.status_label.setText('Please enter a URL.')
            return

        self.status_label.setText(f'Starting download: {url}')
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            result = subprocess.run([
                sys.executable, '-m', 'downloader.cli', 'add', url
            ], capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                self.status_label.setText('Download started successfully.')
                self.downloads_table.refresh_table()
            else:
                self.status_label.setText(f'Error: {result.stderr.strip() or result.stdout.strip()}')
        except Exception as e:
            self.status_label.setText(f'Exception: {str(e)}')

    def refresh_progress(self):
        # Call CLI to get progress for self.download_id
        import subprocess
        import os
        import re
        import json
        if not self.download_id:
            self.status_label.setText('No download ID available.')
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

        # Load state to find gid/status
        gid = None
        job_status = None
        try:
            state_path = os.path.abspath(os.path.join(project_root, '.downloader_state.json'))
            with open(state_path, 'r') as f:
                state = json.load(f)
            all_jobs = (state.get('queue') or []) + (state.get('history') or [])
            for job in all_jobs:
                if job.get('id') == self.download_id:
                    gid = job.get('gid')
                    job_status = job.get('status')
                    break
        except Exception:
            pass

        # If completed, set to 100%
        if job_status == 'completed' or (gid == 'direct-download'):
            self.progress_bar.setValue(100)
            self.status_label.setText('Progress: 100% (completed)')
            return

        # Try aria2-progress when gid is available and not a direct-download marker
        if gid:
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'downloader.cli', 'aria2-progress', gid
                ], capture_output=True, text=True, cwd=project_root)
                output = result.stdout.strip()
                percent = None
                match = re.search(r'Progress: ([0-9.]+)%', output)
                if match:
                    percent = float(match.group(1))
                if percent is not None:
                    self.progress_bar.setValue(int(percent))
                    self.status_label.setText(f'Progress: {percent:.2f}%')
                    return
                else:
                    # Fallback to display raw output
                    self.status_label.setText(output or 'No output from aria2-progress.')
                    return
            except Exception as e:
                self.status_label.setText(f'Exception: {str(e)}')
                return

        # Fallback: call status (may not provide percentage)
        try:
            result = subprocess.run([
                sys.executable, '-m', 'downloader.cli', 'status', self.download_id
            ], capture_output=True, text=True, cwd=project_root)
            output = result.stdout.strip()
            self.status_label.setText(output or 'No output from status command.')
        except Exception as e:
            self.status_label.setText(f'Exception: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
