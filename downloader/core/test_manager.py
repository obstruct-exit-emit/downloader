# Basic tests for DownloadManager backend selection
from downloader.core.manager import DownloadManager

def test_backend_selection():
    mgr = DownloadManager()
    assert mgr._select_backend('https://mega.nz/file/abc') == mgr.mega
    assert mgr._select_backend('mega://folder/xyz') == mgr.mega
    assert mgr._select_backend('http://example.com/file.zip') == mgr.aria2
    assert mgr._select_backend('magnet:?xt=urn:btih:...') == mgr.aria2
    assert mgr._select_backend('ftp://example.com/file') == mgr.aria2
    assert mgr._select_backend('https://example.com/file') == mgr.aria2
    assert mgr._select_backend('https://mega.nz/file/abc', backend='aria2') == mgr.aria2
    assert mgr._select_backend('http://example.com/file.zip', backend='mega') == mgr.mega

if __name__ == "__main__":
    test_backend_selection()
    print("Backend selection tests passed.")
