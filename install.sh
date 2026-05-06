#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Bitte das Installationsskript mit sudo ausfuehren."
  exit 1
fi

echo "Aktualisiere Paketquellen..."
apt update

echo "Installiere Python3, venv und pip..."
apt install -y python3 python3-pip python3-venv

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

SERVICE_FILE="/etc/systemd/system/rpi_barcode_webserver.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Raspberry Pi Barcode Webserver
After=network.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now rpi_barcode_webserver.service

IP_ADDRESSES="$(hostname -I 2>/dev/null | xargs)"

echo "Installiert. Projektverzeichnis: $SCRIPT_DIR"
echo "Der systemd-Dienst rpi_barcode_webserver.service wurde aktiviert und gestartet."
if [ -n "$IP_ADDRESSES" ]; then
  echo "Gefundene IP-Adresse(n): $IP_ADDRESSES"
  for ip in $IP_ADDRESSES; do
    echo "Display: http://$ip:5000/display"
    echo "Admin:   http://$ip:5000/admin"
  done
else
  echo "Keine IP-Adresse erkannt. Pruefe mit: hostname -I"
  echo "Display: http://<raspberrypi-ip>:5000/display"
  echo "Admin:   http://<raspberrypi-ip>:5000/admin"
fi
