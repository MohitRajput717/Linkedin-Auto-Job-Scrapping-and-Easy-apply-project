<div align="center">

# 🔎 LinkedIn Scrapper & Recruiter Outreach Automation

### Discover hiring posts · Extract contact details · Organize opportunities · Streamline outreach

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Playwright-Browser%20Automation-2EAD33?logo=playwright&logoColor=white" alt="Playwright">
  <img src="https://img.shields.io/badge/Google%20Sheets-Data%20Storage-34A853?logo=googlesheets&logoColor=white" alt="Google Sheets">
  <img src="https://img.shields.io/badge/Google%20Apps%20Script-Email%20Automation-4285F4?logo=googleappsscript&logoColor=white" alt="Google Apps Script">
</p>

**An end-to-end job-opportunity research workflow built with Python, Playwright, Google Sheets, and Google Apps Script.**

</div>

---

## 📌 Overview

This project automates parts of the job-search research process. A Python application uses Playwright to search recent LinkedIn hiring posts, expand post content, and extract email addresses and Google Forms application links. New records are filtered and written to a Google Sheet.

A companion Google Apps Script (`app_script.gs`) is included for recruiter email outreach using spreadsheet records.

> **Current implementation note:** The scraper and spreadsheet integration are implemented in `linked.py`. The Apps Script is a separate component and must be configured and authorized in Google Apps Script. A time-driven trigger is configured in the Apps Script interface; it is not automatically created by the Python program.

## ✨ Features

### LinkedIn post discovery
- Opens LinkedIn in a visible Chromium browser using Playwright.
- Reuses a persistent browser session when available.
- Searches configured hiring-related keywords.
- Applies LinkedIn's past-24-hours content filter and recent-post sorting.
- Expands supported “See more” post controls.
- Scrolls the results feed and reads loaded page text.
- Allows manual completion of login, CAPTCHA, or OTP challenges.

### Contact and application-link extraction
- Extracts email-like strings with regular expressions.
- Filters Gmail addresses and selected unwanted domains.
- Extracts Google Forms URLs.
- Cleans trailing punctuation from extracted URLs.
- Avoids duplicate emails and links during the current run.
- Checks existing spreadsheet email values before appending new email records.

### Google Sheets storage
- Authenticates with a Google service account.
- Reads existing email records.
- Appends newly extracted records.
- Stores the date, email address, and application link.

### Recruiter email outreach
- Includes a Google Apps Script file for processing spreadsheet records.
- Uses Google Apps Script's mail service to send HTML-formatted email.
- Can be scheduled using a time-driven trigger after the script is configured.

## 🧰 Technology Stack

| Technology | Role |
|---|---|
| Python | Scraping and data-processing logic |
| Playwright | Browser automation |
| Asyncio | Asynchronous browser workflow |
| Regular expressions | Email and URL extraction |
| gspread | Google Sheets integration |
| Google Auth | Service-account authentication |
| python-dotenv | Local environment configuration |
| Google Sheets API | Central record storage |
| Google Apps Script | Spreadsheet-driven email outreach |
| Gmail / MailApp | Email delivery through Apps Script |

## 🗂️ Project Structure

```text
LinkedIn-Scrapper/
│
├── linked.py                  # LinkedIn scraper and Sheets writer
├── app_script.gs              # Google Apps Script email workflow
├── requirements.txt           # Python dependencies
├── .env                        # Local credentials (never commit)
├── .gitignore                  # Files excluded from Git
├── README.md                   # Project documentation
│
└── linkedin_browser_session/  # Persistent browser session (never commit)
```

The Google service-account JSON file should be stored securely outside the repository. The current Python script contains a local file path for this credential; update it for your machine or move it to an environment variable before sharing the project.

## ⚙️ Getting Started

### 1. Prerequisites

- Windows, macOS, or Linux
- Python 3.10 or later
- Google account with access to Google Sheets and Apps Script
- LinkedIn account
- Google Cloud project with Google Sheets API and Google Drive API enabled
- Google service-account credentials

### 2. Clone the repository

Replace the example URL with your repository URL:

```bash
git clone https://github.com/YOUR_USERNAME/LinkedIn-Scrapper.git
cd LinkedIn-Scrapper
```

### 3. Create and activate a virtual environment

**Windows (Git Bash):**

```bash
python -m venv .venv
source .venv/Scripts/activate
```

**Windows (Command Prompt):**

```bat
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

If `requirements.txt` is present:

```bash
pip install -r requirements.txt
```

The current Python source imports these packages:

```bash
pip install playwright gspread python-dotenv google-auth
```

Install the Playwright Chromium browser:

```bash
playwright install chromium
```

### 5. Configure environment variables

Create a local `.env` file in the project root:

```env
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

The Python script reads these values using `python-dotenv`.

**Never commit your real `.env` file.** Keep credentials out of source code, screenshots, logs, and public repositories.

### 6. Configure Google Sheets access

1. Create or select a project in Google Cloud Console.
2. Enable the Google Sheets API and Google Drive API.
3. Create a service account and generate a JSON key.
4. Store the JSON key securely outside this repository.
5. Share the target spreadsheet with the service account email address, granting the access required by the application.
6. Configure the credential file path and spreadsheet settings in `linked.py`.

The current source defines:

```python
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"
SHEET_NAME = "Sheet1"
```

Use your own spreadsheet ID and worksheet name. Do not publish service-account keys.

> **Configuration improvement:** The current `linked.py` contains a machine-specific service-account JSON path. It must be changed on a different computer. Moving that path into `.env` is a recommended future improvement.

## ▶️ Run the scraper

From the project root, with the virtual environment activated:

```bash
python linked.py
```

