# CLI entry point using argparse (MVP)
import argparse
import sys
import json
from downloader.core.manager import DownloadManager
from downloader.core.config import Config


def _install_portable_aria2():
    """Download and place a portable aria2c.exe into the aria2_portable folder."""
    import urllib.request
    import zipfile
    import shutil
    from pathlib import Path
    from downloader.core.utils import PROJECT_ROOT

    aria_url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    portable_dir = Path(PROJECT_ROOT) / "downloader" / "aria2_portable"
    portable_dir.mkdir(parents=True, exist_ok=True)
    archive_path = portable_dir / "aria2_portable.zip"
    extract_dir = portable_dir / "aria2_portable_tmp"

    try:
        print(f"Downloading aria2 bundle from {aria_url} ...")
        urllib.request.urlretrieve(aria_url, archive_path)
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)
        candidates = list(extract_dir.glob("**/aria2c.exe"))
        if not candidates:
            print("Could not find aria2c.exe in the downloaded archive.")
            return
        dest = portable_dir / "aria2c.exe"
        shutil.copy2(candidates[0], dest)
        print(f"aria2c.exe placed at {dest}")
    except Exception as exc:
        print(f"Failed to download or extract aria2: {exc}")
    finally:
        try:
            archive_path.unlink()
        except Exception:
            pass
        shutil.rmtree(extract_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Cross-platform download utility")
    fallback_group = parser.add_mutually_exclusive_group()
    fallback_group.add_argument("--aria2-direct-fallback", dest="aria2_direct_fallback", action="store_true", help="Enable direct download fallback when aria2 RPC is blocked")
    fallback_group.add_argument("--no-aria2-direct-fallback", dest="aria2_direct_fallback", action="store_false", help="Disable direct download fallback (default if env not set)")
    parser.set_defaults(aria2_direct_fallback=None)
    subparsers = parser.add_subparsers(dest="command")

    # Add download
    add_parser = subparsers.add_parser("add", help="Add a new download")
    add_parser.add_argument("url", help="URL to download")
    add_parser.add_argument("--backend", help="Force backend (aria2, mega)")

    # Pause/resume/remove
    for cmd in ["pause", "resume", "remove"]:
        p = subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a download")
        p.add_argument("id", help="Download ID")

    # Status (single or all)
    status_parser = subparsers.add_parser("status", help="Show status for a download or all")
    status_parser.add_argument("id", nargs="?", help="Download ID (optional)")
    # Query aria2 download progress by GID
    progress_parser = subparsers.add_parser("aria2-progress", help="Show progress for aria2 download by GID")
    progress_parser.add_argument("gid", help="aria2 GID")
    # List all aria2 downloads (GIDs)
    subparsers.add_parser("aria2-list", help="List all active aria2 download GIDs and status")
    # List downloads
    subparsers.add_parser("list", help="List all downloads")
    # Config commands
    config_parser = subparsers.add_parser("config", help="View or set backend configuration")
    config_sub = config_parser.add_subparsers(dest="config_command")

    cfg_show = config_sub.add_parser("show", help="Show current configuration")

    cfg_aria2 = config_sub.add_parser("aria2", help="Set aria2 settings")
    cfg_aria2.add_argument("--rpc-secret", dest="rpc_secret", help="Set aria2 RPC secret")
    cfg_aria2.add_argument("--rpc-port", dest="rpc_port", type=int, help="Set aria2 RPC port")

    cfg_mega = config_sub.add_parser("mega", help="Set Mega credentials")
    cfg_mega.add_argument("--email", dest="email", help="Set Mega email")
    cfg_mega.add_argument("--password", dest="password", help="Set Mega password")
    # Download portable aria2
    subparsers.add_parser("get-aria2", help="Download portable aria2c.exe for Windows into project directory")
    # Download portable MegaCMD
    subparsers.add_parser("get-mega", help="Download portable megacmd for Windows into project directory")
    # Download portable 7-Zip (7zr.exe)
    subparsers.add_parser("get-7zip", help="Download portable 7-Zip (7zr.exe) into project directory")


    args = parser.parse_args()
    config = Config()
    manager = DownloadManager(aria2_direct_fallback=args.aria2_direct_fallback, config=config)

    if args.command == "add":
        manager.add(args.url, backend=args.backend)
    elif args.command == "pause":
        manager.pause(args.id)
    elif args.command == "resume":
        manager.resume(args.id)
    elif args.command == "remove":
        manager.remove(args.id)
    elif args.command == "status":
        manager.status(args.id)
    elif args.command == "list":
        manager.refresh()
        manager.status()
    elif args.command == "get-aria2":
        if sys.platform != "win32":
            print("get-aria2 is currently supported on Windows only.")
        else:
            _install_portable_aria2()
    elif args.command == "get-mega":
        import os, urllib.request, subprocess, shutil
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
    elif args.command == "config":
        if args.config_command == "show":
            data = config.data.copy()
            mega = data.get("mega") or {}
            if "password" in mega:
                mega = mega.copy()
                mega["password"] = "***"
                data["mega"] = mega
            aria2_cfg = data.get("aria2") or {}
            if "rpc_secret" in aria2_cfg:
                aria2_cfg = aria2_cfg.copy()
                aria2_cfg["rpc_secret"] = "***"
                data["aria2"] = aria2_cfg
            print(json.dumps(data, indent=2))
        elif args.config_command == "aria2":
            try:
                config.set_aria2(rpc_secret=args.rpc_secret, rpc_port=args.rpc_port)
                print("Updated aria2 config.")
            except ValueError as ve:
                print(f"Invalid aria2 config: {ve}")
        elif args.config_command == "mega":
            config.set_mega(email=args.email, password=args.password)
            print("Updated Mega config.")
        else:
            config_parser = [sp for sp in subparsers.choices.values() if sp.prog.endswith('config')]
            parser.print_help()
    elif args.command == "get-7zip":
        import os, urllib.request, shutil
        from pathlib import Path
        from downloader.core.utils import PROJECT_ROOT

        if sys.platform != "win32":
            print("get-7zip is currently supported on Windows only.")
            return

        portable_dir = Path(PROJECT_ROOT) / "downloader" / "7zip_portable"
        portable_dir.mkdir(parents=True, exist_ok=True)
        target = portable_dir / "7zr.exe"
        url = "https://www.7-zip.org/a/7zr.exe"

        try:
            print(f"Downloading 7zr.exe from {url} ...")
            urllib.request.urlretrieve(url, target)
            print(f"7zr.exe placed at {target}")
        except Exception as e:
            print(f"Failed to download 7zr.exe: {e}")
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
