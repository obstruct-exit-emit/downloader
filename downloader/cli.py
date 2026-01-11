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
        manager.status()
    elif args.command == "get-mega":
        import os, sys, urllib.request, shutil, subprocess
        mega_url = "https://mega.nz/MEGAcmdSetup64.exe"
        installer_path = os.path.join(os.path.dirname(__file__), "MEGAcmdSetup64.exe")
        portable_dir = os.path.join(os.path.dirname(sys.argv[0]), "mega_portable")
        os.makedirs(portable_dir, exist_ok=True)
        print(f"Downloading MEGAcmd installer from {mega_url} ...")
        urllib.request.urlretrieve(mega_url, installer_path)


        # Download and extract full 7-Zip portable if not present
        sevenzip_dir = os.path.join(os.path.dirname(__file__), "7zip_portable")

        # Try 7za.exe (standalone) if 7z.exe is not present
        sevenzip_exe = os.path.join(sevenzip_dir, "7z.exe")
        if not os.path.isfile(sevenzip_exe):
            sevenzip_exe = os.path.join(sevenzip_dir, "7za.exe")
        if not os.path.isfile(sevenzip_exe):
            sevenzip_exe = os.path.join(sevenzip_dir, "x64", "7za.exe")
        if not os.path.isfile(sevenzip_exe):
            print("7z.exe or 7za.exe not found, downloading 7-Zip portable...")
            sevenzip_url = "https://www.7-zip.org/a/7z2301-extra.7z"
            sevenzip_archive = os.path.join(os.path.dirname(__file__), "7z_portable.7z")
            try:
                urllib.request.urlretrieve(sevenzip_url, sevenzip_archive)
                print("7-Zip portable archive downloaded.")
                # Try to extract with 7zr.exe if available, else instruct user
                sevenzr_path = os.path.join(os.path.dirname(__file__), "7zr.exe")
                if not os.path.isfile(sevenzr_path):
                    print("7zr.exe not found, downloading minimal 7zr.exe to bootstrap extraction...")
                    urllib.request.urlretrieve("https://www.7-zip.org/a/7zr.exe", sevenzr_path)
                print("Extracting 7z.exe and 7z.dll from 7z2301-extra.7z ...")
                result = subprocess.run([
                    sevenzr_path, "x", sevenzip_archive, f"-o{sevenzip_dir}", "-y"
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    print("Failed to extract 7-Zip portable. Output:")
                    print(result.stdout)
                    print(result.stderr)
                    print(f"You can manually extract {sevenzip_archive} to {sevenzip_dir} using 7-Zip.")
                    return
                print("7z.exe and 7z.dll extracted.")
                os.remove(sevenzip_archive)
            except Exception as e:
                print(f"Failed to download or extract 7-Zip portable: {e}")
                print(f"You can manually extract {installer_path} to {portable_dir} using 7-Zip.")
                return

        print(f"Running MEGAcmd installer in silent mode to app directory: {portable_dir}")
        try:
            # Run the installer with /S (silent) and /D=dir (custom install path, no trailing slash)
            install_dir = os.path.abspath(portable_dir)
            result = subprocess.run([
                os.path.abspath(installer_path),
                "/S",
                f"/D={install_dir}"
            ], capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                print("MEGAcmd installer failed. Output:")
                print(result.stdout)
                print(result.stderr)
                print(f"You may need to run the installer manually and select {portable_dir} as the install location.")
            else:
                print(f"MEGAcmd installed to {portable_dir}")
                # Attempt to clean up registry entries (best effort, Windows only)
                try:
                    import winreg
                    def delete_megacmd_keys():
                        for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                            try:
                                winreg.DeleteKey(root, r"Software\\MEGAcmd")
                            except FileNotFoundError:
                                pass
                    delete_megacmd_keys()
                    print("Attempted to remove MEGAcmd registry keys.")
                except Exception:
                    print("Could not clean registry (non-Windows or insufficient permissions).")
        except Exception as e:
            print(f"Installer failed: {e}")
            print(f"You may need to run the installer manually and select {portable_dir} as the install location.")

        # Clean up installer
        try:
            os.remove(installer_path)
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
