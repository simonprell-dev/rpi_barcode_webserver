#!/usr/bin/env python3

import json
import logging
import os
import socket
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-this-secret-key")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


def default_settings():
    return {
        "default_file": "",
        "idle_timeout_seconds": config.DEFAULT_IDLE_TIMEOUT_SECONDS,
    }


def ensure_environment():
    config.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not config.MAPPINGS_FILE.exists():
        config.MAPPINGS_FILE.write_text(json.dumps({}, indent=2), encoding="utf-8")
    if not config.STATUS_FILE.exists():
        config.STATUS_FILE.write_text(json.dumps({"barcode": "", "updated": ""}, indent=2), encoding="utf-8")
    if not config.SETTINGS_FILE.exists():
        config.SETTINGS_FILE.write_text(json.dumps(default_settings(), indent=2), encoding="utf-8")


ensure_environment()


def configure_logging():
    if any(getattr(handler, "baseFilename", None) == str(config.ERROR_LOG_FILE) for handler in app.logger.handlers):
        return

    file_handler = RotatingFileHandler(
        config.ERROR_LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s [in %(pathname)s:%(lineno)d]"
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


configure_logging()


def load_mappings():
    try:
        with config.MAPPINGS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_mappings(mappings):
    with config.MAPPINGS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(mappings, handle, indent=2, ensure_ascii=False)


def load_status():
    try:
        with config.STATUS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                return {
                    "barcode": str(data.get("barcode", "") or ""),
                    "updated": str(data.get("updated", "") or ""),
                }
            return {"barcode": "", "updated": ""}
    except Exception:
        return {"barcode": "", "updated": ""}


def save_status(barcode):
    status = {"barcode": barcode, "updated": datetime.now(timezone.utc).isoformat()}
    with config.STATUS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(status, handle, indent=2, ensure_ascii=False)
    return status


def load_settings():
    settings = default_settings()
    try:
        with config.SETTINGS_FILE.open("r", encoding="utf-8") as handle:
            raw_settings = json.load(handle)
            if isinstance(raw_settings, dict):
                settings.update(raw_settings)
    except Exception:
        pass

    default_file = settings.get("default_file", "")
    if not isinstance(default_file, str):
        default_file = ""
    if default_file and not allowed_file(default_file):
        default_file = ""

    try:
        idle_timeout_seconds = int(settings.get("idle_timeout_seconds", config.DEFAULT_IDLE_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        idle_timeout_seconds = config.DEFAULT_IDLE_TIMEOUT_SECONDS

    settings["default_file"] = default_file
    settings["idle_timeout_seconds"] = max(10, idle_timeout_seconds)
    return settings


def save_settings(settings):
    clean_settings = {
        "default_file": settings.get("default_file", ""),
        "idle_timeout_seconds": max(10, int(settings.get("idle_timeout_seconds", config.DEFAULT_IDLE_TIMEOUT_SECONDS))),
    }
    with config.SETTINGS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(clean_settings, handle, indent=2, ensure_ascii=False)


def get_media_files():
    ensure_environment()
    return sorted([f.name for f in config.MEDIA_DIR.iterdir() if f.is_file() and allowed_file(f.name)])


def get_file_count():
    ensure_environment()
    return sum(1 for f in config.MEDIA_DIR.iterdir() if f.is_file())


def allowed_file(filename):
    if not isinstance(filename, str):
        return False
    return Path(filename).suffix.lower() in config.ALLOWED_EXTENSIONS


def get_local_ip_addresses():
    addresses = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip and "." in ip and not ip.startswith("127."):
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


def parse_timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def resolve_item_from_filename(filename):
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


def resolve_item(barcode):
    mappings = load_mappings()
    filename = mappings.get(barcode) if isinstance(mappings, dict) else None
    return resolve_item_from_filename(filename)


def get_default_item(settings=None):
    settings = settings or load_settings()
    return resolve_item_from_filename(settings.get("default_file", ""))


def get_active_display_state(settings=None, status=None):
    settings = settings or load_settings()
    status = status or load_status()
    barcode = (status.get("barcode") or "").strip()
    updated_at = parse_timestamp(status.get("updated"))

    active_item = None
    active_barcode = ""
    if barcode and updated_at:
        expires_at = updated_at + timedelta(seconds=settings["idle_timeout_seconds"])
        if datetime.now(timezone.utc) < expires_at:
            active_item = resolve_item(barcode)
            if active_item:
                active_barcode = barcode

    if active_item:
        return {
            "mode": "barcode",
            "barcode": active_barcode,
            "item": active_item,
            "updated": status.get("updated", ""),
        }

    return {
        "mode": "default",
        "barcode": "",
        "item": get_default_item(settings),
        "updated": status.get("updated", ""),
    }


def build_admin_rows(mappings, active_barcode):
    rows = []
    for barcode, filename in sorted(mappings.items()):
        rows.append({
            "barcode": barcode,
            "filename": filename,
            "is_active": barcode == active_barcode,
        })
    return rows


def render_admin_page(mappings=None, settings=None):
    ensure_environment()
    mappings = mappings if mappings is not None else load_mappings()
    settings = settings or load_settings()
    media_files = get_media_files()
    active_state = get_active_display_state(settings=settings)
    return render_template(
        "admin.html",
        mappings=mappings,
        mapping_rows=build_admin_rows(mappings, active_state["barcode"]),
        media_files=media_files,
        settings=settings,
        idle_timeout_minutes=max(1, settings["idle_timeout_seconds"] // 60),
        active_state=active_state,
    )


def render_display_page(error=None):
    ensure_environment()
    settings = load_settings()
    state = get_active_display_state(settings=settings)
    return render_template(
        "display.html",
        barcode=state["barcode"],
        item=state["item"],
        error=error,
        local_ips=get_local_ip_addresses(),
        media_dir=str(config.MEDIA_DIR),
        mapping_count=len(load_mappings()),
        file_count=get_file_count(),
        idle_timeout_seconds=settings["idle_timeout_seconds"],
        default_file=settings.get("default_file", ""),
        display_mode=state["mode"],
        state_updated=state.get("updated", ""),
        status_endpoint=url_for("status_json"),
        scan_endpoint=url_for("scan_barcode"),
        display_url=url_for("display"),
    )


@app.route("/")
def index():
    return redirect(url_for("display"))


@app.route("/display")
def display():
    return render_display_page()


@app.route("/display/<barcode>")
def display_barcode(barcode):
    item = resolve_item(barcode)
    if item:
        save_status(barcode)
        return redirect(url_for("display"))
    return render_display_page(error="Barcode nicht erkannt.")


@app.route("/scan", methods=["POST"])
def scan_barcode():
    barcode = request.form.get("barcode", "").strip()
    if not barcode:
        return jsonify({"ok": False, "error": "Bitte Barcode scannen oder eingeben."}), 400

    item = resolve_item(barcode)
    if not item:
        return jsonify({"ok": False, "error": "Barcode nicht erkannt."}), 404

    save_status(barcode)
    return jsonify({"ok": True, "redirect_url": url_for("display"), "barcode": barcode})


@app.route("/status.json")
def status_json():
    settings = load_settings()
    state = get_active_display_state(settings=settings)
    return jsonify({
        "current_barcode": state["barcode"],
        "display_mode": state["mode"],
        "display_url": url_for("display"),
        "updated": state.get("updated", ""),
        "media_dir": str(config.MEDIA_DIR),
        "mappings_file": str(config.MAPPINGS_FILE),
        "settings_file": str(config.SETTINGS_FILE),
        "default_file": settings.get("default_file", ""),
        "idle_timeout_seconds": settings["idle_timeout_seconds"],
        "file_count": get_file_count(),
        "mappings_count": len(load_mappings()),
        "ip_addresses": get_local_ip_addresses(),
        "has_item": bool(state["item"]),
    })


@app.route("/media/<path:filename>")
def media_file(filename):
    return send_from_directory(config.MEDIA_DIR, filename)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    ensure_environment()
    mappings = load_mappings()
    settings = load_settings()
    media_files = get_media_files()

    if request.method == "POST":
        action = request.form.get("action", "mapping")

        if action == "settings":
            default_file = request.form.get("default_file", "").strip()
            idle_timeout_minutes = request.form.get("idle_timeout_minutes", "").strip()

            if default_file and default_file not in media_files:
                flash("Die ausgewaehlte Default-Datei existiert nicht.", "error")
                return render_admin_page(mappings=mappings, settings=settings)

            try:
                idle_timeout_minutes_value = int(idle_timeout_minutes)
            except ValueError:
                flash("Bitte eine gueltige Zahl fuer die Inaktivitaetszeit eingeben.", "error")
                return render_admin_page(mappings=mappings, settings=settings)

            settings["default_file"] = default_file
            settings["idle_timeout_seconds"] = max(1, idle_timeout_minutes_value) * 60
            save_settings(settings)
            flash("Display-Standardseite und Inaktivitaetszeit wurden gespeichert.", "success")
            return redirect(url_for("admin"))

        if action == "activate":
            barcode = request.form.get("barcode", "").strip()
            if not barcode:
                flash("Bitte einen Barcode zum Aktivieren angeben.", "error")
                return render_admin_page(mappings=mappings, settings=settings)

            item = resolve_item(barcode)
            if not item:
                flash("Der Barcode ist keiner Datei zugeordnet.", "error")
                return render_admin_page(mappings=mappings, settings=settings)

            save_status(barcode)
            flash(f"Anzeige fuer Barcode '{barcode}' aktiviert.", "success")
            return redirect(url_for("admin"))

        barcode = request.form.get("barcode", "").strip()
        existing_file = request.form.get("existing_file", "").strip()
        upload = request.files.get("file")

        if not barcode:
            flash("Bitte einen Barcode eingeben.", "error")
            return render_admin_page(mappings=mappings, settings=settings)

        target_filename = None

        if upload and upload.filename:
            filename = secure_filename(upload.filename)
            if not allowed_file(filename):
                flash("Ungueltiger Dateityp. Erlaubt sind Bilder, Videos, PDF und HTML.", "error")
                return render_admin_page(mappings=mappings, settings=settings)

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
                flash("Die ausgewaehlte Datei existiert nicht.", "error")
                return render_admin_page(mappings=mappings, settings=settings)
        else:
            flash("Bitte eine Datei auswaehlen oder hochladen.", "error")
            return render_admin_page(mappings=mappings, settings=settings)

        mappings[barcode] = target_filename
        save_mappings(mappings)
        flash(f"Barcode '{barcode}' mit '{target_filename}' verknuepft.", "success")
        return redirect(url_for("admin"))

    return render_admin_page(mappings=mappings, settings=settings)


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    barcode = request.form.get("delete_barcode", "").strip()
    mappings = load_mappings()
    if barcode in mappings:
        mappings.pop(barcode)
        save_mappings(mappings)
        flash(f"Zuordnung fuer Barcode '{barcode}' entfernt.", "success")
    else:
        flash("Zuordnung nicht gefunden.", "error")
    return redirect(url_for("admin"))


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception(
        "Unhandled exception for %s %s from %s",
        request.method,
        request.path,
        request.remote_addr,
    )
    return (
        render_template(
            "error.html",
            error_message="Ein unerwarteter Fehler ist aufgetreten. Details stehen im Fehlerlog.",
            error_log=str(config.ERROR_LOG_FILE),
        ),
        500,
    )


if __name__ == "__main__":
    ensure_environment()
    app.run(host="0.0.0.0", port=5000)
