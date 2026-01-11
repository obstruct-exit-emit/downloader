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
    elif args.command == "pause":
        manager.pause(args.id)
    elif args.command == "resume":
        manager.resume(args.id)
    elif args.command == "remove":
        manager.remove(args.id)
    elif args.command == "status":
        manager.status(args.id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
