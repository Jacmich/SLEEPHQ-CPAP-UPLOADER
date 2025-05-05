# SLEEPHQ-CPAP-UPLOADER

Automated CPAP Data Uploading to SleepHQ and Google Drive

This project demonstrates a complete automation pipeline built in Python for managing and uploading CPAP machine data. Designed to run daily and unattended, it retrieves therapy data from a Toshiba FlashAir WiFi SD card, uploads it to SleepHQ for analysis, backs it up to Google Drive, and provides detailed logging and notifications.

Originally developed for personal use, this was my first full-stack automation script—and it's become a solid example of how I approach problem-solving, system integration, and maintainable automation.

If you're reviewing this as a sample of my work, feel free to explore the code or reach out with feedback.

---

## Features

- **Automated Downloads**: Retrieves essential DATALOG and SETTINGS files from a Toshiba FlashAir SD card.
- **Secure and Reliable Uploads**: Seamlessly uploads files to SleepHQ for analysis and Google Drive for backup.
- **Duplicate Detection**: Employs file hashing to prevent re-uploading already processed files.
- **Retention Policy Management**: Automatically removes outdated files from FlashAir, local storage, and Google Drive.
- **Detailed Logging**: Provides comprehensive logs for auditing and debugging purposes.
- **Email Notifications**: Sends detailed reports and alerts via Gmail.
- **Customizable Settings**: Configurations are managed through environment variables for flexible operation.

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
- [Credits](#credits)

---

## Requirements

- Python 3.8 or later
- [PyDrive2](https://github.com/iterative/PyDrive2)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- `requests`
- Access to a Toshiba FlashAir SD card with WiFi enabled
- [SleepHQ](https://sleephq.com/) account with API credentials
- Google Cloud service account with Drive access
- Gmail account with an App Password for notifications
- Hardware used: Raspberry Pi 5 (runs fine with a Raspberry Pi Zero 2 W, wouldnt go lower than that though)

### Installing Dependencies

```bash
pip install -r requirements.txt
```

---

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Jacmich/SLEEPHQ-CPAP-UPLOADER.git
   cd SLEEPHQ-CPAP-UPLOADER
   ```

2. **Configure Environment Variables**
   - Copy `.env.template` to `.env` and populate it with the required fields (refer to [Configuration](#configuration)).

3. **Set Up Google Drive Credentials**
   - Create a Google Cloud service account and download the JSON key file.
   - Update the `CREDENTIALS_JSON` field in your `.env` file with the path to this file.

4. **Prepare FlashAir**
   - Ensure the FlashAir SD card is accessible from your local network with its API enabled.

5. **(Optional) Schedule Execution**
   - Use a task scheduler like `cron` (Linux) or Windows Task Scheduler for automated daily execution.

---

## Configuration

Configuration is handled via environment variables. Refer to `.env.template` for a comprehensive list of configurable options.

| Variable                | Description                                          |
|-------------------------|------------------------------------------------------|
| FLASHAIR_IP             | IP address of the FlashAir SD card                   |
| FLASHAIR_PASSWORD       | Password for FlashAir (if applicable)                |
| DOWNLOAD_DIR            | Local directory for downloading and processing files |
| DAYS_TO_KEEP_FLASHAIR   | Retention period for FlashAir files (default: 7 days)|
| DAYS_TO_KEEP_LOCAL      | Retention period for local files (default: 9 days)   |
| CLIENT_ID               | SleepHQ API client ID                                |
| CLIENT_SECRET           | SleepHQ API client secret                            |
| USERNAME                | SleepHQ account username                             |
| PASSWORD                | SleepHQ account password                             |
| TEAM_ID                 | SleepHQ team ID                                      |
| CREDENTIALS_JSON        | Path to Google API credentials JSON                  |
| DRIVE_FOLDER_ID         | Google Drive folder ID for uploads                   |
| GMAIL_USERNAME          | Gmail account for notifications                      |
| GMAIL_APP_PASSWORD      | Gmail App Password                                   |
| NOTIFICATION_EMAIL      | Recipient email for notifications                    |
| LOG_DIR                 | Directory for storing logs                           |

---

## How It Works

1. **File Collection**
   - Retrieves today’s and yesterday’s `/DATALOG/YYYYMMDD` files, all `/SETTINGS` files, and key root files (`STR.edf`, `Identification.crc`, `Identification.json`).

2. **Download**
   - Downloads required files from the FlashAir SD card to a local directory and verifies the integrity of the download.

3. **Hash Verification**
   - Computes SHA-256 file hashes to avoid duplicate uploads, maintaining a 7-day hash log.

4. **Upload**
   - Files are uploaded to SleepHQ via its API and to Google Drive, organized by date.

5. **Post-Upload Processing**
   - Triggers SleepHQ to process the uploaded files.

6. **Cleanup**
   - Deletes files from FlashAir, local storage, and Google Drive based on the configured retention policy.

7. **Reporting**
   - Sends email notifications detailing the results of the operation, including any errors or skipped files.

---

## Logs and Notifications

- **Logs**: Stored in `LOG_DIR` with files such as `success.log`, `errors.log`, and `uploaded_hashes.log`.
- **Email Reports**: Summarizes each execution, highlighting successes, errors, and any missing files.

---

## Retention Policy

- **FlashAir**: Deletes folders older than `DAYS_TO_KEEP_FLASHAIR`.
- **Local**: Removes files older than `DAYS_TO_KEEP_LOCAL`.
- **Google Drive**: Purges folders older than `DAYS_TO_KEEP_FLASHAIR`.

---

## Troubleshooting

- **Missing Files**: The script will notify you via email if required files are unavailable.
- **Authentication Issues**: Verify your SleepHQ and Google Drive credentials.
- **Gmail Errors**: Ensure you are using an App Password instead of your Gmail account password.
- **Network Connectivity**: Confirm that the FlashAir device is powered and reachable on your network.

---

## License

This project is licensed under the MIT License. For details, see [LICENSE](LICENSE).

---

## Credits

Developed by @Jacmich
SleepHQ API provided by SleepHQ

---

**Want to Learn More?** 

This project is a hands-on example of:
- Real-world automation using Python
- Integrating hardware with cloud services
- Secure credential handling
- API-based data pipelines

If you'd like to collaborate or have feedback, open an issue or reach out.