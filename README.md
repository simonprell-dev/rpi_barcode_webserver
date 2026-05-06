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

## Schnellstart

Wenn dein Raspberry Pi bereits laeuft und Internet hat:

```bash
git clone https://github.com/simonprell-dev/rpi_barcode_webserver.git
cd rpi_barcode_webserver
sudo bash install.sh
```

Nach der Installation zeigt das Skript die echte lokale IP-Adresse sowie beide Links an:

- `http://<raspberrypi-ip>:5000/display`
- `http://<raspberrypi-ip>:5000/admin`

## Komplette Schritt-fuer-Schritt-Anleitung

Diese Anleitung ist fuer Leute gedacht, die bei null starten.

### 1. Raspberry Pi Imager installieren

- Lade den Raspberry Pi Imager auf deinem PC oder Mac herunter und installiere ihn.
- Starte den Raspberry Pi Imager.

### 2. SD-Karte vorbereiten

- Waehle dein Raspberry-Pi-Modell aus.
- Waehle als Betriebssystem `Raspberry Pi OS`.
- Waehle deine SD-Karte aus.

### 3. OS-Anpassungen im Imager setzen

Bevor du schreibst, oeffne im Imager die erweiterten Einstellungen und setze mindestens diese Punkte:

- Hostname vergeben, zum Beispiel `barcode-scanner`
- WLAN eintragen, falls der Pi per WLAN ins Netzwerk soll
- SSH aktivieren
- Benutzername und Passwort festlegen
- Zeitzone und Tastaturlayout einstellen

Dann das Image auf die SD-Karte schreiben.

### 4. Raspberry Pi starten

- SD-Karte in den Raspberry Pi stecken
- Raspberry Pi mit Strom versorgen
- Warten, bis der erste Start abgeschlossen ist

### 5. Mit Raspberry Pi Connect oder SSH verbinden

Du hast jetzt zwei einfache Wege:

- `Raspberry Pi Connect`: Gut, wenn du lieber ueber den Browser auf den Pi zugreifen willst
- `SSH`: Gut, wenn du direkt ein Terminal nutzen willst

#### Raspberry Pi Connect

- Melde dich auf dem Raspberry Pi mit Desktop an
- Oeffne `Raspberry Pi Connect`
- Verbinde den Pi mit deinem Raspberry-Pi-Konto
- Oeffne danach den Pi ueber den Browser auf deinem Hauptrechner
- Oeffne dort ein Terminal

#### SSH

- Finde die IP-Adresse deines Raspberry Pi im Router oder ueber einen Netzwerkscan
- Verbinde dich vom Hauptrechner:

```bash
ssh <dein-benutzername>@<raspberrypi-ip>
```

Beispiel:

```bash
ssh blabsps@192.168.178.50
```

### 6. Git installieren

Falls `git` noch nicht installiert ist:

```bash
sudo apt update
sudo apt install -y git
```

### 7. Projekt herunterladen

```bash
git clone https://github.com/simonprell-dev/rpi_barcode_webserver.git
cd rpi_barcode_webserver
```

### 8. Webserver installieren

```bash
sudo bash install.sh
```

Das Skript:

- installiert Python 3, `pip` und `python3-venv`
- erstellt eine lokale virtuelle Umgebung in `.venv/`
- installiert die Python-Abhaengigkeiten aus `requirements.txt`
- legt `media/`, `mappings.json` und den systemd-Dienst an
- aktiviert und startet den Dienst automatisch
- zeigt danach die echte lokale IP-Adresse und die Browser-Links an

### 9. Im Browser oeffnen

Nach erfolgreicher Installation siehst du im Terminal so etwas in der Art:

```text
Gefundene IP-Adresse(n): 192.168.178.50
Display: http://192.168.178.50:5000/display
Admin:   http://192.168.178.50:5000/admin
```

Diese Links kannst du dann auf jedem Geraet im selben Netzwerk im Browser oeffnen.

## Nutzung

- Display-Seite im Browser oeffnen: `http://<raspberrypi-ip>:5000/display`
- Admin-Seite im Browser oeffnen: `http://<raspberrypi-ip>:5000/admin`
- Im Admin-Bereich Medien hochladen oder vorhandene Dateien einem Barcode zuordnen
- Auf der Display-Seite Barcode scannen oder manuell eingeben und mit `Enter` bestaetigen
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

## Manuell starten

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
