import json
import logging
import os
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv


# ============================================================
# LOGGING SETUP
# ============================================================

LOG_FILE = "easytime_zoho.log"

logger = logging.getLogger("EasyTimeZoho")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(console_formatter)

# Rotating file handler (5 MB max per file, 5 backups)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def log(msg):
    logger.info(msg)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")

ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in"
ZOHO_PEOPLE_URL = "https://people.zoho.in"

HOST = "0.0.0.0"
PORT = 8000

PROCESSED_FILE = "processed_punches.json"

# Cutoff date: only sync punches on or after this timestamp
SYNC_FROM_DATE_ENV = os.getenv("SYNC_FROM_DATE", "today").strip().lower()


def get_sync_cutoff():
    if SYNC_FROM_DATE_ENV == "today" or not SYNC_FROM_DATE_ENV:
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"]:
        try:
            return datetime.strptime(SYNC_FROM_DATE_ENV, fmt)
        except ValueError:
            pass
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


SYNC_CUTOFF = get_sync_cutoff()


# ============================================================
# CHECK CREDENTIALS
# ============================================================

if not ZOHO_CLIENT_ID:
    raise Exception("ZOHO_CLIENT_ID missing in .env")

if not ZOHO_CLIENT_SECRET:
    raise Exception("ZOHO_CLIENT_SECRET missing in .env")

if not ZOHO_REFRESH_TOKEN:
    raise Exception("ZOHO_REFRESH_TOKEN missing in .env")


# ============================================================
# PROCESSED PUNCHES
# ============================================================

def load_processed():

    if not os.path.exists(PROCESSED_FILE):
        return set()

    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))

    except Exception:
        return set()


def save_processed(processed):

    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, indent=2)


processed_punches = load_processed()


# In-memory token cache
_cached_token = None
_token_expiry = 0


# ============================================================
# ZOHO ACCESS TOKEN
# ============================================================

def get_access_token():
    global _cached_token, _token_expiry

    current_time = time.time()
    if _cached_token and current_time < _token_expiry:
        return _cached_token

    url = f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token"

    params = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    log("Getting new Zoho access token...")

    response = requests.post(
        url,
        params=params,
        timeout=30
    )

    log(f"OAuth HTTP: {response.status_code}")

    if response.status_code != 200:
        log(f"OAuth response: {response.text}")
        raise Exception("Unable to obtain Zoho access token")

    data = response.json()

    if "access_token" not in data:
        log(f"OAuth response: {data}")
        raise Exception("No access_token returned by Zoho")

    _cached_token = data["access_token"]
    # Cache for 55 minutes (tokens are valid for 60 minutes)
    _token_expiry = current_time + data.get("expires_in", 3600) - 300
    return _cached_token


def extract_field(record, keys):
    for key in keys:
        if key in record and record[key] is not None:
            val = str(record[key]).strip()
            if val:
                return val
    return ""


def parse_punch_datetime(val):
    if not val:
        return None, None
    val = str(val).strip()
    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt, dt.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            pass
    return None, None


def parse_punch_state(val):
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ["check in", "checkin", "in", "0", "i", "duty on", "true"]:
        return "checkin"
    elif s in ["check out", "checkout", "out", "1", "o", "duty off", "false"]:
        return "checkout"
    return None


# ============================================================
# SEND ATTENDANCE
# ============================================================

