# SLEEPHQ-CPAP-UPLOADER

This is the first fully working script I’ve ever built, and I’m genuinely proud of it. What started as a simple idea to automate SleepHQ uploads grew into a fully featured system with backup, logging, cleanup, and notification support. Hopefully it’s helpful to someone else too. If you end up using it,(or not) I’d really appreciate any feedback or suggestions!

## Features

- **Automatic download**: Retrieves required DATALOG and SETTINGS files from a Toshiba FlashAir SD card.
- **Reliable upload**: Uploads files to SleepHQ (for analysis/recording) and Google Drive (for personal backup).
- **Duplicate prevention**: Uses file hashes to skip already-uploaded files.
- **Automatic cleanup**: Deletes old files from FlashAir, local storage, and Google Drive based on retention policy.
- **Comprehensive logging**: Logs successes and errors for audit and debugging.
- **Email notifications**: Sends detailed reports and error alerts via Gmail.
- **Highly configurable**: All settings are provided via environment variables.

---

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Logs and Notifications](#logs-and-notifications)
- [Retention Policy](#retention-policy)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Requirements

- Python 3.8+
- [PyDrive2](https://github.com/iterative/PyDrive2)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- `requests`
- Access to Toshiba FlashAir SD card (with WiFi enabled)
- [SleepHQ](https://sleephq.com/) account with API credentials
- Google Cloud service account with Drive access (for uploads)
- Gmail account with App Password (for notifications)
- I used a Raspberry Pi 5 to code and run this but it should run fine with a Rasberry Pi zero 2 W

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jacmich/SLEEPHQ-CPAP-UPLOADER.git
   cd SLEEPHQ-CPAP-UPLOADER
   ```

2. **Prepare environment variables**
   - Copy `.env.template` to `.env` and fill in all necessary fields (see [Configuration](#configuration))

3. **Google Drive credentials**
   - Create a Google Cloud service account and download the JSON key file
   - Set the path to this JSON in your `.env` as `CREDENTIALS_JSON`

4. **FlashAir setup**
   - Ensure your FlashAir SD card is accessible on your local network and the API is enabled

5. **(Optional) Set up as a scheduled job**
   - Use `cron` or Windows Task Scheduler to run the script daily

---

## Configuration

All configuration is done by environment variables. See `.env.template` for a full list.

| Variable                | Description                                        |
|-------------------------|----------------------------------------------------|
| FLASHAIR_IP             | IP address of the FlashAir SD card                 |
| FLASHAIR_PASSWORD       | Password for FlashAir (if required)                |
| DOWNLOAD_DIR            | Local directory to download and process files      |
| DAYS_TO_KEEP_FLASHAIR   | Days to keep files/folders on FlashAir (default: 7)|
| DAYS_TO_KEEP_LOCAL      | Days to keep files locally (default: 9)            |
| CLIENT_ID               | SleepHQ API client ID                              |
| CLIENT_SECRET           | SleepHQ API client secret                          |
| USERNAME                | SleepHQ username                                   |
| PASSWORD                | SleepHQ password                                   |
| TEAM_ID                 | SleepHQ team ID                                    |
| CREDENTIALS_JSON        | Path to Google API credentials JSON                |
| DRIVE_FOLDER_ID         | Google Drive folder ID for uploads                 |
| GMAIL_USERNAME          | Gmail address for notifications                    |
| GMAIL_APP_PASSWORD      | Gmail App Password                                 |
| NOTIFICATION_EMAIL      | Email to receive notifications                     |
| LOG_DIR                 | Directory for logs                                 |

---

## How It Works

1. **Gather required files**
    - Collects today’s and yesterday’s `/DATALOG/YYYYMMDD` files, all `/SETTINGS` files, and critical root files (`STR.edf`, `Identification.crc`, `Identification.json`).

2. **Download files**
    - Downloads all required files from FlashAir to the local folder.
    - Verifies download success.

3. **Hash check and deduplication**
    - Calculates SHA-256 hashes for each file.
    - Uses a 7-day hash log to skip duplicate uploads.

4. **Upload**
    - Files are uploaded to both SleepHQ (API) and Google Drive (organized by date).

5. **Process imports**
    - Triggers SleepHQ to process the uploaded files.

6. **Cleanup**
    - Old files and folders are deleted from FlashAir, local storage, and Google Drive based on the retention policy.

7. **Reporting**
    - Sends an email notification (success or error report) with log summaries and details.

---

## Logs and Notifications

- **Logs**: All actions are logged to files in `LOG_DIR` (defaults: `success.log`, `errors.log`, `uploaded_hashes.log`).
- **Email**: After each run, an email is sent with a summary of operations, including any errors, missing files, or skipped uploads.

---

## Retention Policy

- **FlashAir**: Old folders (older than `DAYS_TO_KEEP_FLASHAIR`) are deleted.
- **Local**: Old files (older than `DAYS_TO_KEEP_LOCAL`) are deleted.
- **Google Drive**: Old folders (older than `DAYS_TO_KEEP_FLASHAIR`) are deleted.

---

## Troubleshooting

- **Missing files**: The script will email you if any required files are not downloaded or missing.
- **Authentication errors**: Check your SleepHQ and Google Drive credentials.
- **Gmail issues**: Ensure you use an App Password, not your regular Gmail password.
- **Network errors**: Ensure the FlashAir device is powered and reachable on your network.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Credits

Maintained by [@Jacmich](https://github.com/Jacmich).  
SleepHQ API by [SleepHQ.com](https://sleephq.com/).

---

**Questions or Suggestions?**  
Open an issue or pull request on [GitHub](https://github.com/Jacmich/SLEEPHQ-CPAP-UPLOADER).

---
# SLEEPHQ-CPAP-UPLOADER
