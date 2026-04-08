"""Selenium automation runner for the selenium_demo_forms Flask app.

This is a beginner-friendly script that uses a single CSV file (read via pandas) to
populate the "All Inputs" form. Login values are hardcoded, and only the captcha is
solved at runtime.

Usage:
  uv run selenium_automation/run_automation.py

Prerequisites:
  1) Run `uv pip install -r selenium_automation/requirements.txt`
  2) Start the Flask app (e.g. `python app.py`) on http://localhost:5000
"""

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from dotenv import load_dotenv
from data_class import InputRow
import os
import re
import pandas as pd

# Load .env file (if present) from the script directory.
# This ensures env vars are found even when running from the repo root.
load_dotenv(Path(__file__).resolve().parent / ".env")

driver = webdriver.Chrome()
driver.maximize_window()

CSV_PATH = Path(__file__).resolve().parent /"inputs.csv"

# Login values are loaded from the .env file to keep credentials out of code.
BASE_URL = os.getenv("BASE_URL","")
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME","")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL","")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD","")
LOGIN_ROLE = os.getenv("LOGIN_ROLE","")
LOGIN_COMMENTS = os.getenv("LOGIN_COMMENTS","")
LOGIN_REMEMBER_ME = os.getenv("LOGIN_REMEMBER_ME","")



def solve_captcha(captcha_text: str) -> str:
    # Captcha format: "<num> <op> <num> = ?"
    match = re.search(r"(\d+)\s*([+-])\s*(\d+)", captcha_text)
    if not match:
        raise ValueError(f"Unable to parse captcha: {captcha_text!r}")
    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
    return str(a + b) if op == "+" else str(a - b)


def parse_datetime_local(value: str) -> str:
    """Convert a friendly datetime string into a HTML `datetime-local` value."""
    if not value:
        return ""
    value = str(value).strip()

    # If already in the expected input format, just use it.
    if "T" in value and ":" in value:
        return value

    for fmt in ["%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"]:
        try:
            return pd.to_datetime(value, format=fmt).strftime("%Y-%m-%dT%H:%M")
        except (ValueError, TypeError):
            continue

    # Fall back to pandas generic parse if it can handle it
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%dT%H:%M")
    except Exception:
        raise ValueError(f"Unable to parse datetime-local value: {value!r}")


def parse_time(value: str) -> str:
    """Convert a friendly time string into HH:MM 24-hour format."""
    if not value:
        return ""
    value = str(value).strip()

    for fmt in ["%I:%M %p", "%H:%M"]:
        try:
            return pd.to_datetime(value, format=fmt).strftime("%H:%M")
        except (ValueError, TypeError):
            continue

    try:
        return pd.to_datetime(value).strftime("%H:%M")
    except Exception:
        raise ValueError(f"Unable to parse time value: {value!r}")


def safe_click(driver, element):
    """Click an element safely, retrying via JS if normal click is intercepted."""
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        driver.execute_script("arguments[0].click();", element)


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}


# Login one time 

driver.get(f"{BASE_URL}/login")
time.sleep(1)  # Wait for page to load

driver.find_element(By.ID, "username").send_keys(LOGIN_USERNAME)

driver.find_element(By.ID, "email").send_keys(LOGIN_EMAIL)
 
driver.find_element(By.ID, "password").send_keys(LOGIN_PASSWORD)


Select(driver.find_element(By.ID, "role")).select_by_visible_text(LOGIN_ROLE)

driver.find_element(By.ID, "comments").send_keys(LOGIN_COMMENTS)


captcha_text = driver.find_element(By.ID, "captcha_question").text
driver.find_element(By.ID, "captcha_answer").send_keys(solve_captcha(captcha_text))

driver.find_element(By.ID, "remember_me").click()

driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

# Wait until the automation flow redirects to the all-inputs page.
try:
    WebDriverWait(driver, 15).until(EC.url_contains("/all-inputs"))
except TimeoutException:
    # If it doesn't redirect, print a bit of context to help diagnose.
    print("❌ Login did not redirect to /all-inputs")
    print("Current URL:", driver.current_url)
    print("Page title:", driver.title)
    print("Page snippet:", driver.page_source[:800])
    raise

try:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()  # Remove leading/trailing whitespace from column names
    input_rows = [InputRow(**row) for _, row in df.iterrows()]

    # Ensure that the full form is present before typing.
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "full_name")))

    for row in input_rows:
        # Convert dataclass to dict so `row.get()` works like a normal dict.
        row = vars(row)
        print(f"Processing row: {row}")

        # Ensure we are on the all-inputs page. After each submit, the app redirects to /submissions.
        if "/all-inputs" not in driver.current_url:
            driver.get(f"{BASE_URL}/all-inputs")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "full_name")))

        # Fill in the all-inputs page (values come from the CSV)
        if row.get("full_name"):
            name_el = driver.find_element(By.ID, "full_name")
            name_el.clear()
            name_el.send_keys(row["full_name"])

        if row.get("email"):
            email_el = driver.find_element(By.ID, "email")
            email_el.clear()
            email_el.send_keys(row["email"])

        if row.get("password"):
            pw_el = driver.find_element(By.ID, "password")
            pw_el.clear()
            pw_el.send_keys(row["password"])
     
        if row.get("phone"):
            driver.find_element(By.ID, "phone").send_keys(row["phone"])
          
        if row.get("website"):
            driver.find_element(By.ID, "website").send_keys(row["website"])
           
        if row.get("age"):
            driver.find_element(By.ID, "age").send_keys(str(row["age"]))
          
        if row.get("birthdate"):
            driver.find_element(By.ID, "birthdate").send_keys(row["birthdate"])
           
        if row.get("appointment"):
            elem = driver.find_element(By.ID, "appointment")
            formatted = parse_datetime_local(row["appointment"])
            # datetime-local inputs often work best when setting the value directly.
            driver.execute_script("arguments[0].value = arguments[1];", elem, formatted)

        if row.get("alarm_time"):
            elem = driver.find_element(By.ID, "alarm_time")
            formatted = parse_time(row["alarm_time"])
            driver.execute_script("arguments[0].value = arguments[1];", elem, formatted)
           

        if row.get("gender"):
            try:
                gender_radio = driver.find_element(By.XPATH, f"//input[@name='gender' and @value='{row['gender']}']")
                if not gender_radio.is_selected():
                    safe_click(driver, gender_radio)
                   
            except NoSuchElementException:
                pass
        
        if row.get("hobbies"):
            hobbies = [h.strip() for h in str(row["hobbies"]).split(",") if h.strip()]
            for hobby in hobbies:
                try:
                    checkbox = driver.find_element(By.XPATH, f"//input[@name='hobbies' and @value='{hobby}']")
                    if not checkbox.is_selected():
                        safe_click(driver, checkbox)
                    
                except NoSuchElementException:
                    pass

        if row.get("education"):
            Select(driver.find_element(By.ID, "education")).select_by_visible_text(row["education"])

        if row.get("skills"):
            skills = [s.strip() for s in str(row["skills"]).split(",") if s.strip()]
            select = Select(driver.find_element(By.ID, "skills"))
            select.deselect_all()
            for skill in skills:
                select.select_by_visible_text(skill)
              

        if row.get("color"):
            driver.find_element(By.ID, "color").send_keys(row["color"])
        
        if row.get("satisfaction"):
            driver.find_element(By.ID, "satisfaction").clear()
            driver.find_element(By.ID, "satisfaction").send_keys(row["satisfaction"])
          
        if row.get("volume"):
            driver.find_element(By.ID, "volume").clear()
            driver.find_element(By.ID, "volume").send_keys(row["volume"])
       

        if row.get("country"):
            driver.find_element(By.ID, "country").send_keys(row["country"])
    

        if parse_bool(row.get("terms")):
            checkbox = driver.find_element(By.ID, "terms")
            if not checkbox.is_selected():
                safe_click(driver, checkbox)
        time.sleep(5)
        # Submit the full form
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        safe_click(driver, submit_btn) 
            
        # Wait for redirection to /submissions
        try:
            WebDriverWait(driver, 30).until(EC.url_contains("/submissions"))
        except TimeoutException:
            form = driver.find_element(By.CSS_SELECTOR, "form")
            driver.execute_script("arguments[0].submit();", form)
            WebDriverWait(driver, 30).until(EC.url_contains("/submissions"))

except (TimeoutException, NoSuchElementException) as exc:
    print(f"❌ Error while processing {row.get('full_name', '(no name)')}: {exc}")

finally:
    time.sleep(1)


    driver.quit()



