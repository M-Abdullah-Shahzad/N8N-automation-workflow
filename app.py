from __future__ import annotations

import csv
import os
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'data' / 'demo_submissions.db'
CSV_PATH = BASE_DIR / 'data' / 'demo_submissions.csv'
SECRET_KEY = 'selenium-demo-secret-key-change-me'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS login_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            remember_me INTEGER NOT NULL,
            role TEXT NOT NULL,
            comments TEXT
        )
        '''
    )
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS input_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            full_name TEXT,
            email TEXT NOT NULL UNIQUE,
            password TEXT,
            phone TEXT,
            website TEXT,
            age INTEGER,
            birthdate TEXT,
            appointment TEXT,
            alarm_time TEXT,
            color TEXT,
            satisfaction INTEGER,
            volume REAL,
            country TEXT,
            gender TEXT,
            education TEXT,
            hobbies TEXT,
            skills TEXT,
            hidden_token TEXT,
            terms_accepted INTEGER
        )
        '''
    )
    db.commit()

    ensure_unique_index(
        db,
        table='login_submissions',
        index_name='idx_login_email_unique',
        column='email',
    )
    ensure_unique_index(
        db,
        table='input_submissions',
        index_name='idx_inputs_email_unique',
        column='email',
    )

    db.close()


def ensure_unique_index(db: sqlite3.Connection, table: str, index_name: str, column: str) -> None:
    duplicates = db.execute(
        f'''
        SELECT {column}, COUNT(*) AS total
        FROM {table}
        WHERE {column} IS NOT NULL AND TRIM({column}) != ''
        GROUP BY {column}
        HAVING COUNT(*) > 1
        '''
    ).fetchall()

    for row in duplicates:
        value = row[0]
        db.execute(
            f'''
            DELETE FROM {table}
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM {table}
                WHERE {column} = ?
            )
            AND {column} = ?
            ''',
            (value, value),
        )

    db.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table}({column})')
    db.commit()


