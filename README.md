SLEEPHQ-CPAP-UPLOADER

Automated CPAP Data Uploading to SleepHQ and Google Drive

This project demonstrates a complete automation pipeline built in Python for managing and uploading CPAP machine data. Designed to run daily and unattended, it retrieves therapy data from a Toshiba FlashAir WiFi SD card, uploads it to SleepHQ for analysis, backs it up to Google Drive, and provides detailed logging and notifications.

Originally developed for personal use, this was my first full-stack automation script—and it's become a solid example of how I approach problem-solving, system integration, and maintainable automation.

If you're reviewing this as a sample of my work, feel free to explore the code or reach out with feedback.

Key Features

- End-to-end automation: No user interaction needed after setup.
- Dual upload: Sends files to both SleepHQ (for viewing) and Google Drive (for backup).
- Hash-based deduplication: Prevents redundant uploads using SHA-256.
- Automated cleanup: Removes old files from FlashAir, local storage, and Drive.
- Email alerts: Sends success/error notifications after every run.
- Fully configurable: Uses environment variables for easy deployment across environments.
- Runs on Raspberry Pi: Optimized for low-power devices like the Pi Zero 2 W.

Table of Contents

- Requirements
- Installation & Setup
- Configuration
- How It Works
- Logging & Notifications
- Retention Policy
- Troubleshooting
- License
- Credits

Requirements

- Python 3.8+
- A Toshiba FlashAir SD card (with WiFi and API enabled)
- SleepHQ account with API access
- Google Cloud Service Account (for Drive API)
- Gmail account (App Password required)
- Raspberry Pi or other Linux device recommended

Install dependencies:
pip install -r requirements.txt

Installation & Setup

1. Clone this repository
   git clone https://github.com/Jacmich/SLEEPHQ-CPAP-UPLOADER.git
   cd SLEEPHQ-CPAP-UPLOADER

2. Create environment configuration
   - Copy .env.template to .env
   - Fill in all required values (see Configuration)

3. Set up Google Drive access
   - Create a service account in Google Cloud
   - Enable the Drive API
   - Save and reference the JSON key file

4. Connect your FlashAir card
   - Ensure it's accessible on your WiFi network

5. Schedule automatic runs (optional)
   - Use cron or a scheduled task to run the script daily

Configuration

All options are set via environment variables:

| Variable              | Purpose                                  |
|-----------------------|------------------------------------------|
| FLASHAIR_IP           | IP address of FlashAir card              |
| CLIENT_ID             | SleepHQ API client ID                    |
| CREDENTIALS_JSON      | Path to Google Drive credentials JSON    |
| DRIVE_FOLDER_ID       | Target Google Drive folder ID            |
| DOWNLOAD_DIR          | Local download folder                    |
| DAYS_TO_KEEP_LOCAL    | Days to retain local files               |
| GMAIL_USERNAME        | Gmail sender address                     |
| NOTIFICATION_EMAIL    | Recipient address for reports            |
| (... and more)        | See .env.template for full list          |

How It Works

1. Data Discovery: Detects files from the last 2 days on FlashAir (/DATALOG, /SETTINGS, and root files).
2. File Transfer: Downloads those files to a local directory.
3. Integrity Checks: Verifies files and checks for duplicates using a hash log.
4. Uploads: Sends data to both SleepHQ and Google Drive.
5. Post-Processing: Triggers SleepHQ to process the uploads.
6. Cleanup: Removes old files based on your retention settings.
7. Notifications: Sends an email summary of the run, with error tracking.

Logging & Notifications

- All activity is recorded in the LOG_DIR folder (successes, errors, and hash logs).
- Email reports include:
  - Number of files uploaded
  - Any skipped or failed uploads
  - Errors encountered during transfer or API calls

Retention Policy

- FlashAir: Old files deleted after DAYS_TO_KEEP_FLASHAIR days
- Local: Cleaned up after DAYS_TO_KEEP_LOCAL
- Google Drive: Folders older than DAYS_TO_KEEP_FLASHAIR are purged

Troubleshooting

- Files not downloading? Confirm the FlashAir card is online and reachable.
- Email not sending? Double-check Gmail App Password settings.
- Drive upload failing? Ensure your service account has permission for the target folder.

License

This project is open-source under the MIT License.

Credits

Developed by @Jacmich
SleepHQ API provided by SleepHQ

Want to Learn More?

This project is a hands-on example of:
- Real-world automation using Python
- Integrating hardware with cloud services
- Secure credential handling
- API-based data pipelines

If you'd like to collaborate or have feedback, open an issue or reach out.