def send_to_zoho(record):

    emp_code = extract_field(
        record,
        ["EMP_CODE", "emp_code", "pin", "user_id", "userId", "enroll_number", "EnrollNumber", "badgenumber"]
    )
    punch_datetime_raw = extract_field(
        record,
        ["PUNCH_DATETIME", "punch_datetime", "punch_time", "punchtime", "att_time", "time", "auth_date_time"]
    )
    punch_state_raw = extract_field(
        record,
        ["PUNCH_STATE", "punch_state", "state", "status", "verify_type", "in_out", "punch_type"]
    )

    log(f"Record -> EMP_CODE: {emp_code}, DATETIME: {punch_datetime_raw}, STATE: {punch_state_raw}")

    if not emp_code:
        log("ERROR: EMP_CODE / User ID missing")
        return False

    if not punch_datetime_raw:
        log("ERROR: PUNCH_DATETIME missing")
        return False

    punch_dt, zoho_datetime = parse_punch_datetime(punch_datetime_raw)
    if not punch_dt or not zoho_datetime:
        log(f"ERROR: Invalid date format: {punch_datetime_raw}")
        return False

    state_normalized = parse_punch_state(punch_state_raw)
    if not state_normalized:
        log(f"ERROR: Unknown PUNCH_STATE: {punch_state_raw}")
        return False

    # --------------------------------------------------------
    # Duplicate key
    # --------------------------------------------------------

    unique_key = (
        f"{emp_code}|"
        f"{zoho_datetime}|"
        f"{state_normalized}"
    )

    if unique_key in processed_punches:
        log("DUPLICATE: Already processed")
        return True

    # --------------------------------------------------------
    # Past punch cutoff check (only sync from today / onwards)
    # --------------------------------------------------------

    if punch_dt < SYNC_CUTOFF:
        log(f"SKIPPED (Past punch): {zoho_datetime} is before sync start ({SYNC_CUTOFF.strftime('%d/%m/%Y %H:%M:%S')})")
        processed_punches.add(unique_key)
        save_processed(processed_punches)
        return True

    # --------------------------------------------------------
    # OAuth
    # --------------------------------------------------------

    try:
        access_token = get_access_token()
    except Exception as e:
        log(f"OAuth ERROR: {e}")
        return False

    # --------------------------------------------------------
    # Prepare attendance request
    # --------------------------------------------------------

    data = {
        "dateFormat": "dd/MM/yyyy HH:mm:ss",
        "mapId": emp_code
    }

    if state_normalized == "checkin":
        data["checkIn"] = zoho_datetime
    else:
        data["checkOut"] = zoho_datetime

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    url = f"{ZOHO_PEOPLE_URL}/people/api/attendance"

    log(f"ZOHO REQUEST -> mapId: {emp_code}, Data: {data}")

    # --------------------------------------------------------
    # Send to Zoho
    # --------------------------------------------------------

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=30
        )
    except Exception as e:
        log(f"Zoho connection ERROR: {e}")
        return False

    log(f"ZOHO RESPONSE [{response.status_code}]: {response.text}")

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    if response.status_code in (200, 201):
        log(f"Attendance recorded for mapId: {emp_code}")
        processed_punches.add(unique_key)
        save_processed(processed_punches)
        return True

    log("Attendance request FAILED.")
    return False


# ============================================================
# PROCESS EASYTIMEPRO DATA
# ============================================================

def process_body(body):

    log(f"Incoming EasyTime request: {body[:300]}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        log(f"JSON Decode ERROR: {e}")
        return {
            "status": "error",
            "message": "Invalid JSON"
        }

    records = []

    # Direct list
    if isinstance(data, list):
        records = data
    # Object
    elif isinstance(data, dict):
        for key in [
            "data",
            "records",
            "attendance",
            "punches",
            "result"
        ]:
            if key in data and isinstance(data[key], list):
                records = data[key]
                break

        if not records and "EMP_CODE" in data:
            records = [data]

    if not records:
        log("No attendance records found in payload.")
        return {
            "status": "error",
            "message": "No attendance records found"
        }

    log(f"Found {len(records)} attendance record(s)")

    success = 0
    failed = 0
    skipped = 0

    for record in records:
        if not isinstance(record, dict):
            skipped += 1
            continue

        result = send_to_zoho(record)
        if result:
            success += 1
        else:
            failed += 1

    log(f"Batch completed: Success={success}, Failed={failed}, Skipped={skipped}")

    return {
        "status": "success",
        "processed": success,
        "failed": failed,
        "skipped": skipped
    }


# ============================================================
# HTTP SERVER
# ============================================================

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress default stdout log to avoid duplicates
        return

    def send_json(self, status, data):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        self.send_json(
            200,
            {
                "status": "running",
                "service": "EasyTimePro -> Zoho People",
                "sync_cutoff": SYNC_CUTOFF.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_json(
                400,
                {
                    "status": "error",
                    "message": "Empty request body"
                }
            )
            return

        body = self.rfile.read(length)
        body_text = body.decode("utf-8", errors="replace")
        result = process_body(body_text)
        self.send_json(200, result)


# ============================================================
# START
# ============================================================

log("==========================================")
log(" EasyTimePro -> Zoho People Connector")
log(f" Server: http://{HOST}:{PORT}")
log(f" Sync Cutoff: {SYNC_CUTOFF.strftime('%Y-%m-%d %H:%M:%S')} (punches before this are skipped)")
log(f" Log file: {LOG_FILE}")
log("==========================================")
log("Waiting for EasyTimePro...")

server = HTTPServer(
    (HOST, PORT),
    Handler
)

server.serve_forever()