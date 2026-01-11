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


    # List downloads
    subparsers.add_parser("list", help="List all downloads")

    # Download portable aria2
    subparsers.add_parser("get-aria2", help="Download portable aria2c.exe for Windows into project directory")

    # Download portable MegaCMD
    subparsers.add_parser("get-mega", help="Download portable megacmd for Windows into project directory")

    # Pause/resume/remove
    for cmd in ["pause", "resume", "remove", "status"]:
        p = subparsers.add_parser(cmd, help=f"{cmd.capitalize()} a download")
        p.add_argument("id", nargs="?", help="Download ID")


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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
