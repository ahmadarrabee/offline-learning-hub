#!/usr/bin/env python3
"""Copy stopped Kolibri data to a mounted USB, then publish a complete snapshot."""

import argparse
import datetime
from pathlib import Path
import shutil
import uuid

KOLIBRI_DATA_DIR = Path.home() / ".kolibri"
USB_MOUNT = Path("/media/server/BACKUP_USB")
USB_BACKUP_DIR = USB_MOUNT / "kolibri_backups"


def create_backup(source=KOLIBRI_DATA_DIR, backup_dir=USB_BACKUP_DIR, mount=USB_MOUNT):
    """Caller must stop Kolibri before copying its database and content files."""
    source = Path(source).expanduser().resolve()
    backup_dir = Path(backup_dir).expanduser().resolve()
    mount = Path(mount).expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Kolibri data directory does not exist: {source}")
    if not mount.is_mount():
        raise OSError(f"USB is not mounted at: {mount}")
    if backup_dir == mount or mount not in backup_dir.parents:
        raise ValueError("Backup directory must be inside the USB mount")
    if backup_dir == source or source in backup_dir.parents or backup_dir in source.parents:
        raise ValueError("Source and backup directories must not overlap")

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S_%f")
    destination = backup_dir / f"backup_{stamp}_{uuid.uuid4().hex[:8]}"
    staging = backup_dir / f"{destination.name}.partial"
    print(f"Copying {source} to {destination}")
    try:
        # Never merge snapshots. Preserve symlinks rather than following them.
        shutil.copytree(source, staging, symlinks=True)
        staging.rename(destination)
    except Exception:
        # Keep partial files labelled for inspection; never report them as complete.
        print(f"Backup incomplete; inspect any partial data at {staging}")
        raise
    print(f"Backup complete: {destination}")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=KOLIBRI_DATA_DIR)
    parser.add_argument("--mount", type=Path, default=USB_MOUNT)
    parser.add_argument("--backup-dir", type=Path, help="Default: <mount>/kolibri_backups")
    parser.add_argument("--confirm-stopped", action="store_true", required=True,
                        help="Confirm Kolibri is stopped for a consistent backup")
    args = parser.parse_args()
    try:
        create_backup(args.source, args.backup_dir or args.mount / "kolibri_backups", args.mount)
    except (OSError, ValueError, shutil.Error) as error:
        print(f"Backup failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
