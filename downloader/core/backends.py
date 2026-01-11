# Backend abstraction for aria2, mega, etc.

class BackendBase:
    def add(self, url, options=None):
        raise NotImplementedError("add() must be implemented by backend.")
    def pause(self, download_id):
        raise NotImplementedError("pause() must be implemented by backend.")
    def resume(self, download_id):
        raise NotImplementedError("resume() must be implemented by backend.")
    def remove(self, download_id):
        raise NotImplementedError("remove() must be implemented by backend.")
    def status(self, download_id=None):
        raise NotImplementedError("status() must be implemented by backend.")
