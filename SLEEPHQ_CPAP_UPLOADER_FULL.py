import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import smtplib
from email.mime.text import MIMEText
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Config ---

FLASHAIR_IP = os.getenv("FLASHAIR_IP")
FLASHAIR_PASSWORD = os.getenv("FLASHAIR_PASSWORD")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
DAYS_TO_KEEP_FLASHAIR = int(os.getenv("DAYS_TO_KEEP_FLASHAIR", 7))
DAYS_TO_KEEP_LOCAL = int(os.getenv("DAYS_TO_KEEP_LOCAL", 9))

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
TEAM_ID = os.getenv("TEAM_ID")
BASE_API_URL = "https://sleephq.com/api/v1"

CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")

LOG_DIR = os.getenv("LOG_DIR")
SUCCESS_LOG = Path(LOG_DIR) / "success.log"
ERROR_LOG = Path(LOG_DIR) / "errors.log"
UPLOAD_LOG_FILE = Path(LOG_DIR) / "uploaded_hashes.log"

os.makedirs(LOG_DIR, exist_ok=True)

# --- Log Rotation ---
def rotate_log(log_path, max_bytes=1_000_000):
    if os.path.exists(log_path) and os.path.getsize(log_path) > max_bytes:
        with open(log_path, "w") as f:
            f.write("")  # Truncate

rotate_log(SUCCESS_LOG)
rotate_log(ERROR_LOG)

# --- Logging Helpers ---
def log_success(message, step=None):
    entry = f"{datetime.now()} - SUCCESS"
    if step:
        entry += f" [{step}]"
    entry += f": {message}\n"
    with open(SUCCESS_LOG, "a") as f:
        f.write(entry)
    print(f"✅ {entry.strip()}")

def log_error(message, step=None):
    entry = f"{datetime.now()} - ERROR"
    if step:
        entry += f" [{step}]"
    entry += f": {message}\n"
    with open(ERROR_LOG, "a") as f:
        f.write(entry)
    print(f"❌ {entry.strip()}")

# --- FlashAir Helpers ---
def flashair_get(params):
    p = params.copy()
    if FLASHAIR_PASSWORD:
        p["p"] = FLASHAIR_PASSWORD
    r = requests.get(f"http://{FLASHAIR_IP}/command.cgi", params=p, timeout=10)
    r.raise_for_status()
    return r.text

def list_flashair_files(root="/"):
    stack = [root]
    all_files = []
    while stack:
        current_dir = stack.pop()
        try:
            data = flashair_get({"op": "100", "DIR": current_dir})
        except Exception as e:
            log_error(f"Failed to list {current_dir}: {e}")
            continue
        lines = data.splitlines()
        if not lines or lines[0] != "WLANSD_FILELIST":
            continue
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) < 4:
                continue
            name = parts[1].strip()
            attribute = parts[3].strip()
            full_path = current_dir.rstrip("/") + "/" + name
            if attribute == "16":
                stack.append(full_path)
            else:
                all_files.append(full_path)
    return all_files

def flashair_download_file(remote_path, local_path):
    try:
        url_path = remote_path.replace("/", "%2F").lstrip("/")
        download_url = f"http://{FLASHAIR_IP}/{url_path}"
        if FLASHAIR_PASSWORD:
            download_url += f"?p={FLASHAIR_PASSWORD}"
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(response.content)
        log_success(f"Downloaded file: {remote_path} to {local_path}")
    except Exception as e:
        log_error(f"Failed to download file: {remote_path} - {e}")

def flashair_delete_file(remote_path):
    try:
        flashair_get({"op": "111", "DEL": remote_path})
        log_success(f"Deleted file from FlashAir: {remote_path}")
    except Exception as e:
        log_error(f"Failed to delete file from FlashAir: {remote_path} - {e}")

def cleanup_local_files(base_dir, days_old):
    cutoff = datetime.now() - timedelta(days=days_old)
    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    log_success(f"Deleted local file: {filepath}")
            except Exception as e:
                log_error(f"Failed to delete local file: {filepath} - {e}")