def append_csv(row: dict[str, Any]) -> None:
    file_exists = CSV_PATH.exists()
    with CSV_PATH.open('a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def generate_captcha() -> str:
    a = random.randint(10, 99)
    b = random.randint(1, 9)
    operator = random.choice(['+', '-'])
    if operator == '-' and a < b:
        a, b = b, a
    session['captcha_answer'] = str(eval(f'{a}{operator}{b}'))
    return f'{a} {operator} {b} = ?'


def is_logged_in() -> bool:
    return bool(session.get('is_logged_in'))


@app.route('/')
def index() -> Any:
    return redirect(url_for('login_form'))


@app.route('/logout')
def logout() -> Any:
    session.pop('is_logged_in', None)
    session.pop('logged_in_email', None)
    session.pop('logged_in_username', None)
    session.pop('captcha_answer', None)
    flash('Session cleared. You can demonstrate the login flow again.', 'info')
    return redirect(url_for('login_form'))


@app.route('/login', methods=['GET', 'POST'])
def login_form() -> Any:
    if request.method == 'POST':
        form = request.form
        captcha_answer = form.get('captcha_answer', '').strip()
        expected = session.get('captcha_answer', '')

        if captcha_answer != expected:
            flash('Captcha is incorrect. Please try again.', 'danger')
            captcha_question = generate_captcha()
            return render_template('login.html', captcha_question=captcha_question)

        data = {
            'submitted_at': datetime.now().isoformat(timespec='seconds'),
            'username': form.get('username', '').strip(),
            'email': form.get('email', '').strip().lower(),
            'password': form.get('password', ''),
            'remember_me': 1 if form.get('remember_me') else 0,
            'role': form.get('role', '').strip(),
            'comments': form.get('comments', '').strip(),
        }

        if not data['email']:
            flash('Email is required.', 'danger')
            captcha_question = generate_captcha()
            return render_template('login.html', captcha_question=captcha_question)

        db = get_db()
        existing = db.execute(
            'SELECT id FROM login_submissions WHERE email = ?',
            (data['email'],),
        ).fetchone()

        if existing:
            session['is_logged_in'] = True
            session['logged_in_email'] = data['email']
            session['logged_in_username'] = data['username']
            flash('Login already exists for this email. Reusing existing record and moving to the next form.', 'warning')
            return redirect(url_for('all_inputs_form'))

        db.execute(
            '''
            INSERT INTO login_submissions
            (submitted_at, username, email, password, remember_me, role, comments)
            VALUES (:submitted_at, :username, :email, :password, :remember_me, :role, :comments)
            ''',
            data,
        )
        db.commit()
        append_csv({'form_type': 'login', **data})

        session['is_logged_in'] = True
        session['logged_in_email'] = data['email']
        session['logged_in_username'] = data['username']
        flash('Login successful. Now the student is redirected to the full input form.', 'success')
        return redirect(url_for('all_inputs_form'))

    captcha_question = generate_captcha()
    return render_template('login.html', captcha_question=captcha_question)


@app.route('/all-inputs', methods=['GET', 'POST'])
def all_inputs_form() -> Any:
    if not is_logged_in():
        flash('Please complete login first. This page is protected for the demo flow.', 'warning')
        return redirect(url_for('login_form'))

    if request.method == 'POST':
        form = request.form
        email = (form.get('email') or session.get('logged_in_email', '')).strip().lower()
        data = {
            'submitted_at': datetime.now().isoformat(timespec='seconds'),
            'full_name': form.get('full_name', '').strip(),
            'email': email,
            'password': form.get('password', ''),
            'phone': form.get('phone', '').strip(),
            'website': form.get('website', '').strip(),
            'age': form.get('age') or None,
            'birthdate': form.get('birthdate', ''),
            'appointment': form.get('appointment', ''),
            'alarm_time': form.get('alarm_time', ''),
            'color': form.get('color', ''),
            'satisfaction': form.get('satisfaction') or None,
            'volume': form.get('volume') or None,
            'country': form.get('country', '').strip(),
            'gender': form.get('gender', '').strip(),
            'education': form.get('education', '').strip(),
            'hobbies': ', '.join(form.getlist('hobbies')),
            'skills': ', '.join(form.getlist('skills')),
            'hidden_token': form.get('hidden_token', ''),
            'terms_accepted': 1 if form.get('terms') else 0,
        }

        db = get_db()
        existing = db.execute(
            'SELECT id FROM input_submissions WHERE email = ?',
            (data['email'],),
        ).fetchone()

        if existing:
            flash('A detailed submission already exists for this email, so no duplicate row was added.', 'warning')
            return redirect(url_for('submissions'))

        db.execute(
            '''
            INSERT INTO input_submissions (
                submitted_at, full_name, email, password, phone, website,
                age, birthdate, appointment,
                alarm_time, color, satisfaction,
                volume, country, gender, education, hobbies, skills,
                hidden_token, terms_accepted
            )
            VALUES (
                :submitted_at, :full_name, :email, :password, :phone, :website,
                :age, :birthdate, :appointment,
                :alarm_time, :color, :satisfaction,
                :volume, :country, :gender, :education, :hobbies, :skills,
                :hidden_token, :terms_accepted
            )
            ''',
            data,
        )
        db.commit()
        append_csv({'form_type': 'all_inputs', **data})
        flash('Full form submitted successfully. Data stored once only, with duplicate protection.', 'success')
        return redirect(url_for('submissions'))

    return render_template(
        'all_inputs.html',
        logged_in_email=session.get('logged_in_email', ''),
        logged_in_username=session.get('logged_in_username', ''),
    )


@app.route('/submissions')
def submissions() -> Any:
    db = get_db()
    login_rows = db.execute(
        'SELECT * FROM login_submissions ORDER BY id DESC LIMIT 10'
    ).fetchall()
    input_rows = db.execute(
        'SELECT * FROM input_submissions ORDER BY id DESC LIMIT 10'
    ).fetchall()
    return render_template('submissions.html', login_rows=login_rows, input_rows=input_rows)


if __name__ == '__main__':
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    init_db()
    app.run(debug=True)
