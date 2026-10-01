#!/usr/bin/env python3
"""Report local disk capacity and Kolibri's systemd service state."""

import argparse
import datetime
import shutil
import subprocess


def check_disk_space(path="/"):
    total, used, free = shutil.disk_usage(path)
    gb = 1024 ** 3
    print("--- Disk space / فحص المساحة (GiB) ---")
    print(f"Total: {total / gb:.2f} GiB")
    print(f"Used:  {used / gb:.2f} GiB")
    print(f"Free:  {free / gb:.2f} GiB\n")
    return total, used, free


def check_service_status(service_name="kolibri"):
    print(f"--- Service / حالة الخدمة: {service_name} ---")
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Cannot query systemctl: {error}")
        return False
    state = result.stdout.strip() or "unknown"
    print(f"State: {state.upper()}")
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.returncode == 0 and state == "active"


def run_diagnostics(path="/"):
    print(f"System diagnostics: {datetime.datetime.now().isoformat(timespec='seconds')}")
    try:
        check_disk_space(path)
    except OSError as error:
        print(f"Disk check failed: {error}")
        return 1
    return 0 if check_service_status() else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default="/", help="Filesystem path to inspect")
    raise SystemExit(run_diagnostics(parser.parse_args().path))
