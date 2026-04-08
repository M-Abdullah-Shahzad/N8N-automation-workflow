# Selenium Automation Demo

This folder contains a simple Selenium automation project that drives the existing `selenium_demo_forms` Flask app.

## Goal
Automate the following flow using a CSV-driven data file:
1. Open the login page (`/login`).
2. Fill the login form and submit (includes a simple server-generated captcha).
3. Once logged in, fill the “All Inputs” form (`/all-inputs`) and submit.

## Setup
1. Install dependencies (recommended inside a virtual environment):

   ```bash
   pip install -r selenium_automation/requirements.txt
   ```

2. Start the Flask demo server (from the repo root):

   ```bash
   python app.py
   ```

   The demo server will run at: `http://localhost:5000`

3. Run the automation script:

   ```bash
   python selenium_automation/run_automation.py
   ```

## CSV Input Format
The script reads data from `selenium_automation/inputs.csv`. Each row defines one automation run.

### Minimum required columns
- `email` (login/email for both forms)
- `password` (login password and all-inputs password)

If you include these additional columns, the automation will fill them too:
- `username` (login username; defaults to `full_name` or `email` if omitted)
- `role` (login role; defaults to `Student`)
- `comments` (login comments)
- `remember_me` (yes/no; defaults to `yes`)

### Optional columns (for the full form)
- `full_name`
- `phone`
- `website`
- `age`
- `birthdate` (YYYY-MM-DD)
- `appointment` (YYYY-MM-DDTHH:MM)
- `alarm_time` (HH:MM)
- `color` (#RRGGBB)
- `satisfaction` (0-10)
- `volume` (decimal)
- `country`
- `gender` (Male/Female/Other)
- `education` (High School/Bachelor's/Master's/PhD)
- `hobbies` (comma-separated)
- `skills` (comma-separated)
- `terms` (yes/no)

## Notes
- The demo server uses a numeric captcha; the automation script reads the captcha question from the page and solves it automatically.
- Update `inputs.csv` to add different test cases.
