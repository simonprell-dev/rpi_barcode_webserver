# Raspberry Pi Barcode Webserver

Dieses Projekt stellt einen einfachen Webserver fuer Raspberry Pi OS bereit, der Bilder, Videos, PDFs oder HTML-Dateien im Vollbild anzeigt. Die Auswahl erfolgt ueber einen Barcode-Scanner oder manuelle Texteingabe. Neue Dateien und Barcode-Zuordnungen werden ueber die Administrationsseite verwaltet.

## Funktionen

- `/display`: Barcode eingeben oder scannen und den zugeordneten Inhalt anzeigen
- `/admin`: Medien hochladen und Barcodes zuordnen
- Unterstuetzt Bilder, Videos, PDF und HTML
- Ungueltige Barcodes werden 3 Sekunden lang als Popup angezeigt
- Alle offenen Display-Seiten aktualisieren sich automatisch bei neuem Barcode
- Anzeige der lokalen Raspberry-Pi-IP(s), Dateianzahl und Zuordnungen auf der Display-Seite
- Fester Medienordner `media/` im Projektverzeichnis

## Schnellstart auf dem Raspberry Pi

Die schnellste Installation auf einem Raspberry Pi mit Raspberry Pi OS:

```bash
git clone https://github.com/simonprell-dev/rpi_barcode_webserver.git
cd rpi_barcode_webserver
sudo bash install.sh
```

Das Skript:

- installiert Python 3 und `pip`
- installiert `python3-venv`
- installiert die Python-Abhaengigkeiten aus `requirements.txt`
- erstellt eine lokale virtuelle Umgebung in `.venv/`
- legt `media/`, `mappings.json` und den systemd-Dienst an
- aktiviert und startet den Dienst automatisch

Danach ist die Anwendung unter `http://<raspberrypi-ip>:5000/display` erreichbar.

## Installation

Voraussetzung: Raspberry Pi OS mit Internetzugang.

Falls `git` noch nicht installiert ist:

```bash
sudo apt update
sudo apt install -y git
```

Repository klonen und Installation starten:

```bash
git clone https://github.com/simonprell-dev/rpi_barcode_webserver.git
cd rpi_barcode_webserver
sudo bash install.sh
```

Hinweis: `chmod +x install.sh` ist nicht noetig, weil das Skript direkt mit `bash` gestartet wird.

## Server manuell starten

Falls du den Dienst nicht nutzen willst, kannst du den Server auch direkt starten:

```bash
.venv/bin/python app.py
```

Der Server laeuft standardmaessig auf Port `5000`.

## Systemd-Service

Das Installationsskript erstellt automatisch `rpi_barcode_webserver.service`, aktiviert den Dienst und startet ihn direkt.

Dienststatus pruefen:

```bash
sudo systemctl status rpi_barcode_webserver.service
```

Dienst neu starten:

```bash
sudo systemctl restart rpi_barcode_webserver.service
```

Dienst deaktivieren und stoppen:

```bash
sudo systemctl disable --now rpi_barcode_webserver.service
```

Logs anzeigen:

```bash
journalctl -u rpi_barcode_webserver.service -f
```

## Update-Prozess

Wenn du spaeter Aenderungen aus GitHub uebernehmen willst:

```bash
cd ~/rpi_barcode_webserver
git pull
sudo bash install.sh
```

Damit werden Abhaengigkeiten und der Service bei Bedarf direkt mit aktualisiert.

## Nutzung

- Display-Seite im Browser oeffnen: `http://<raspberrypi-ip>:5000/display`
- Admin-Seite im Browser oeffnen: `http://<raspberrypi-ip>:5000/admin`
- Barcode scannen oder manuell eingeben und mit `Enter` bestaetigen
- Bei gueltigem Barcode wird das zugeordnete Medium angezeigt
- Bei ungueltigem Barcode erscheint unten rechts kurz ein Hinweis
- Offene Display-Seiten erkennen neue Barcodes automatisch und laden die passende Anzeige nach

## Admin-Bereich

Im Admin-Bereich kannst du:

- neue Dateien hochladen
- vorhandene Dateien einem Barcode zuordnen
- bestehende Barcode-Zuordnungen loeschen

Erlaubte Dateitypen:

- Bilder: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`
- Videos: `.mp4`, `.webm`, `.ogg`, `.mov`
- Dokumente: `.pdf`
- Webseiten: `.html`

## Projektstruktur

- `app.py`: Flask-Anwendung
- `config.py`: Pfade und erlaubte Dateitypen
- `media/`: hochgeladene Medien
- `mappings.json`: Barcode-Zuordnungen
- `status.json`: aktuell angezeigter Barcode fuer die automatische Aktualisierung

## Sicherheitshinweis

Der Admin-Bereich ist nicht passwortgeschuetzt. Setze den Server nur in einem vertrauenswuerdigen lokalen Netzwerk ein oder erweitere die Anwendung um eine Authentifizierung.

## Support

Bei Problemen helfen meist diese beiden Checks zuerst:

```bash
sudo systemctl status rpi_barcode_webserver.service
journalctl -u rpi_barcode_webserver.service -n 100
```
