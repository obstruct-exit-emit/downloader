# Basic CLI test (manual, for now)
import subprocess
import sys
import os

if __name__ == "__main__":
    # Add a download
    subprocess.run([sys.executable, '-m', 'downloader.cli', 'add', 'http://example.com/file.zip'])
    # List downloads
    subprocess.run([sys.executable, '-m', 'downloader.cli', 'list'])
    # Remove the download (should be the only one, so get its ID from the queue file)
    from downloader.core.persistence import Persistence
    queue = Persistence().load()['queue']
    if queue:
        subprocess.run([sys.executable, '-m', 'downloader.cli', 'remove', queue[0]['id']])
    # List again
    subprocess.run([sys.executable, '-m', 'downloader.cli', 'list'])
    print('CLI test completed.')