On the first run, the browser may require you to sign in and complete LinkedIn verification manually. After authentication, the application uses the persistent browser-session directory on subsequent runs, subject to LinkedIn's session validity.

## 🔍 Search settings

The current source includes these search terms:

```python
SEARCH_QUERIES = [
    "data analyst hiring",
    "Sr data analyst hiring",
]
```

The current scraper configuration includes:

| Setting | Current value |
|---|---:|
| Search timeout | 300 seconds per query |
| Scroll pause | 2 seconds |
| Scroll amount | 800 pixels |
| Minimum page text | 1,000 characters |
| LinkedIn post filter | Past 24 hours |
| Browser mode | Visible Chromium |

You can edit `SEARCH_QUERIES` in `linked.py` to change the search terms.

## 📊 Google Sheets data format

The Python scraper writes three values per record:

| Column | Field | Meaning |
|---|---|---|
| A | Date | Date assigned by the scraper |
| B | Email | Extracted email address |
| C | Apply Link | Extracted Google Forms URL, when available |

Example rows (illustrative only):

| Date | Email | Apply Link |
|---|---|---|
| 10/05/2026 | recruiter@example-company.com | `https://docs.google.com/forms/...` |
| 10/05/2026 | hiring@example-company.com | |
| 10/05/2026 | | `https://docs.google.com/forms/...` |

The code pairs extracted emails and form links by their order in the page text when both are present. This is a heuristic, not a verified relationship between a specific recruiter and a specific application form. Unpaired values are stored in separate rows.

## ✉️ Configure the Google Apps Script

The repository includes `app_script.gs` as a separate email-automation component.

1. Open [Google Apps Script](https://script.google.com/).
2. Create a new Apps Script project.
3. Copy the contents of the local `app_script.gs` into the Apps Script editor.
4. Configure the correct spreadsheet reference and any email-template details.
5. Review the recipient selection and message content.
6. Save and authorize the script.
7. Test with an address you control before enabling a scheduled trigger.

### Optional daily trigger

To run the configured function during the 10 AM hour:

1. Open **Triggers** in the Apps Script editor.
2. Select **Add Trigger**.
3. Choose the intended email function.
4. Set the event source to **Time-driven**.
5. Choose **Day timer** and the **10 AM–11 AM** time window.
6. Save the trigger and confirm the script's project time zone.

Apps Script time-driven triggers run within the selected window; they do not guarantee execution at exactly 10:00 AM.

### Important email-safety checks

Before enabling unattended sending, verify that the script:

- Tracks each record with a clear status such as `PENDING`, `SENT`, or `FAILED`.
- Skips records already marked as sent.
- Applies a conservative daily sending limit.
- Handles errors without marking failed messages as sent.
- Uses accurate, relevant, non-misleading message content.
- Provides an appropriate way to opt out of further contact.
- Sends only to contacts you are permitted to contact.

**The uploaded implementation does not currently provide reliable sent-status tracking or duplicate-send prevention.** A repeated trigger could therefore send the same message again. Add these safeguards before scheduling recurring email delivery.

## 🔄 Workflow

```text
LinkedIn hiring posts
        │
        ▼
Python + Playwright
        │
        ▼
Expand posts and scroll results
        │
        ▼
Extract email addresses and Forms URLs
        │
        ▼
Filter and deduplicate extracted values
        │
        ▼
Google Sheets
        │
        ▼
Google Apps Script (separately configured)
        │
        ▼
Review, status checks and email outreach
```

## 🔐 Security checklist

Before pushing changes to GitHub, confirm that the following are excluded:

- `.env` and other environment files containing secrets
- Google service-account JSON keys
- `linkedin_browser_session/`
- Virtual environments and Python cache files
- Any exported spreadsheet or file containing private contact data

Recommended `.gitignore`:

```gitignore
# Secrets and local configuration
.env
.env.*
!.env.example
*.json

# Browser authentication data
linkedin_browser_session/

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Editor and operating-system files
.vscode/
.idea/
.DS_Store
Thumbs.db
```

> If a credential was ever committed to Git, adding it to `.gitignore` does not remove it from Git history. Revoke or rotate the exposed credential and clean the repository history where appropriate.

## ⚠️ Current limitations

- LinkedIn can change its page structure and selectors, which may affect scraping.
- Search results depend on the content LinkedIn makes available to the signed-in account.
- The scraper extracts visible page text; it does not guarantee that every post or contact detail is captured.
- Email-to-application-link association is based on extraction order and may be inaccurate.
- The service-account JSON path is currently machine-specific.
- The Apps Script trigger must be configured separately.
- The current email workflow needs sent-status tracking and duplicate-send protection before unattended recurring execution.

Use automation responsibly. Respect LinkedIn's terms, applicable privacy and data-protection laws, email rules, and recipients' communication preferences. Do not use collected contact details for unsolicited or misleading bulk messaging.

## 🛣️ Roadmap

- [ ] Move all machine-specific paths and settings into environment configuration.
- [ ] Add structured logging and clearer error reporting.
- [ ] Improve extraction of company names, job titles, locations, and post URLs.
- [ ] Improve the association between recruiter contacts and application links.
- [ ] Add email validation and data-quality checks.
- [ ] Add `PENDING`, `SENT`, and `FAILED` status tracking.
- [ ] Add duplicate-send prevention and daily sending limits.
- [ ] Add configurable, personalized outreach templates and opt-out handling.
- [ ] Add reporting or a Power BI dashboard for collected opportunities.
- [ ] Explore AI-assisted job-post classification and matching.

## 👨‍💻 Author

**Mohit Rajput**

[LinkedIn](https://linkedin.com/in/mohit-singh-analyst/)

*Python · SQL · Data Analytics · Automation · Data Engineering*

---

<div align="center">

**Built to make job-opportunity research more organized and less manual.**

</div>
