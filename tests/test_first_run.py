import json
import unittest

import app
import config


class FirstRunSmokeTest(unittest.TestCase):
    def setUp(self):
        self.runtime_files = [
            config.MAPPINGS_FILE,
            config.STATUS_FILE,
            config.SETTINGS_FILE,
        ]
        self.backups = {}
        for path in self.runtime_files:
            if path.exists():
                self.backups[path] = path.read_text(encoding="utf-8")
                path.unlink()

        if config.MEDIA_DIR.exists():
            self.media_backup = [p for p in config.MEDIA_DIR.iterdir() if p.is_file()]
        else:
            self.media_backup = []

        app.ensure_environment()
        self.client = app.app.test_client()

    def tearDown(self):
        for path in self.runtime_files:
            if path in self.backups:
                path.write_text(self.backups[path], encoding="utf-8")
            elif path.exists():
                path.unlink()

    def test_first_run_display_admin_and_status(self):
        display = self.client.get("/display")
        admin = self.client.get("/admin")
        status = self.client.get("/status.json")

        self.assertEqual(display.status_code, 200)
        self.assertEqual(admin.status_code, 200)
        self.assertEqual(status.status_code, 200)

        display_html = display.get_data(as_text=True)
        admin_html = admin.get_data(as_text=True)
        status_payload = status.get_json()

        self.assertIn("Keine Standardseite konfiguriert", display_html)
        self.assertIn("Es sind noch keine Zuordnungen vorhanden.", admin_html)
        self.assertEqual(status_payload["current_barcode"], "")
        self.assertEqual(status_payload["display_mode"], "default")
        self.assertEqual(status_payload["default_file"], "")
        self.assertEqual(status_payload["mappings_count"], 0)
        self.assertEqual(status_payload["file_count"], 0)

    def test_first_run_created_default_json_files(self):
        mappings = json.loads(config.MAPPINGS_FILE.read_text(encoding="utf-8"))
        status = json.loads(config.STATUS_FILE.read_text(encoding="utf-8"))
        settings = json.loads(config.SETTINGS_FILE.read_text(encoding="utf-8"))

        self.assertEqual(mappings, {})
        self.assertEqual(status, {"barcode": "", "updated": ""})
        self.assertEqual(settings["default_file"], "")
        self.assertEqual(settings["idle_timeout_seconds"], config.DEFAULT_IDLE_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
