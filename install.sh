#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte das Installationsskript mit sudo ausfuehren."
  exit 1
fi

echo "Aktualisiere Paketquellen..."
apt update

echo "Installiere Python3, venv, pip und qrencode..."
apt install -y python3 python3-pip python3-venv qrencode

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEDIA_DIR="$SCRIPT_DIR/media"
MAPPINGS_FILE="$SCRIPT_DIR/mappings.json"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "Installiere Python-Abhaengigkeiten..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

mkdir -p "$MEDIA_DIR"
if [ ! -f "$MAPPINGS_FILE" ]; then
  python3 - <<PY
from pathlib import Path
import json
Path("$MAPPINGS_FILE").write_text(json.dumps({}, indent=2), encoding="utf-8")
PY
fi

chmod +x "$SCRIPT_DIR/app.py"
chmod +x "$SCRIPT_DIR/start_server.sh"

SERVICE_FILE="/etc/systemd/system/rpi_barcode_webserver.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Raspberry Pi Barcode Webserver
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=/bin/bash $SCRIPT_DIR/start_server.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now rpi_barcode_webserver.service

echo "Installiert. Projektverzeichnis: $SCRIPT_DIR"
echo "Der systemd-Dienst rpi_barcode_webserver.service wurde aktiviert und gestartet."
REPORT_ONLY=1 /bin/bash "$SCRIPT_DIR/start_server.sh" >/tmp/rpi_barcode_webserver_startup_preview.log 2>&1 || true
sed '/^$/d' /tmp/rpi_barcode_webserver_startup_preview.log | sed '/^\* Serving Flask app/d;/^\* Debug mode/d;/^WARNING: This is a development server/d;/^\* Running on /d;/^Press CTRL+C to quit/d'
rm -f /tmp/rpi_barcode_webserver_startup_preview.log
