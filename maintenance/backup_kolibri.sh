#!/usr/bin/env bash
# Usage: sudo bash backup_kolibri.sh /actual/kolibri/data /mounted/usb
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 KOLIBRI_DATA_DIR USB_MOUNT" >&2
  exit 2
fi
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec 9>/run/lock/offline-learning-hub-backup.lock
flock -n 9 || { echo "Another backup is running" >&2; exit 1; }
# Verify the service exists and systemd is reachable before proceeding.
load_state="$(systemctl show kolibri --property=LoadState --value)"
[[ "$load_state" == "loaded" ]] || { echo "Kolibri service is not loaded" >&2; exit 1; }
was_active=0
if systemctl is-active --quiet kolibri; then was_active=1; fi
restart_kolibri() {
  result=$?
  trap - EXIT
  if [[ "$was_active" -eq 1 ]]; then
    if ! systemctl start kolibri; then
      echo "ERROR: could not restart Kolibri" >&2
      result=1
    fi
  fi
  exit "$result"
}
trap restart_kolibri EXIT
systemctl stop kolibri
python3 "$script_dir/auto_backup.py" --source "$1" --mount "$2" --confirm-stopped
