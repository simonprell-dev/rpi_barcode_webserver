#!/bin/bash
set -e

if [ "$(id -u)" -eq 0 ]; then
  echo "Bitte update.sh ohne sudo ausfuehren. Das Skript ruft sudo nur fuer die Installation auf."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "Git ist nicht installiert. Bitte zuerst 'sudo apt install -y git' ausfuehren."
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Dieses Verzeichnis ist kein Git-Repository: $SCRIPT_DIR"
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [ -z "$CURRENT_BRANCH" ] || [ "$CURRENT_BRANCH" = "HEAD" ]; then
  echo "Konnte keinen gueltigen Git-Branch ermitteln."
  exit 1
fi

echo "Aktualisiere Repository auf den neuesten Stand von origin/$CURRENT_BRANCH..."
git fetch origin
git pull --ff-only origin "$CURRENT_BRANCH"

echo "Fuehre die Installation erneut aus..."
sudo bash "$SCRIPT_DIR/install.sh"

echo "Update abgeschlossen."
