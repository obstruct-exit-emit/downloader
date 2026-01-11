# Test for Persistence module
from downloader.core.persistence import Persistence
import os

def test_persistence():
    test_path = 'test_queue.json'
    p = Persistence(test_path)
    queue = [{'id': '1', 'url': 'http://a', 'backend': 'aria2', 'status': 'queued'}]
    history = [{'id': '2', 'url': 'http://b', 'backend': 'aria2', 'status': 'done'}]
    p.save(queue, history)
    data = p.load()
    assert data['queue'] == queue
    assert data['history'] == history
    os.remove(test_path)
    print('Persistence test passed.')

if __name__ == "__main__":
    test_persistence()
