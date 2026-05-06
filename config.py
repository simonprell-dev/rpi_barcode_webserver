from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
MAPPINGS_FILE = BASE_DIR / "mappings.json"
STATUS_FILE = BASE_DIR / "status.json"
SETTINGS_FILE = BASE_DIR / "settings.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}
PDF_EXTENSIONS = {".pdf"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | PDF_EXTENSIONS | {".html"}
DEFAULT_IDLE_TIMEOUT_SECONDS = 300