# --- FlashAir Cleanup Helper ---
def cleanup_flashair_dated_folders(base_dir, days_old):
    cutoff_date = datetime.now() - timedelta(days=days_old)
    all_folders = list_flashair_files(base_dir)
    for folder in all_folders:
        folder_name = folder.strip("/").split("/")[-1]
        try:
            folder_date = datetime.strptime(folder_name, "%Y%m%d")
            if folder_date < cutoff_date:
                flashair_delete_file(folder)
                log_success(f"Deleted old folder from FlashAir: {folder}")
        except ValueError:
            continue

# --- SleepHQ Helpers ---
def get_access_token():
    try:
        url = "https://sleephq.com/oauth/token"
        data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": USERNAME,
            "password": PASSWORD,
            "scope": "read write"
        }
        headers = {"accept": "application/json"}
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        log_success("Authenticated with SleepHQ")
        return response.json()["access_token"]
    except Exception as e:
        log_error(f"Failed to authenticate with SleepHQ: {e}")
        raise

def create_import(access_token):
    try:
        url = f"{BASE_API_URL}/teams/{TEAM_ID}/imports"
        data = {"programatic": False}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/vnd.api+json",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        import_id = response.json()["data"]["id"]
        log_success(f"Created Import ID: {import_id}")
        return import_id
    except Exception as e:
        log_error(f"Failed to create import: {e}")
        raise

def upload_file_to_import(file_path, access_token, import_id, relative_path):
    try:
        url = f"{BASE_API_URL}/imports/{import_id}/files"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/vnd.api+json"
        }
        content_hash = sha256_of_file(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            data = {
                "name": file_path.name,
                "path": str(relative_path),
                "content_hash": content_hash
            }
            response = requests.post(url, headers=headers, data=data, files=files)
            response.raise_for_status()
            log_success(f"Uploaded file to SleepHQ: {file_path}")
            return True
    except Exception as e:
        log_error(f"Failed to upload file to SleepHQ: {file_path} - {e}")
        return False

def process_import(access_token, import_id):
    try:
        url = f"{BASE_API_URL}/imports/{import_id}/process_files"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/vnd.api+json"
        }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        log_success(f"Processed Import ID: {import_id}")
    except Exception as e:
        log_error(f"Failed to process import: {import_id} - {e}")

# --- Google Drive Helpers ---
def get_or_create_drive_folder(drive, parent_id, folder_name):
    # Search for the folder
    file_list = drive.ListFile({
        'q': f"'{parent_id}' in parents and trashed=false and title='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    }).GetList()
    if file_list:
        return file_list[0]['id']
    # Create the folder if it doesn't exist
    folder = drive.CreateFile({
        'title': folder_name,
        'parents': [{'id': parent_id}],
        'mimeType': 'application/vnd.google-apps.folder'
    })
    folder.Upload()
    return folder['id']

def upload_to_drive(file_path, date_folder):
    try:
        gauth = GoogleAuth(settings={
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": CREDENTIALS_JSON
            }
        })
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)
        # Create/find date folder
        date_folder_id = get_or_create_drive_folder(drive, DRIVE_FOLDER_ID, date_folder)
        file = drive.CreateFile({
            "title": file_path.name,
            "parents": [{"id": date_folder_id}]
        })
        file.SetContentFile(str(file_path))
        file.Upload()
        log_success(f"Uploaded file to Google Drive: {file_path} in {date_folder}")
        return True
    except Exception as e:
        log_error(f"Failed to upload file to Google Drive: {file_path} - {e}")
        return False

# --- Google Drive Cleanup Helper ---
def cleanup_drive_dated_folders(days_old):
    try:
        gauth = GoogleAuth(settings={
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": CREDENTIALS_JSON
            }
        })
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)
        cutoff_date = datetime.now() - timedelta(days=days_old)
        # List all folders in the main drive folder
        folder_list = drive.ListFile({
            'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
        }).GetList()
        for folder in folder_list:
            try:
                folder_name = folder['title']
                # Expecting folder_name to be a date string like YYYYMMDD
                folder_date = datetime.strptime(folder_name, "%Y%m%d")
                if folder_date < cutoff_date:
                    folder.Delete()
                    log_success(f"Deleted old folder from Google Drive: {folder_name}")
            except ValueError:
                # Skip folders that don't match the date format
                continue
    except Exception as e:
        log_error(f"Failed to clean up old folders in Google Drive: {e}")

