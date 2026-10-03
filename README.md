# Offline Village Learning Hub - Northern Jordan

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Ubuntu_Linux-orange.svg)
![Environment](https://img.shields.io/badge/Environment-Offline_Rural-green.svg)

An offline-first educational server platform built to deliver Arabic learning resources, digital literacy tools, and introductory programming labs to students in rural villages across Northern Jordan without mobile data or internet dependencies.

## Why I Built This

This project began with my family. My cousins, uncles, and grandparents on both my mother's and father's sides live in Jordan. They come from families of modest means, and access to basic Wi-Fi, digital skills, and online learning opportunities is limited. These challenges extend beyond my relatives to the wider village community.

God has blessed me with access to technology, connectivity, and opportunities to learn. I felt a responsibility to use those blessings to help the people I love and the community they belong to. I took it upon myself to build an offline learning hub that everyone in the village could access, without needing mobile data or an internet connection.

My goal is to give people a place to explore educational resources, build digital confidence, and take their first steps in programming. This hub is my way of sharing what I have been given and helping make those learning opportunities accessible to my family, their neighbors, and the whole village.

— Ahmad Arrabee

## Key Features

- **Custom Local Portal:** Lightweight, responsive, RTL-optimized Arabic interface accessible over local Wi-Fi. A heartbeat checks the portal server immediately and every 10 seconds.
- **Kolibri LMS Integration:** Direct access to locally installed Kolibri for offline lessons, videos, quizzes, and learner accounts.
- **In-Browser Coding Lab:** Self-contained JavaScript editor with text-only output, error handling, a stop button, and a three-second worker timeout. No CDN, package installation, or internet connection is needed to run it.
- **Maintenance & Backup Automation:** Standard-library Python diagnostics and timestamped USB backups, with a systemd-compatible wrapper for scheduled, stopped-service snapshots.

Kolibri is installed separately; this repository does not bundle lessons or learner data. Import content before deployment, or transport it using USB. README badges require internet to display; all portal and lab assets are local.

## Team & Project Attribution

| Team member | Role | Responsibilities |
| --- | --- | --- |
| **Ahmad Arrabee** | Lead System Architect & Lead Developer | Platform design, Arabic portal, system scripts, network configuration |
| **Nour Momani** | Educational Content Facilitator | Student enrollment, offline lesson planning, Kolibri coordination |
| **Ahmad Obeidat** | Local Technical & Field Support | Hardware deployment, router maintenance, USB synchronization |
| **Fatima Zoubi** | Community & Student Outreach Coordinator | Session scheduling, device distribution, impact tracking |

## Hardware Specifications

| Subsystem | Component | Notes |
| --- | --- | --- |
| Server | Repurposed laptop, Ubuntu 22.04 LTS | Integrated battery provides short-term power resilience |
| Network | Dual-band Wi-Fi router | Ethernet connection to server; local Wi-Fi for students |
| Clients | Shared laptops/tablets | Modern browser supporting Web Workers |
| Storage | 512GB SSD + 128GB USB 3.0 | Local learning content and USB backups; USB must have room for each snapshot |

## Repository Layout

```text
offline-learning-hub/
├── README.md
├── LICENSE
├── custom_interface/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── programming_activities/
│   └── python_intro.html
├── maintenance/
│   ├── system_diagnostics.py
│   ├── auto_backup.py
│   └── backup_kolibri.sh
└── tests/
    ├── test_maintenance.py
    └── test_heartbeat.cjs
```

The requested filename `python_intro.html` is retained, but the exercise runs **JavaScript, not Python**. The worker captures `console.log()` and displays values as text. It supports synchronous exercises; asynchronous callbacks are stopped when the synchronous program finishes. A worker prevents accidental infinite loops from freezing the page, but is not a security sandbox for hostile code.

## Installation & Server Setup

Initial installation and downloading learning channels require internet, or separately prepared offline packages and USB content. Normal classroom use needs only the local network.

### 1. Prepare the local network

Reserve `192.168.1.100` for the server on the router's `192.168.1.0/24` LAN. Connect clients to that router. Update the Kolibri link in `custom_interface/index.html` if your server address differs. Turn off Wi-Fi client isolation if it prevents access to the server.

### 2. Install Kolibri from its PPA

For Ubuntu 22.04, use the signed-key PPA procedure in the [official Kolibri installation guide](https://kolibri.readthedocs.io/en/latest/install/ubuntu-debian.html):

```bash
sudo apt update
sudo apt install python3 gnupg dirmngr
sudo gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys DC5BAA93F9E4AE4F0411F97C74F88ADB3194DD81
sudo gpg --output /usr/share/keyrings/learningequality-kolibri.gpg --export DC5BAA93F9E4AE4F0411F97C74F88ADB3194DD81
echo 'deb [signed-by=/usr/share/keyrings/learningequality-kolibri.gpg] http://ppa.launchpad.net/learningequality/kolibri/ubuntu jammy main' | sudo tee /etc/apt/sources.list.d/learningequality-ubuntu-kolibri.list
sudo apt update
sudo apt install kolibri
```

Choose to run Kolibri as a system service when prompted. Then:

```bash
sudo systemctl enable --now kolibri
systemctl is-active kolibri
```

Open `http://192.168.1.100:8080`, complete facility setup, create learner accounts, and import Arabic channels. The library card is a noninteractive “Coming Soon” placeholder. Verify the real data directory in Kolibri's **Device > Info** screen: it may differ from `~/.kolibri` when installed as a service.

### 3. Host the local portal on port 80

Serve the **repository root**, so the sibling coding-lab path works:

```bash
cd /path/to/offline-learning-hub
sudo python3 -m http.server 80 --bind 192.168.1.100 --directory "$PWD"
```

Students open `http://192.168.1.100/custom_interface/index.html`. Port 80 requires elevated permissions; for development use `python3 -m http.server 8000 --bind 127.0.0.1` and open `http://127.0.0.1:8000/custom_interface/index.html`.

Python's HTTP server is a basic trusted-LAN demo server: keep this checkout free of private data and do not forward its port to the internet. For an unattended installation, use a dedicated static web server and a restricted document root. Allow TCP 80 and 8080 from the LAN if a host firewall is enabled. The portal status checks only the portal server, not internet availability or Kolibri health.

### 4. Run diagnostics

```bash
python3 maintenance/system_diagnostics.py
python3 maintenance/system_diagnostics.py --path /home/server
```

The script prints total/used/free capacity in GiB (1024³ bytes), and queries `systemctl is-active kolibri`. Exit status is `0` when checks succeed and the service is active; otherwise `1`. Missing `systemctl`, query timeouts, and stopped services are reported without a traceback.

### 5. Make a consistent USB backup

Mount the USB at `/media/server/BACKUP_USB`. The backup script verifies it is an actual mount point, then creates `kolibri_backups` inside it. Run as a user who can read the data and write the USB. Stop Kolibri before copying to keep its database consistent:

```bash
sudo systemctl stop kolibri
# Replace /home/server/.kolibri with the actual Device > Info data path.
sudo python3 maintenance/auto_backup.py --source /home/server/.kolibri --confirm-stopped
sudo systemctl start kolibri
```

Default source: the invoking user's `~/.kolibri`; default destination: `/media/server/BACKUP_USB/kolibri_backups`. `sudo` changes the default home, so always provide `--source` when using it. `--confirm-stopped` confirms that the operator has stopped all writers; it does not stop the service itself. Alternate mount points use `--mount /your/usb/mount`; `--backup-dir` must be a descendant of that mount.

Every completed snapshot has a unique timestamped folder. Failed copies retain a `.partial` suffix for inspection. No old backup is overwritten or automatically deleted; manage USB capacity before scheduling. Safely unmount the USB after completion.

### 6. Schedule backups (optional)

The included Bash wrapper requires a systemd-managed Kolibri service. It acquires a lock, stops Kolibri, copies data, and uses a trap to restart it if it was initially active, even when copying fails:

```bash
sudo bash maintenance/backup_kolibri.sh /home/server/.kolibri /media/server/BACKUP_USB
```

After verifying the paths and a manual backup, add a root crontab entry with `sudo crontab -e` for 02:00 daily (server local time), outside learning sessions:

```cron
0 2 * * * /bin/bash /opt/offline-learning-hub/maintenance/backup_kolibri.sh /home/server/.kolibri /media/server/BACKUP_USB >> /var/log/kolibri-backup.log 2>&1
```

Adjust `/opt/offline-learning-hub` to the checkout location. The USB must remain mounted, and root must have access. Check the log for failed runs and confirm the service restarted.

### 7. Restore a snapshot

Stop Kolibri, retain a separate copy of the current data, and copy a **completed** backup's contents into the actual Kolibri data directory. Restore ownership to the service user, restart Kolibri, then verify learner accounts and channel access. Test restores on a spare installation before relying on a backup. Snapshots preserve symlinks; externally linked content needs separate backup coverage.

## Verification

No Python third-party packages are needed. Development checks:

```bash
python3 -m unittest discover -s tests -v
node --check custom_interface/app.js
node tests/test_heartbeat.cjs
bash -n maintenance/backup_kolibri.sh
```

Tests cover backup success, unique names, missing sources, unmounted USBs, partial failures, service states, and heartbeat success/failure/timeout recovery. In a browser, verify Arabic layout at tablet/phone widths, literal HTML-looking output, syntax errors, multiple log arguments, and `while (true) {}` timeout/stop behavior. Ubuntu service and physical USB integration must also be verified on the deployment hardware.

## License

Distributed under the [MIT License](LICENSE). Kolibri and imported educational content retain their respective licenses.
