# CLI entry point using argparse (MVP)
import argparse
from downloader.core.manager import DownloadManager

def main():
    parser = argparse.ArgumentParser(description="Cross-platform download utility")
    subparsers = parser.add_subparsers(dest="command")

    # Add download
    add_parser = subparsers.add_parser("add", help="Add a new download")
    add_parser.add_argument("url", help="URL to download")
    add_parser.add_argument("--backend", help="Force backend (aria2, mega)")



    # Pause/resume/remove
    for cmd in ["pause", "resume", "remove", "status"]:
        p = subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a download")
        p.add_argument("id", nargs="?", help="Download ID")
    # Query aria2 download progress by GID
    progress_parser = subparsers.add_parser("aria2-progress", help="Show progress for aria2 download by GID")
    progress_parser.add_argument("gid", help="aria2 GID")
    # List all aria2 downloads (GIDs)
    subparsers.add_parser("aria2-list", help="List all active aria2 download GIDs and status")
    # List downloads
    subparsers.add_parser("list", help="List all downloads")
    # Download portable aria2
    subparsers.add_parser("get-aria2", help="Download portable aria2c.exe for Windows into project directory")
    # Download portable MegaCMD
    subparsers.add_parser("get-mega", help="Download portable megacmd for Windows into project directory")


    args = parser.parse_args()
    manager = DownloadManager()

    if args.command == "add":
        manager.add(args.url, backend=args.backend)
    elif args.command == "list":
        manager.refresh()
        manager.status()
    elif args.command == "get-mega":
        import os, sys, urllib.request, subprocess, shutil
        from pathlib import Path
        from downloader.core.utils import PROJECT_ROOT

        mega_url = "https://mega.nz/MEGAcmdSetup64.exe"
        installer_path = Path(PROJECT_ROOT) / "downloader" / "MEGAcmdSetup64.exe"
        portable_dir = Path(PROJECT_ROOT) / "downloader" / "mega_portable"
        portable_dir.mkdir(parents=True, exist_ok=True)

        # Download installer if missing or zero bytes
        if not installer_path.is_file() or installer_path.stat().st_size == 0:
            print(f"Downloading MEGAcmd installer from {mega_url} ...")
            urllib.request.urlretrieve(mega_url, installer_path)

        print("Running MEGAcmd installer (silent)...")
        try:
            result = subprocess.run([
                os.fspath(installer_path.resolve()),
                "/S",
            ], capture_output=True, text=True)
            if result.returncode != 0:
                print("MEGAcmd installer failed. Output:")
                print(result.stdout)
                print(result.stderr)
                print("You may need to rerun get-mega or install manually.")
                return
        except Exception as e:
            print(f"Installer failed: {e}")
            print("You may need to rerun get-mega or install manually.")
            return

        # Stop MEGAcmd processes so we can copy files
        if os.name == 'nt':
            subprocess.run(["taskkill", "/IM", "MEGAcmd*", "/F"], capture_output=True)

        # Copy installed MEGAcmd into project portable folder
        source_dir = None
        if os.name == 'nt':
            local_appdata = os.getenv('LOCALAPPDATA')
            if local_appdata:
                candidate = Path(local_appdata) / "MEGAcmd"
                if candidate.exists():
                    source_dir = candidate
        if not source_dir:
            print("Could not locate MEGAcmd installation to copy.")
        else:
            dest = portable_dir / "MEGAcmd"
            try:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source_dir, dest)
                print(f"Copied MEGAcmd to portable folder: {dest}")
            except Exception as e:
                print(f"Failed to copy MEGAcmd to portable folder: {e}")

        # Uninstall system MEGAcmd to stay portable
        if source_dir:
            uninstaller = source_dir / "uninst.exe"
            if uninstaller.exists():
                subprocess.run([os.fspath(uninstaller), "/S"], capture_output=True)
                print("Ran MEGAcmd uninstaller to remove system install.")

        # Clean up installer
        try:
            installer_path.unlink()
        except Exception:
            pass
        print("Done.")
    # (Removed duplicate and obsolete code for get-aria2 and get-mega)
    elif args.command == "aria2-list":
        from downloader.core.aria2_backend import Aria2Backend, DEFAULT_RPC_SECRET
        backend = Aria2Backend(rpc_secret=DEFAULT_RPC_SECRET)
        # List all active downloads via aria2 RPC
        payload = {
            "jsonrpc": "2.0",
            "id": "tellActive",
            "method": "aria2.tellActive",
            "params": [f"token:{backend.rpc_secret}", ["gid", "status", "totalLength", "completedLength", "downloadSpeed", "errorCode", "errorMessage"]]
        }
        import urllib.request, json
        try:
            req = urllib.request.Request(backend.rpc_url, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
                downloads = result.get('result') or []
                if not downloads:
                    print("No active aria2 downloads.")
                    return
                for d in downloads:
                    gid = d['gid']
                    status = d.get('status')
                    total = int(d.get('totalLength', 0))
                    completed = int(d.get('completedLength', 0))
                    percent = (completed / total * 100) if total else 0
                    speed = int(d.get('downloadSpeed', 0))
                    err = d.get('errorMessage') or ''
                    print(f"GID: {gid} | Status: {status} | Progress: {percent:.2f}% ({completed}/{total} bytes) | Speed: {speed/1024:.2f} KB/s {err}")
        except Exception as e:
            print(f"Failed to list aria2 downloads: {e}")
    elif args.command == "aria2-progress":
        from downloader.core.aria2_backend import Aria2Backend, DEFAULT_RPC_SECRET
        backend = Aria2Backend(rpc_secret=DEFAULT_RPC_SECRET)
        status = backend.get_status(args.gid)
        if status:
            total = int(status.get('totalLength', 0))
            completed = int(status.get('completedLength', 0))
            percent = (completed / total * 100) if total else 0
            speed = int(status.get('downloadSpeed', 0))
            err = status.get('errorMessage') or ''
            err_line = f"\nError: {err}" if err else ""
            print(f"GID: {args.gid}\nStatus: {status.get('status')}\nProgress: {percent:.2f}% ({completed}/{total} bytes)\nSpeed: {speed/1024:.2f} KB/s{err_line}")
        else:
            print("Could not retrieve status for GID", args.gid)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