# --- Email Notification ---
def send_email_notification(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = GMAIL_USERNAME
        msg["To"] = NOTIFICATION_EMAIL
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USERNAME, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        log_success(f"Sent email notification: {subject}")
    except Exception as e:
        log_error(f"Failed to send email: {e}")

# --- Hash Log Helpers ---
def sha256_of_file(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_hash_log(log_file):
    """Load the hash log and only keep entries for the last 7 days."""
    if not log_file.exists():
        return set()
    cutoff = datetime.now() - timedelta(days=7)
    valid_hashes = set()
    lines = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                hash_str, date_str = line.strip().split(",")
                log_date = datetime.strptime(date_str, "%Y-%m-%d")
                if log_date >= cutoff:
                    valid_hashes.add(hash_str)
                    lines.append(line)
            except Exception:
                continue
    # Rewrite log file with only recent entries
    with open(log_file, "w") as f:
        f.writelines(lines)
    return valid_hashes

def log_hash(file_hash, log_file):
    with open(log_file, "a") as f:
        f.write(f"{file_hash},{datetime.now().strftime('%Y-%m-%d')}\n")

# --- Improved Email Report ---
def build_email_report(success_log, error_log, missing_files=None, skipped_files=None):
    with open(success_log, "r") as f:
        success_content = f.read()
    with open(error_log, "r") as f:
        error_content = f.read()
    body = "FlashAir & SleepHQ Upload Report\n\n"
    if missing_files:
        body += f"❗ Missing files:\n" + "\n".join(missing_files) + "\n\n"
    if skipped_files:
        body += f"⏭️ Skipped files (already uploaded):\n" + "\n".join(skipped_files) + "\n\n"
    body += "--- SUCCESSFUL OPERATIONS ---\n" + success_content + "\n"
    body += "--- ERRORS ---\n" + error_content + "\n"
    return body

# --- Main Script ---
if __name__ == "__main__":
    try:
        # Step 1: Gather required files (today/yesterday's DATALOG, all SETTINGS, critical files)
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        required_files = []

        # DATALOG folders
        for datalog_folder in [f"/DATALOG/{today_str}", f"/DATALOG/{yesterday_str}"]:
            try:
                required_files.extend(list_flashair_files(datalog_folder))
            except Exception as e:
                log_error(f"Failed to list {datalog_folder}: {e}")

        # SETTINGS folder (all files)
        try:
            settings_files = list_flashair_files("/SETTINGS")
            required_files.extend(settings_files)
        except Exception as e:
            log_error(f"Failed to list /SETTINGS: {e}")
            send_email_notification(
                "🚨 FlashAir and SleepHQ Upload Failed",
                "Critical failure: Unable to retrieve SETTINGS folder."
            )
            sys.exit(1)

        # Critical standalone files
        critical_files = [
            "/STR.edf",
            "/Identification.crc",
            "/Identification.json"
        ]
        required_files.extend(critical_files)

        # Step 2: Download required files
        missing_files = []
        for remote_file in required_files:
            relative_path = remote_file.lstrip("/")
            local_path = Path(DOWNLOAD_DIR) / relative_path
            flashair_download_file(remote_file, local_path)  # Always overwrite
            if not local_path.exists():
                missing_files.append(str(local_path))

        # Step 3: Validate required files
        missing = []
        for critical in critical_files:
            if not (Path(DOWNLOAD_DIR) / critical.lstrip("/")).exists():
                missing.append(critical)
        for settings_file in settings_files:
            if not (Path(DOWNLOAD_DIR) / settings_file.lstrip("/")).exists():
                missing.append(settings_file)
        if missing:
            log_error(f"Missing required files after download: {', '.join(missing)}")
            send_email_notification(
                "🚨 FlashAir and SleepHQ Upload Failed",
                f"Missing required files after download: {', '.join(missing)}"
            )
            sys.exit(1)

        # Step 4: Check hash log for duplicates
        uploaded_hashes = load_hash_log(UPLOAD_LOG_FILE)
        files_to_upload = []
        skipped_files = []
        new_datalog_files = []

        for file_path in required_files:
            local_path = Path(DOWNLOAD_DIR) / file_path.lstrip("/")
            if not local_path.exists():
                continue
            file_hash = sha256_of_file(local_path)
            is_datalog = "/DATALOG/" in file_path
            if file_hash not in uploaded_hashes or file_path in critical_files or file_path in settings_files:
                files_to_upload.append(local_path)
                if is_datalog and file_hash not in uploaded_hashes:
                    new_datalog_files.append(local_path)
            else:
                skipped_files.append(str(local_path))

        if missing_files:
            log_error(f"Missing required files after download: {', '.join(missing_files)}", step="Validation")
            email_body = build_email_report(SUCCESS_LOG, ERROR_LOG, missing_files=missing_files)
            send_email_notification(
                "🚨 FlashAir and SleepHQ Upload Failed",
                email_body
            )
            sys.exit(1)

        if not files_to_upload:
            log_success("All files for today and yesterday have already been uploaded.", step="Validation")
            email_body = build_email_report(SUCCESS_LOG, ERROR_LOG, skipped_files=skipped_files)
            send_email_notification(
                "✅ FlashAir and SleepHQ Upload Skipped",
                email_body
            )
            sys.exit(0)

        # --- Only proceed if there is a new DATALOG file to upload ---
        if not new_datalog_files:
            log_success("No new DATALOG files to upload. Skipping upload.", step="Validation")
            email_body = build_email_report(SUCCESS_LOG, ERROR_LOG, skipped_files=skipped_files)
            send_email_notification(
                "✅ FlashAir and SleepHQ Upload Skipped (No New DATALOG)",
                email_body
            )
            sys.exit(0)

        # Step 5: Upload to SleepHQ and Google Drive
        try:
            access_token = get_access_token()
            import_id = create_import(access_token)
            for file_path in files_to_upload:
                relative_path = file_path.relative_to(DOWNLOAD_DIR)
                if upload_file_to_import(file_path, access_token, import_id, relative_path):
                    log_hash(sha256_of_file(file_path), UPLOAD_LOG_FILE)
            # Determine the date folder for each file (e.g., based on today's date or file's parent folder)
            for file_path in files_to_upload:
                relative_path = file_path.relative_to(DOWNLOAD_DIR)
                # Use today's date as folder name, or extract from file_path if you want per-session folders
                date_folder = today_str
                upload_to_drive(file_path, date_folder)
            process_import(access_token, import_id)
        except Exception as e:
            log_error(f"Failed during upload: {e}", step="Upload")
            email_body = build_email_report(SUCCESS_LOG, ERROR_LOG)
            send_email_notification(
                "🚨 FlashAir and SleepHQ Upload Failed",
                email_body
            )
            sys.exit(1)

        # Step 6: Cleanup
        cleanup_local_files(DOWNLOAD_DIR, days_old=DAYS_TO_KEEP_LOCAL)
        cleanup_flashair_dated_folders("/DATALOG", days_old=DAYS_TO_KEEP_FLASHAIR)
        cleanup_drive_dated_folders(days_old=DAYS_TO_KEEP_FLASHAIR)

        # Step 7: Concise Email Notification
        with open(ERROR_LOG, "r") as error_file:
            error_content = error_file.read().strip()

        if error_content:
            email_body = (
                "Some errors occurred during the FlashAir & SleepHQ upload process:\n\n"
                f"{error_content}\n"
            )
            subject = "⚠️ FlashAir and SleepHQ Upload Completed With Errors"
        else:
            email_body = "✅ FlashAir and SleepHQ upload completed successfully. All required files were uploaded."
            subject = "✅ FlashAir and SleepHQ Upload Success"

        send_email_notification(subject, email_body)
        print("🎉 All operations completed successfully!")
        sys.exit(0)

    except Exception as e:
        log_error(f"Critical Failure: {e}", step="Critical")
        with open(ERROR_LOG, "r") as error_file:
            error_content = error_file.read().strip()
        email_body = (
            "A critical error occurred during the FlashAir & SleepHQ upload process:\n\n"
            f"{error_content}\n"
        )
        send_email_notification(
            "🚨 FlashAir and SleepHQ Upload Failed",
            email_body
        )
        sys.exit(1)