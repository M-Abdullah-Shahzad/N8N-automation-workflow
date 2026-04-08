# Selenium Demo Forms

This mini project contains two demonstration webpages for Selenium training:

1. **Login Form with Captcha**
2. **All HTML Inputs Demo Form**

## Features
- Bootstrap-based modern UI
- Server-side arithmetic captcha
- SQLite storage (`data/demo_submissions.db`)
- CSV logging (`data/demo_submissions.csv`)
- Submission viewer at `/submissions`

## Run locally

```bash
cd selenium_demo_forms
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:
- `http://127.0.0.1:5000/login`
- `http://127.0.0.1:5000/all-inputs`
- `http://127.0.0.1:5000/submissions`

## Notes for Selenium class
- The login form includes text, email, password, select, checkbox, textarea, and captcha.
- The all-inputs page includes common HTML input types in one form.
- File upload is included for interaction practice, but file content is not stored in this basic version.

## Added automation asset
- Added `Task 1 – All Input Form Automation (Complete with CAPTCHA).json` to the repository.
- This file contains an n8n workflow for solving the login captcha and submitting the all-inputs form.

## Selenium automation
- Added `selenium_automation/run_automation.py` to automate login, captcha solving, and all-inputs form submission.
- The script reads `selenium_automation/inputs.csv` and uses Selenium WebDriver to drive the demo Flask app.
