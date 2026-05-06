# Raspberry Pi Barcode Webserver

Dieses Projekt stellt einen einfachen Webserver für Raspberry Pi OS bereit, der Bilder oder HTML-Dateien im Vollbild anzeigt. Die Auswahl erfolgt über einen Barcode-Scanner oder manuelle Texteingabe. Neue Dateien und Barcode-Zuordnungen werden über die Administrationsseite verwaltet.

## Funktionen

- `/display`: Eingabe eines Barcodes und Anzeige des zugeordneten Bildes, HTML-, PDF- oder Video-Inhalts im Vollbild
- `/admin`: Hochladen von Medien und Anlernen neuer Barcode-Zuordnungen
- Automatische Anzeige eines kurzen Popups bei ungültigem Barcode (3 Sekunden)
- Feste Medien-Direktive im Verzeichnis `media/`
- Anzeige der lokalen RPi-IP(s) und Verzeichnisinformation im Display
- Alle geöffneten Browser aktualisieren sich automatisch, wenn ein neuer Barcode geladen wird

## Installation

1. Klone oder kopiere das Projekt auf den Raspberry Pi.
2. Wechsle in das Projektverzeichnis:

```bash
cd ~/rpi_barcode_webserver
```

3. Setze das Installationsskript ausführbar:

```bash
sudo chmod +x install.sh
```

4. Führe das Installationsskript aus:

```bash
sudo ./install.sh
```

Das Skript installiert Python3, pip und die benötigten Python-Pakete und legt das `media/`-Verzeichnis sowie `mappings.json` an.

## Starten des Servers

Starte den Webserver manuell mit:

```bash
python3 app.py
```

Der Server läuft dann standardmäßig auf Port `5000`.

## Systemd-Service

Das Installationsskript legt automatisch einen systemd-Dienst namens `rpi_barcode_webserver.service` an und startet ihn. Der Dienst ist so konfiguriert, dass er beim Boot automatisch gestartet wird.

- Prüfen, ob der Dienst läuft:

```bash
sudo systemctl status rpi_barcode_webserver.service
```

- Bei Bedarf deaktivieren und stoppen:

```bash
sudo systemctl disable --now rpi_barcode_webserver.service
```

- Falls die Datei an einem anderen Ort liegt, passe die `WorkingDirectory`- und `ExecStart`-Pfadwerte in `/etc/systemd/system/rpi_barcode_webserver.service` an und lade systemd neu:

```bash
sudo systemctl daemon-reload
sudo systemctl restart rpi_barcode_webserver.service
```

## Nutzung

- Öffne im Browser `http://<raspberrypi-ip>:5000/display`
- Scanne den Barcode in das Eingabefeld oder tippe den Code per Tastatur ein und drücke `Enter`
- Bei einem gültigen Barcode wird das zugeordnete Bild, Video, HTML- oder PDF-Dokument angezeigt
- Auf der Display-Seite werden die lokale RPi-IP-Adresse(n) und das Medienverzeichnis angezeigt
- Alle Browser auf dieser Seite prüfen im Hintergrund alle paar Sekunden, ob ein neuer Barcode geladen wurde, und aktualisieren sich dann automatisch
- Bei einem falschen Barcode erscheint unten rechts ein kurzes Popup für 3 Sekunden

## Admin-Bereich

- Öffne `http://<raspberrypi-ip>:5000/admin`
- Lade ein Bild oder eine `.html`-Datei hoch
- Gib einen Barcode ein, der dem Medium zugeordnet werden soll
- Alternativ kannst du auch eine bereits vorhandene Datei auswählen und einem Barcode zuordnen
- Bestehende Zuordnungen können über die Admin-Oberfläche gelöscht werden

## Medienordner

Alle Medien werden im festen Verzeichnis `media/` abgelegt. Dort können Bilder (`.jpg`, `.png`, `.gif`, `.webp`, `.svg`) und HTML-Dateien (`.html`) liegen.

## Sicherheitshinweis

Der Admin-Bereich ist nicht passwortgeschützt. Setze den Server nur in einem sicheren lokalen Netzwerk ein oder erweitere die Anwendung mit einer Authentifizierung, falls dies erforderlich ist.

## Support

Bei Problemen prüfe zunächst die Konsole, in der der Flask-Server läuft. Achte darauf, dass Barcode-Eingaben exakt den hinterlegten Zuordnungen entsprechen.
