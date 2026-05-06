import logging
import os
import struct
import threading
import time
from pathlib import Path


EV_KEY = 1
KEY_PRESS = 1
KEY_REPEAT = 2
SHIFT_CODES = {42, 54}
ENTER_CODES = {28, 96}

KEY_MAP = {
    2: ("1", "!"),
    3: ("2", "@"),
    4: ("3", "#"),
    5: ("4", "$"),
    6: ("5", "%"),
    7: ("6", "^"),
    8: ("7", "&"),
    9: ("8", "*"),
    10: ("9", "("),
    11: ("0", ")"),
    12: ("-", "_"),
    13: ("=", "+"),
    16: ("q", "Q"),
    17: ("w", "W"),
    18: ("e", "E"),
    19: ("r", "R"),
    20: ("t", "T"),
    21: ("y", "Y"),
    22: ("u", "U"),
    23: ("i", "I"),
    24: ("o", "O"),
    25: ("p", "P"),
    26: ("[", "{"),
    27: ("]", "}"),
    30: ("a", "A"),
    31: ("s", "S"),
    32: ("d", "D"),
    33: ("f", "F"),
    34: ("g", "G"),
    35: ("h", "H"),
    36: ("j", "J"),
    37: ("k", "K"),
    38: ("l", "L"),
    39: (";", ":"),
    40: ("'", '"'),
    41: ("`", "~"),
    43: ("\\", "|"),
    44: ("z", "Z"),
    45: ("x", "X"),
    46: ("c", "C"),
    47: ("v", "V"),
    48: ("b", "B"),
    49: ("n", "N"),
    50: ("m", "M"),
    51: (",", "<"),
    52: (".", ">"),
    53: ("/", "?"),
    55: ("*", "*"),
    57: (" ", " "),
    71: ("7", "7"),
    72: ("8", "8"),
    73: ("9", "9"),
    74: ("-", "-"),
    75: ("4", "4"),
    76: ("5", "5"),
    77: ("6", "6"),
    78: ("+", "+"),
    79: ("1", "1"),
    80: ("2", "2"),
    81: ("3", "3"),
    82: ("0", "0"),
    83: (".", "."),
}


class BarcodeInputListener:
    def __init__(self, on_barcode, logger=None, device_path=None):
        self.on_barcode = on_barcode
        self.logger = logger or logging.getLogger(__name__)
        self.device_path = device_path
        self.stop_event = threading.Event()
        self.thread = None
        self.buffer = []
        self.shift_down = False

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self.run, name="barcode-input-listener", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            path = self.device_path or find_keyboard_device()
            if not path:
                self.logger.info("No barcode keyboard device found; retrying")
                self.stop_event.wait(5)
                continue

            try:
                self.logger.info("Reading barcode scanner input from %s", path)
                self.read_device(path)
            except PermissionError:
                self.logger.exception("Permission denied reading barcode scanner device %s", path)
                self.stop_event.wait(10)
            except OSError:
                self.logger.exception("Barcode scanner device %s is not readable; retrying", path)
                self.stop_event.wait(2)
            except Exception:
                self.logger.exception("Barcode scanner listener failed; retrying")
                self.stop_event.wait(2)

    def read_device(self, path):
        event_format = "llHHI"
        event_size = struct.calcsize(event_format)
        with open(path, "rb", buffering=0) as device:
            while not self.stop_event.is_set():
                data = device.read(event_size)
                if len(data) != event_size:
                    time.sleep(0.05)
                    continue

                _, _, event_type, code, value = struct.unpack(event_format, data)
                if event_type != EV_KEY:
                    continue

                self.handle_key_event(code, value)

    def handle_key_event(self, code, value):
        if code in SHIFT_CODES:
            self.shift_down = value in (KEY_PRESS, KEY_REPEAT)
            return

        if value != KEY_PRESS:
            return

        if code in ENTER_CODES:
            barcode = "".join(self.buffer).strip()
            self.buffer = []
            if barcode:
                self.on_barcode(barcode)
            return

        key = KEY_MAP.get(code)
        if key:
            self.buffer.append(key[1] if self.shift_down else key[0])


def find_keyboard_device():
    configured = os.environ.get("BARCODE_SCANNER_DEVICE", "").strip()
    if configured:
        return configured

    by_id = Path("/dev/input/by-id")
    if by_id.exists():
        scanner_links = sorted(
            path for path in by_id.iterdir()
            if "event-kbd" in path.name and any(token in path.name.lower() for token in ("barcode", "scanner", "tot", "hid"))
        )
        if scanner_links:
            return str(scanner_links[0])

        keyboard_links = sorted(path for path in by_id.iterdir() if "event-kbd" in path.name)
        if keyboard_links:
            return str(keyboard_links[0])

    return None
