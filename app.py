#!/usr/bin/env python3

import json
import os
import socket
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import config

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret-key")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def ensure_environment():
    config.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    if not config.MAPPINGS_FILE.exists():
        config.MAPPINGS_FILE.write_text(json.dumps({}, indent=2), encoding="utf-8")
    if not config.STATUS_FILE.exists():
        config.STATUS_FILE.write_text(json.dumps({"barcode": "", "updated": ""}, indent=2), encoding="utf-8")

ensure_environment()


def load_mappings():
    try:
        with config.MAPPINGS_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def save_mappings(mappings):
    with config.MAPPINGS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(mappings, handle, indent=2, ensure_ascii=False)


def load_status():
    try:
        with config.STATUS_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {"barcode": "", "updated": ""}


def save_status(barcode):
    status = {"barcode": barcode, "updated": datetime.utcnow().isoformat() + "Z"}
    with config.STATUS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2, ensure_ascii=False)
    return status


def allowed_file(filename):
    return Path(filename).suffix.lower() in config.ALLOWED_EXTENSIONS


def get_local_ip_addresses():
    addresses = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                addresses.add(ip)
    except Exception:
        pass
    if not addresses:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                addresses.add(sock.getsockname()[0])
        except Exception:
            pass
    if not addresses:
        addresses.add("127.0.0.1")
    return sorted(addresses)


def resolve_item(barcode):
    mappings = load_mappings()
    filename = mappings.get(barcode)
    if not filename:
        return None
    safe_path = config.MEDIA_DIR / filename
    if not safe_path.exists() or not allowed_file(filename):
        return None
    suffix = Path(filename).suffix.lower()
    if suffix == ".html" or suffix in config.PDF_EXTENSIONS:
        item_type = "html"
    elif suffix in config.VIDEO_EXTENSIONS:
        item_type = "video"
    else:
        item_type = "image"
    return {
        "filename": filename,
        "type": item_type,
    }


@app.route("/")
def index():
    return redirect(url_for("display"))


@app.route("/display", methods=["GET", "POST"])
def display():
    error = None
    barcode = ""
    item = None

    if request.method == "POST":
        barcode = request.form.get("barcode", "").strip()
        if not barcode:
            error = "Bitte Barcode scannen oder eingeben."
        else:
            item = resolve_item(barcode)
            if item:
                return redirect(url_for("display_barcode", barcode=barcode))
            error = "Barcode nicht erkannt."

    return render_template(
        "display.html",
        barcode=barcode,
        item=item,
        error=error,
        local_ips=get_local_ip_addresses(),
        media_dir=str(config.MEDIA_DIR),
        mapping_count=len(load_mappings()),
        file_count=sum(1 for f in config.MEDIA_DIR.iterdir() if f.is_file()),
    )


@app.route("/display/<barcode>")
def display_barcode(barcode):
    item = resolve_item(barcode)
    error = None
    if not item:
        error = "Barcode nicht erkannt."
    else:
        save_status(barcode)
    return render_template(
        "display.html",
        barcode=barcode,
        item=item,
        error=error,
        local_ips=get_local_ip_addresses(),
        media_dir=str(config.MEDIA_DIR),
        mapping_count=len(load_mappings()),
        file_count=sum(1 for f in config.MEDIA_DIR.iterdir() if f.is_file()),
    )


@app.route("/status.json")
def status_json():
    status = load_status()
    return jsonify({
        "current_barcode": status.get("barcode", ""),
        "updated": status.get("updated", ""),
        "media_dir": str(config.MEDIA_DIR),
        "mappings_file": str(config.MAPPINGS_FILE),
        "file_count": sum(1 for f in config.MEDIA_DIR.iterdir() if f.is_file()),
        "mappings_count": len(load_mappings()),
        "ip_addresses": get_local_ip_addresses(),
    })


@app.route("/media/<path:filename>")
def media_file(filename):
    return send_from_directory(config.MEDIA_DIR, filename)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    ensure_environment()
    mappings = load_mappings()
    media_files = sorted([f.name for f in config.MEDIA_DIR.iterdir() if f.is_file() and allowed_file(f.name)])

    if request.method == "POST":
        barcode = request.form.get("barcode", "").strip()
        existing_file = request.form.get("existing_file", "").strip()
        upload = request.files.get("file")

        if not barcode:
            flash("Bitte einen Barcode eingeben.", "error")
            return render_template("admin.html", mappings=mappings, media_files=media_files)

        target_filename = None

        if upload and upload.filename:
            filename = secure_filename(upload.filename)
            if not allowed_file(filename):
                flash("Ungültiger Dateityp. Erlaubt sind Bilder, Videos, PDF und HTML.", "error")
                return render_template("admin.html", mappings=mappings, media_files=media_files)

            target = config.MEDIA_DIR / filename
            counter = 1
            while target.exists():
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                target = config.MEDIA_DIR / f"{stem}_{counter}{suffix}"
                counter += 1
            upload.save(target)
            target_filename = target.name
            flash(f"Datei '{target.name}' erfolgreich hochgeladen.", "success")
        elif existing_file:
            if existing_file in media_files:
                target_filename = existing_file
            else:
                flash("Die ausgewählte Datei existiert nicht.", "error")
                return render_template("admin.html", mappings=mappings, media_files=media_files)
        else:
            flash("Bitte eine Datei auswählen oder hochladen.", "error")
            return render_template("admin.html", mappings=mappings, media_files=media_files)

        mappings[barcode] = target_filename
        save_mappings(mappings)
        flash(f"Barcode '{barcode}' mit '{target_filename}' verknüpft.", "success")
        return redirect(url_for("admin"))

    return render_template("admin.html", mappings=mappings, media_files=media_files)


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    barcode = request.form.get("delete_barcode", "").strip()
    mappings = load_mappings()
    if barcode in mappings:
        mappings.pop(barcode)
        save_mappings(mappings)
        flash(f"Zuordnung für Barcode '{barcode}' entfernt.", "success")
    else:
        flash("Zuordnung nicht gefunden.", "error")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    ensure_environment()
    app.run(host="0.0.0.0", port=5000)
