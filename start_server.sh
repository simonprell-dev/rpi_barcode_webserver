#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PORT="${PORT:-5000}"

get_ip_addresses() {
  local addresses
  addresses="$(
    ip -4 -o addr show up scope global 2>/dev/null \
      | awk '{print $4}' \
      | cut -d/ -f1 \
      | awk '!seen[$0]++'
  )"

  if [ -z "$addresses" ]; then
    addresses="$(
      hostname -I 2>/dev/null \
        | tr ' ' '\n' \
        | awk 'NF && $1 !~ /^127\./ && !seen[$1]++'
    )"
  fi

  printf '%s\n' "$addresses" | awk 'NF'
}

print_connection_info() {
  local addresses primary_ip display_url admin_url attempt
  addresses=()

  for attempt in $(seq 1 15); do
    mapfile -t addresses < <(get_ip_addresses)
    if [ "${#addresses[@]}" -gt 0 ]; then
      break
    fi
    sleep 1
  done

  echo "Raspberry Pi Barcode Webserver startet..."

  if [ "${#addresses[@]}" -eq 0 ]; then
    echo "Keine Netzwerk-IP erkannt. Pruefe LAN/WLAN mit: ip addr oder hostname -I"
    echo "Display: http://<raspberrypi-ip>:$PORT/display"
    echo "Admin:   http://<raspberrypi-ip>:$PORT/admin"
    return
  fi

  echo "Gefundene IP-Adresse(n): ${addresses[*]}"
  for ip in "${addresses[@]}"; do
    echo "Display: http://$ip:$PORT/display"
    echo "Admin:   http://$ip:$PORT/admin"
  done

  primary_ip="${addresses[0]}"
  display_url="http://$primary_ip:$PORT/display"
  admin_url="http://$primary_ip:$PORT/admin"

  echo "Primaere Display-URL: $display_url"
  echo "Primaere Admin-URL:   $admin_url"

  if command -v qrencode >/dev/null 2>&1; then
    echo "QR-Code fuer die Display-Seite:"
    qrencode -t ANSIUTF8 "$display_url"
  else
    echo "Kein QR-Code verfuegbar, weil 'qrencode' nicht installiert ist."
  fi
}

print_connection_info
if [ "${REPORT_ONLY:-0}" = "1" ]; then
  exit 0
fi

exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/app.py"
