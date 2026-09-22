from flask import Flask, jsonify, render_template, request, redirect, session, url_for,send_file
import requests
import sqlite3
import random
import re
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# =========================================================
# JLPT DEMO ACCOUNT
# =========================================================

DEMO_JLPT_EMAIL = "chinnuachu4647@gmail.com"

DATABASE = os.environ.get("DATABASE_PATH", "database.db")

# =========================================================
# JLPT DEMO UNLOCK KEY
# =========================================================

JLPT_DEMO_KEY = "akshu2028"

def get_certificate_progress(user_id, category):
    conn = get_db()
    cursor = conn.cursor()

    # Total lessons in this category
    cursor.execute(
        "SELECT COUNT(*) FROM notes WHERE category = ?",
        (category,)
    )
    total_lessons = cursor.fetchone()[0]

    # Completed lessons in this category
    cursor.execute("""
        SELECT COUNT(DISTINCT lesson_id)
        FROM lesson_progress
        WHERE user_id = ?
          AND completed = 1
          AND lesson_id IN (
              SELECT id
              FROM notes
              WHERE category = ?
          )
    """, (user_id, category))

    completed_lessons = cursor.fetchone()[0]

    conn.close()

    eligible = (
        total_lessons > 0
        and completed_lessons >= total_lessons
    )

    return {
        "category": category,
        "completed": completed_lessons,
        "total": total_lessons,
        "eligible": eligible,
        "percentage": round(
            (completed_lessons / total_lessons) * 100
        ) if total_lessons else 0
    }


def generate_certificate(user_id, category):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    import os
    import re
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth

    # =========================================================
    # SAFE CATEGORY NAME
    # =========================================================

    safe_category = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        category
    ).strip("_")

    if not safe_category:
        safe_category = "Category"

    # =========================================================
    # CERTIFICATE FOLDER
    # =========================================================

    certificate_folder = "certificates"

    os.makedirs(
        certificate_folder,
        exist_ok=True
    )

    certificate_path = os.path.join(
        certificate_folder,
        f"certificate_{user_id}_{safe_category}.pdf"
    )

    # =========================================================
    # CERTIFICATE DATA
    # =========================================================

    progress = get_certificate_progress(
        user_id,
        category
    )

    completed = progress["completed"]
    total = progress["total"]

    issue_date = datetime.now().strftime(
        "%d %B %Y"
    )

    certificate_id = (
        f"JLP-{safe_category.upper()}-"
        f"{str(user_id).zfill(4)}"
    )

    student_name = user["name"]

    # =========================================================
    # LANDSCAPE A4
    # =========================================================

    page_width, page_height = landscape(A4)

    pdf = canvas.Canvas(
        certificate_path,
        pagesize=(page_width, page_height)
    )

    pdf.setTitle(
        f"{category} Certificate - Japanese Learning Portal"
    )

    pdf.setAuthor(
        "Japanese Learning Portal"
    )

    # =========================================================
    # BACKGROUND
    # =========================================================

    pdf.setFillColorRGB(
        0.99,
        0.98,
        0.96
    )

    pdf.rect(
        0,
        0,
        page_width,
        page_height,
        fill=1,
        stroke=0
    )

    # =========================================================
    # OUTER BORDER
    # =========================================================

    pdf.setStrokeColorRGB(
        0.25,
        0.18,
        0.38
    )

    pdf.setLineWidth(5)

    pdf.roundRect(
        25,
        25,
        page_width - 50,
        page_height - 50,
        12,
        stroke=1,
        fill=0
    )

    # =========================================================
    # INNER GOLD BORDER
    # =========================================================

    pdf.setStrokeColorRGB(
        0.72,
        0.55,
        0.22
    )

    pdf.setLineWidth(1.5)

    pdf.roundRect(
        38,
        38,
        page_width - 76,
        page_height - 76,
        8,
        stroke=1,
        fill=0
    )

    # =========================================================
    # DECORATIVE CORNERS
    # =========================================================

    pdf.setFillColorRGB(
        0.72,
        0.55,
        0.22
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawString(
        55,
        page_height - 70,
        "✦"
    )

    pdf.drawRightString(
        page_width - 55,
        page_height - 70,
        "✦"
    )

    pdf.drawString(
        55,
        52,
        "✦"
    )

    pdf.drawRightString(
        page_width - 55,
        52,
        "✦"
    )

    # =========================================================
    # JAPANESE PORTAL TITLE
    # =========================================================

    pdf.setFillColorRGB(
        0.25,
        0.18,
        0.38
    )

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 92,
        "JAPANESE LEARNING PORTAL"
    )

    # =========================================================
    # MAIN TITLE
    # =========================================================

    pdf.setFont(
        "Helvetica-Bold",
        31
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 135,
        "CERTIFICATE OF COMPLETION"
    )

    # =========================================================
    # DECORATIVE LINE
    # =========================================================

    line_width = 180

    pdf.setStrokeColorRGB(
        0.72,
        0.55,
        0.22
    )

    pdf.setLineWidth(2)

    pdf.line(
        (page_width - line_width) / 2,
        page_height - 153,
        (page_width + line_width) / 2,
        page_height - 153
    )

    # =========================================================
    # PORTAL NAME
    # =========================================================

    pdf.setFillColorRGB(
        0.35,
        0.31,
        0.42
    )

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 180,
        "Japanese Learning Portal"
    )

    # =========================================================
    # CATEGORY
    # =========================================================

    pdf.setFillColorRGB(
        0.25,
        0.18,
        0.38
    )

    pdf.setFont(
        "Helvetica-Bold",
        23
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 225,
        category.upper()
    )

    # =========================================================
    # PRESENTATION TEXT
    # =========================================================

    pdf.setFillColorRGB(
        0.20,
        0.18,
        0.25
    )

    pdf.setFont(
        "Helvetica",
        13
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 270,
        "This certificate is proudly presented to"
    )

    # =========================================================
    # STUDENT NAME
    # =========================================================

    pdf.setFillColorRGB(
        0.25,
        0.18,
        0.38
    )

    pdf.setFont(
        "Helvetica-Bold",
        30
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 315,
        student_name
    )

    name_width = stringWidth(
        student_name,
        "Helvetica-Bold",
        30
    )

    pdf.setStrokeColorRGB(
        0.72,
        0.55,
        0.22
    )

    pdf.setLineWidth(1)

    pdf.line(
        (page_width - name_width) / 2,
        page_height - 325,
        (page_width + name_width) / 2,
        page_height - 325
    )

    # =========================================================
    # COMPLETION STATEMENT
    # =========================================================

    pdf.setFillColorRGB(
        0.20,
        0.18,
        0.25
    )

    pdf.setFont(
        "Helvetica",
        13
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 365,
        f"for successfully completing all required {category} lessons."
    )

    # =========================================================
    # COMPLETION BADGE
    # =========================================================

    badge_width = 190
    badge_height = 38

    badge_x = (
        page_width - badge_width
    ) / 2

    badge_y = (
        page_height - 425
    )

    pdf.setFillColorRGB(
        0.93,
        0.89,
        0.97
    )

    pdf.roundRect(
        badge_x,
        badge_y,
        badge_width,
        badge_height,
        19,
        fill=1,
        stroke=0
    )

    pdf.setFillColorRGB(
        0.25,
        0.18,
        0.38
    )

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawCentredString(
        page_width / 2,
        badge_y + 13,
        f"{completed} / {total} LESSONS COMPLETED"
    )

    # =========================================================
    # CERTIFICATE ID
    # =========================================================

    pdf.setFillColorRGB(
        0.38,
        0.35,
        0.42
    )

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawString(
        70,
        82,
        f"Certificate ID: {certificate_id}"
    )

    # =========================================================
    # ISSUE DATE
    # =========================================================

    pdf.drawRightString(
        page_width - 70,
        82,
        f"Issued: {issue_date}"
    )

    # =========================================================
    # TEAM SIGNATURE
    # =========================================================

    signature_path = os.path.join(
        "static",
        "images",
        "team_signature.png"
    )

    if os.path.exists(signature_path):

        signature_width = 180
        signature_height = 65

        signature_x = (
            page_width / 2
            - signature_width / 2
        )

        signature_y = 72

        pdf.drawImage(
            ImageReader(signature_path),
            signature_x,
            signature_y,
            width=signature_width,
            height=signature_height,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto"
        )

    # =========================================================
    # SIGNATURE LINE
    # =========================================================

    signature_line_width = 190

    pdf.setStrokeColorRGB(
        0.30,
        0.27,
        0.34
    )

    pdf.setLineWidth(1)

    pdf.line(
        (page_width - signature_line_width) / 2,
        65,
        (page_width + signature_line_width) / 2,
        65
    )

    # =========================================================
    # SIGNATURE LABEL
    # =========================================================

    pdf.setFillColorRGB(
        0.25,
        0.23,
        0.30
    )

    pdf.setFont(
        "Helvetica-Bold",
        9
    )

    pdf.drawCentredString(
        page_width / 2,
        50,
        "PROJECT DEVELOPERS"
    )

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawCentredString(
        page_width / 2,
        39,
        "A & D"
    )

    # =========================================================
    # JAPANESE-STYLE SEAL
    # =========================================================

    seal_x = page_width - 105
    seal_y = 110

    pdf.setStrokeColorRGB(
        0.70,
        0.12,
        0.12
    )

    pdf.setLineWidth(2)

    pdf.circle(
        seal_x,
        seal_y,
        25,
        stroke=1,
        fill=0
    )

    pdf.setFillColorRGB(
        0.70,
        0.12,
        0.12
    )

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawCentredString(
        seal_x,
        seal_y + 5,
        "認"
    )

    pdf.drawCentredString(
        seal_x,
        seal_y - 9,
        "定"
    )

    # =========================================================
    # FINISH PDF
    # =========================================================

    pdf.save()

    return certificate_path
# =========================================================
# CERTIFICATE PAGE
# =========================================================
@app.route("/certificates")
def certificates():

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT category FROM notes"
    )

    categories = [
        row["category"]
        for row in cursor.fetchall()
    ]

    conn.close()

    certificate_progress = []

    for category in categories:

        progress = get_certificate_progress(
            session["user_id"],
            category
        )

        certificate_progress.append(progress)

    return render_template(
        "certificates.html",
        certificate_progress=certificate_progress
    )

@app.route("/certificate")
def certificate():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    category = request.args.get("category", "").strip()

    if not category:
        return redirect("/dashboard")

    certificate_progress = get_certificate_progress(
        user_id,
        category
    )

    if not certificate_progress["eligible"]:
        return redirect("/dashboard")

    certificate_path = generate_certificate(
        user_id,
        category
    )

    if not certificate_path:
        return redirect("/dashboard")

    return render_template(
        "certificate.html",
        certificate_progress=certificate_progress,
        certificate_path=certificate_path,
        category=category
    )

# =========================================================
# DOWNLOAD CERTIFICATE
# =========================================================

@app.route("/download_certificate")
def download_certificate():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    category = request.args.get("category", "").strip()

    if not category:
        return redirect("/dashboard")

    certificate_progress = get_certificate_progress(
        user_id,
        category
    )

    if not certificate_progress["eligible"]:
        return redirect("/dashboard")

    certificate_path = generate_certificate(
        user_id,
        category
    )

    if not certificate_path:
        return redirect("/dashboard")

    safe_category = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        category
    ).strip("_") or "Category"

    return send_file(
        certificate_path,
        as_attachment=True,
        download_name=(
            f"Japanese_{safe_category}_Certificate.pdf"
        )
    )

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# =========================================================
# NOTIFICATION HELPER
# =========================================================

def create_notification(user_id, title, message, notification_type="general"):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notifications
        (
            user_id,
            title,
            message,
            notification_type
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        title,
        message,
        notification_type
    ))

    conn.commit()
    conn.close()
# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            dob TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # USER SETTINGS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            theme TEXT DEFAULT 'light',
            pronunciation INTEGER DEFAULT 1,
            english_display INTEGER DEFAULT 1,
            notifications INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # LESSON PROGRESS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id)
        )
    """)

    # COMPLETED LESSONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completed_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_id INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, note_id)
        )
    """)

    # QUIZ HISTORY
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            quiz_attempt INTEGER NOT NULL,
            selected_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


# =========================================================
# NOTES TABLE
# =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    conn.commit()

    # =====================================================
    # CERTIFICATE REQUESTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificate_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP,
        certificate_file TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


# =====================================================
# NOTIFICATIONS
# =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
       )
    """)

    # =========================================================
    # JLPT PROGRESS
    # =========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jlpt_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            highest_unlocked_level TEXT NOT NULL DEFAULT 'N5',
            n5_score INTEGER DEFAULT 0,
            n4_score INTEGER DEFAULT 0,
            n3_score INTEGER DEFAULT 0,
            n2_score INTEGER DEFAULT 0,
            n1_score INTEGER DEFAULT 0,
            demo_unlocked INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # =========================================================
    # ADD JLPT DEMO ACCESS COLUMN IF NEEDED
    # =========================================================

    cursor.execute("""
        PRAGMA table_info(jlpt_progress)
    """)

    jlpt_progress_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "demo_unlocked" not in jlpt_progress_columns:

        cursor.execute("""
            ALTER TABLE jlpt_progress
            ADD COLUMN demo_unlocked INTEGER DEFAULT 0
        """)

# =====================================================
# SAVE ALL DATABASE CHANGES
# =====================================================

    conn.commit()


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'general',
            action_url TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # =====================================================
    # HELP DESK REQUESTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # -----------------------------------------------------
    # Upgrade old quiz_history table if necessary
    # -----------------------------------------------------

    cursor.execute("PRAGMA table_info(quiz_history)")
    columns = [row[1] for row in cursor.fetchall()]

    if "selected_answer" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_history
            ADD COLUMN selected_answer TEXT
        """)

    if "correct_answer" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_history
            ADD COLUMN correct_answer TEXT
        """)

    if "is_correct" not in columns:
        cursor.execute("""
            ALTER TABLE quiz_history
            ADD COLUMN is_correct INTEGER DEFAULT 0
        """)

    conn.commit()
    conn.close()

# =========================================================
# ONLINE QUOTE OF THE DAY
# =========================================================

def get_online_quote():

    try:

        # Get random English quote
        response = requests.get(
            "https://zenquotes.io/api/random",
            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            if data and isinstance(data, list):

                quote_text = data[0].get("q", "")
                quote_author = data[0].get("a", "Unknown")

                if quote_text:

                    # Translate English quote to Japanese
                    translation_response = requests.get(
                        "https://api.mymemory.translated.net/get",
                        params={
                            "q": quote_text,
                            "langpair": "en|ja"
                        },
                        timeout=5
                    )

                    japanese_quote = ""

                    if translation_response.status_code == 200:

                        translation_data = (
                            translation_response.json()
                        )

                        japanese_quote = (
                            translation_data
                            .get("responseData", {})
                            .get("translatedText", "")
                        )

                    # If translation fails
                    if not japanese_quote:
                        japanese_quote = (
                            "日本語訳を取得できませんでした。"
                        )

                    return {
                        "text": quote_text,
                        "japanese": japanese_quote,
                        "author": quote_author
                    }

    except Exception:
        pass

    # =====================================================
    # FALLBACK
    # =====================================================

    return {
        "text": "Every Japanese master was once a beginner.",
        "japanese": "日本語の達人も、最初はみんな初心者でした。",
        "author": "Japanese Learning Portal"
    }


# =========================================================
# AUTOMATIC JAPANESE NAME
# =========================================================

def get_japanese_name(name):

    try:
        # Get only the first name/word.
        # Example:
        # "Dharani s" -> "Dharani"
        first_name = name.strip().split()[0]

        if not first_name:
            return ""

        # If the name is already Japanese, don't translate it.
        if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", first_name):
            return first_name

        # Google Translate endpoint for English -> Japanese
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "en",
                "tl": "ja",
                "dt": "t",
                "q": first_name
            },
            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            if data and data[0]:

                japanese_name = ""

                for item in data[0]:

                    if item and item[0]:
                        japanese_name += item[0]

                japanese_name = japanese_name.strip()

                if japanese_name:
                    return japanese_name

    except Exception:
        pass

    # Fallback
    return ""
# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")

# =========================================================
# START LEARNING
# =========================================================

@app.route("/start-learning")
def start_learning():

    return render_template("start_learning.html")
# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        dob = request.form.get("dob", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not dob or not password:
            return "Please fill all the fields."

        if password != confirm_password:
            return "Passwords do not match!"

        # -------------------------------------------------
        # HASH PASSWORD BEFORE SAVING
        # -------------------------------------------------

        password_hash = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (name, email, dob, password)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                dob,
                password_hash
            ))

            conn.commit()

            cursor.execute("""
                INSERT OR IGNORE INTO user_settings
                (user_id)
                VALUES (?)
            """, (
                cursor.lastrowid,
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already exists!"

        conn.close()

        return render_template("login.html")

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================
# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        if user is None:

            conn.close()

            return render_template(
                "login.html",
                login_error="Invalid password or email. Please try again.",
                entered_email=email
            )

        stored_password = user["password"]

        password_valid = False
        legacy_password = False

        # -------------------------------------------------
        # CHECK WHETHER PASSWORD IS ALREADY HASHED
        # -------------------------------------------------

        is_hashed = (
            stored_password.startswith("scrypt:")
            or stored_password.startswith("pbkdf2:")
            or stored_password.startswith("argon2:")
        )

        if is_hashed:

            try:

                password_valid = check_password_hash(
                    stored_password,
                    password
                )

            except (ValueError, TypeError):

                password_valid = False

        else:

            # -------------------------------------------------
            # OLD PLAIN-TEXT PASSWORD
            # -------------------------------------------------

            if stored_password == password:

                password_valid = True
                legacy_password = True

        # -------------------------------------------------
        # INVALID LOGIN
        # -------------------------------------------------

        if not password_valid:

            conn.close()

            return render_template(
                "login.html",
                login_error="Invalid password or email. Please try again.",
                entered_email=email
            )

        # -------------------------------------------------
        # UPGRADE OLD PASSWORD TO SECURE HASH
        # -------------------------------------------------

        if legacy_password:

            password_hash = generate_password_hash(
                password
            )

            cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (
                password_hash,
                user["id"]
            ))

            conn.commit()

        # -------------------------------------------------
        # LOGIN SUCCESSFUL
        # -------------------------------------------------

        session["user_id"] = user["id"]
        session["user"] = user["name"]
        session["email"] = user["email"]

        session.pop("daily_word", None)

        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("login.html")
# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route("/forgot", methods=["GET", "POST"])
def forgot():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        dob = request.form.get("dob", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not email or not dob or not new_password or not confirm_password:
            return "Please fill all the fields."

        if new_password != confirm_password:
            return "Passwords do not match!"

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND dob = ?
        """, (
            email,
            dob
        ))

        user = cursor.fetchone()

        if user:

            # -------------------------------------------------
            # HASH NEW PASSWORD
            # -------------------------------------------------

            new_password_hash = generate_password_hash(
                new_password
            )

            cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (
                new_password_hash,
                user["id"]
            ))

            conn.commit()
            conn.close()

            return render_template("login.html")

        conn.close()

        return "Invalid Email or Date of Birth!"

    return render_template("forgot_password.html")
# =========================================================
# DASHBOARD
# =========================================================
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    from datetime import datetime

    # =====================================================
    # DYNAMIC GREETING
    # =====================================================

    current_hour = datetime.now().hour

    if 5 <= current_hour < 12:

        greeting_japanese = "おはようございます！"
        greeting_english = "Good Morning!"

    elif 12 <= current_hour < 18:

        greeting_japanese = "こんにちは！"
        greeting_english = "Good Afternoon!"

    else:

        greeting_japanese = "こんばんは！"
        greeting_english = "Good Evening!"


    # =====================================================
    # JAPANESE WORDS
    # =====================================================

    japanese_words = [

        {
            "japanese": "ありがとう",
            "romaji": "Arigatou",
            "meaning": "Thank you",
            "example": "ありがとうございます！",
            "example_meaning": "Thank you very much!"
        },

        {
            "japanese": "こんにちは",
            "romaji": "Konnichiwa",
            "meaning": "Hello / Good afternoon",
            "example": "こんにちは、先生！",
            "example_meaning": "Hello, teacher!"
        },

        {
            "japanese": "頑張る",
            "romaji": "Ganbaru",
            "meaning": "To do your best / To persevere",
            "example": "頑張ります！",
            "example_meaning": "I'll do my best!"
        },

        {
            "japanese": "友達",
            "romaji": "Tomodachi",
            "meaning": "Friend",
            "example": "私の友達です。",
            "example_meaning": "This is my friend."
        },

        {
            "japanese": "先生",
            "romaji": "Sensei",
            "meaning": "Teacher",
            "example": "先生、おはようございます。",
            "example_meaning": "Good morning, teacher."
        },

        {
            "japanese": "学校",
            "romaji": "Gakkou",
            "meaning": "School",
            "example": "学校へ行きます。",
            "example_meaning": "I go to school."
        },

        {
            "japanese": "本",
            "romaji": "Hon",
            "meaning": "Book",
            "example": "本を読みます。",
            "example_meaning": "I read a book."
        },

        {
            "japanese": "水",
            "romaji": "Mizu",
            "meaning": "Water",
            "example": "水をください。",
            "example_meaning": "Please give me some water."
        },

        {
            "japanese": "楽しい",
            "romaji": "Tanoshii",
            "meaning": "Fun / Enjoyable",
            "example": "日本語は楽しいです。",
            "example_meaning": "Japanese is fun."
        },

        {
            "japanese": "夢",
            "romaji": "Yume",
            "meaning": "Dream",
            "example": "夢があります。",
            "example_meaning": "I have a dream."
        }

    ]


    # =====================================================
    # SELECT WORD FOR THIS LOGIN SESSION
    # =====================================================

    if "daily_word" not in session:
        session["daily_word"] = random.choice(japanese_words)

    word = session["daily_word"]

   # =====================================================
   # GET ONLINE QUOTE
   # =====================================================

    quote = get_online_quote()

        # =====================================================
    # JAPANESE USER NAME
    # =====================================================

    username = session["user"]

    username_japanese = get_japanese_name(username)

    # =====================================================
    # CATEGORY-WISE CERTIFICATE PROGRESS
    # =====================================================
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT category
        FROM notes
        WHERE category IS NOT NULL
          AND TRIM(category) != ''
        ORDER BY category
    """)
    categories = [row["category"] for row in cursor.fetchall()]

    # GET USER NOTIFICATIONS

    cursor.execute("""
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))

    notifications = cursor.fetchall()




    conn.close()

    certificate_progress = [
        get_certificate_progress(
            session["user_id"],
            category
        )
        for category in categories
    ]


    # =====================================================
    # RENDER DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",

        username=username,

        username_japanese=username_japanese,

        greeting_japanese=greeting_japanese,

        greeting_english=greeting_english,

        word=word,

        quote=quote,

        certificate_progress=certificate_progress,

        notifications=notifications
    )
#notifications read
@app.route("/mark_notifications_read", methods=["POST"])
def mark_notifications_read():

    if "user_id" not in session:
        return "", 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = ?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return "", 204

@app.route("/delete_notification/<int:notification_id>", methods=["POST"])
def delete_notification(notification_id):

    if "user_id" not in session:
        return "", 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM notifications
        WHERE id = ?
          AND user_id = ?
    """, (notification_id, session["user_id"]))

    conn.commit()
    conn.close()

    return "", 204


@app.route("/clear_notifications", methods=["POST"])
def clear_notifications():

    if "user_id" not in session:
        return "", 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM notifications
        WHERE user_id = ?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return "", 204


# =========================================================
# HELP DESK
# =========================================================

@app.route("/help-desk", methods=["GET", "POST"])
@app.route("/help_desk", methods=["GET", "POST"])
def help_desk():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method == "POST":

        category = request.form.get("category", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        valid_categories = {
            "Account",
            "Lessons",
            "Quiz",
            "Certificates",
            "Technical Issue",
            "Other"
        }

        if category not in valid_categories:
            category = "Other"

        if not subject or not message:
            return render_template(
                "help_desk.html",
                username=session["user"],
                requests=[],
                form_error="Please enter a subject and message.",
                form_category=category,
                form_subject=subject,
                form_message=message
            )

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO help_requests
            (
                user_id,
                category,
                subject,
                message
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            category,
            subject,
            message
        ))

        conn.commit()
        conn.close()

        return redirect("/help-desk")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            category,
            subject,
            message,
            status,
            admin_reply,
            created_at,
            updated_at
        FROM help_requests
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
    """, (user_id,))

    help_requests = cursor.fetchall()
    conn.close()

    return render_template(
        "help_desk.html",
        username=session["user"],
        requests=help_requests,
        form_error=None,
        form_category="Other",
        form_subject="",
        form_message=""
    )


# =========================================================
# LEARNING HUB
# =========================================================

@app.route("/learning_hub")
def learning_hub():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "learning_hub.html",
        username=session["user"]
    )

# =========================================================
# TRANSLATOR
# =========================================================
@app.route("/translator", methods=["GET", "POST"])
def translator():

    if "user_id" not in session:
        return redirect("/login")

    text = ""
    result = ""
    direction = "en_to_ja"

    if request.method == "POST":

        text = request.form.get("text", "").strip()
        direction = request.form.get("direction", "en_to_ja")

        if text:

            if direction == "en_to_ja":
                langpair = "en|ja"
            else:
                langpair = "ja|en"

            try:

                response = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={
                        "q": text,
                        "langpair": langpair,
                        "de": "japaneselearningportal@example.com"
                    },
                    timeout=10
                )

                print("MyMemory status:", response.status_code)

                if response.status_code == 200:

                    data = response.json()

                    # MyMemory may return the translation in either
                    # responseData.translatedText or matches[].translation.
                    result = (
                        data.get("responseData", {})
                        .get("translatedText", "")
                        .strip()
                    )

                    if not result:

                        for match in data.get("matches", []):

                            translation = match.get(
                                "translation",
                                ""
                            )

                            if translation:
                                translation = str(translation).strip()

                            if translation:
                                result = translation
                                break

                    # Some MyMemory responses can contain HTML entities.
                    if result:
                        from html import unescape
                        result = unescape(result).strip()

                    print("Translation result:", repr(result))

                    if not result:

                        if direction == "en_to_ja":
                            result = "Translation not found."
                        else:
                            result = "翻訳が見つかりません。"

                else:
                    result = "Translation service unavailable."

            except requests.RequestException as error:

                print("Translation request error:", error)

                result = (
                    "Could not connect to the translation service."
                )

            except (ValueError, TypeError) as error:

                print("Translation processing error:", error)

                result = (
                    "Could not process the translation."
                )

    return render_template(
        "translator.html",
        username=session["user"],
        text=text,
        result=result,
        direction=direction
    )

# =========================================================
# FLASHCARDS
# =========================================================

@app.route("/flashcards")
def flashcards():

    if "user_id" not in session:
        return redirect("/login")

    import random

    flashcards_data = [

        {
            "japanese": "水",
            "romaji": "Mizu",
            "meaning": "Water"
        },

        {
            "japanese": "猫",
            "romaji": "Neko",
            "meaning": "Cat"
        },

        {
            "japanese": "犬",
            "romaji": "Inu",
            "meaning": "Dog"
        },

        {
            "japanese": "学校",
            "romaji": "Gakkou",
            "meaning": "School"
        },

        {
            "japanese": "先生",
            "romaji": "Sensei",
            "meaning": "Teacher"
        },

        {
            "japanese": "友達",
            "romaji": "Tomodachi",
            "meaning": "Friend"
        },

        {
            "japanese": "本",
            "romaji": "Hon",
            "meaning": "Book"
        },

        {
            "japanese": "日本",
            "romaji": "Nihon",
            "meaning": "Japan"
        },

        {
            "japanese": "学生",
            "romaji": "Gakusei",
            "meaning": "Student"
        },

        {
            "japanese": "先生",
            "romaji": "Sensei",
            "meaning": "Teacher"
        },

        {
            "japanese": "家",
            "romaji": "Ie",
            "meaning": "House"
        },

        {
            "japanese": "車",
            "romaji": "Kuruma",
            "meaning": "Car"
        },

        {
            "japanese": "電車",
            "romaji": "Densha",
            "meaning": "Train"
        },

        {
            "japanese": "駅",
            "romaji": "Eki",
            "meaning": "Station"
        },

        {
            "japanese": "学校",
            "romaji": "Gakkou",
            "meaning": "School"
        },

        {
            "japanese": "食べ物",
            "romaji": "Tabemono",
            "meaning": "Food"
        },

        {
            "japanese": "飲み物",
            "romaji": "Nomimono",
            "meaning": "Drink"
        },

        {
            "japanese": "朝",
            "romaji": "Asa",
            "meaning": "Morning"
        },

        {
            "japanese": "夜",
            "romaji": "Yoru",
            "meaning": "Night"
        },

        {
            "japanese": "今日",
            "romaji": "Kyou",
            "meaning": "Today"
        },

        {
            "japanese": "明日",
            "romaji": "Ashita",
            "meaning": "Tomorrow"
        },

        {
            "japanese": "昨日",
            "romaji": "Kinou",
            "meaning": "Yesterday"
        },

        {
            "japanese": "天気",
            "romaji": "Tenki",
            "meaning": "Weather"
        },

        {
            "japanese": "雨",
            "romaji": "Ame",
            "meaning": "Rain"
        },

        {
            "japanese": "空",
            "romaji": "Sora",
            "meaning": "Sky"
        },

        {
            "japanese": "山",
            "romaji": "Yama",
            "meaning": "Mountain"
        },

        {
            "japanese": "川",
            "romaji": "Kawa",
            "meaning": "River"
        },

        {
            "japanese": "花",
            "romaji": "Hana",
            "meaning": "Flower"
        },

        {
            "japanese": "友達",
            "romaji": "Tomodachi",
            "meaning": "Friend"
        },

        {
            "japanese": "先生",
            "romaji": "Sensei",
            "meaning": "Teacher"
        },

        {
            "japanese": "会社",
            "romaji": "Kaisha",
            "meaning": "Company"
        },

        {
            "japanese": "仕事",
            "romaji": "Shigoto",
            "meaning": "Work"
        },

        {
            "japanese": "時間",
            "romaji": "Jikan",
            "meaning": "Time"
        },

        {
            "japanese": "名前",
            "romaji": "Namae",
            "meaning": "Name"
        },

        {
            "japanese": "電話",
            "romaji": "Denwa",
            "meaning": "Telephone"
        },

        {
            "japanese": "言葉",
            "romaji": "Kotoba",
            "meaning": "Word / Language"
        },

        {
            "japanese": "日本語",
            "romaji": "Nihongo",
            "meaning": "Japanese language"
        },

        {
            "japanese": "英語",
            "romaji": "Eigo",
            "meaning": "English language"
        },

        {
            "japanese": "お金",
            "romaji": "Okane",
            "meaning": "Money"
        },

        {
            "japanese": "店",
            "romaji": "Mise",
            "meaning": "Shop"
        },

        {
            "japanese": "病院",
            "romaji": "Byouin",
            "meaning": "Hospital"
        }

    ]


    # Pick 8 different cards randomly
    selected_cards = random.sample(
        flashcards_data,
        8
    )


    return render_template(
        "flashcards.html",
        flashcards=selected_cards,
        username=session["user"]
    )
# =========================================================
# JLPT PROGRESS HELPER
# =========================================================

def get_jlpt_progress(user_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jlpt_progress
        (
            user_id,
            highest_unlocked_level,
            demo_unlocked
        )
        VALUES (?, 'N5', 0)
    """, (user_id,))

    conn.commit()

    cursor.execute("""
        SELECT
            highest_unlocked_level,
            n5_score,
            n4_score,
            n3_score,
            n2_score,
            n1_score,
            demo_unlocked
        FROM jlpt_progress
        WHERE user_id = ?
    """, (user_id,))

    progress = cursor.fetchone()

    conn.close()

    return progress


# =========================================================
# JLPT LEVEL UNLOCK HELPER
# =========================================================

def jlpt_level_unlocked(level, progress):

    if not progress:
        return level == "N5"

    highest = progress["highest_unlocked_level"]

    level_order = {
        "N5": 5,
        "N4": 4,
        "N3": 3,
        "N2": 2,
        "N1": 1
    }

    # Demo mode unlocks every JLPT level.
    if progress["demo_unlocked"] == 1:
        return True

    return level_order[level] >= level_order[highest]


# =========================================================
# SAVE JLPT SCORE + UNLOCK NEXT LEVEL
# =========================================================

def save_jlpt_score(user_id, level, percentage):

    next_level = {
        "N5": "N4",
        "N4": "N3",
        "N3": "N2",
        "N2": "N1"
    }.get(level)

    score_column = f"{level.lower()}_score"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jlpt_progress
        (
            user_id,
            highest_unlocked_level,
            n5_score,
            n4_score,
            n3_score,
            n2_score,
            n1_score,
            demo_unlocked
        )
        VALUES (?, 'N5', 0, 0, 0, 0, 0, 0)
    """, (user_id,))

    if next_level:
        cursor.execute(f"""
            UPDATE jlpt_progress
            SET
                {score_column} = ?,
                highest_unlocked_level =
                    CASE
                        WHEN ? >= 80
                             AND (
                                 highest_unlocked_level = 'N5'
                                 OR
                                 CASE
                                     WHEN highest_unlocked_level = 'N4' THEN 4
                                     WHEN highest_unlocked_level = 'N3' THEN 3
                                     WHEN highest_unlocked_level = 'N2' THEN 2
                                     WHEN highest_unlocked_level = 'N1' THEN 1
                                     ELSE 5
                                 END
                                 >
                                 CASE
                                     WHEN ? = 'N4' THEN 4
                                     WHEN ? = 'N3' THEN 3
                                     WHEN ? = 'N2' THEN 2
                                     WHEN ? = 'N1' THEN 1
                                     ELSE 5
                                 END
                             )
                        THEN ?
                        ELSE highest_unlocked_level
                    END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            percentage,
            percentage,
            next_level,
            next_level,
            next_level,
            next_level,
            next_level,
            user_id
        ))
    else:
        cursor.execute(f"""
            UPDATE jlpt_progress
            SET
                {score_column} = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            percentage,
            user_id
        ))

    conn.commit()
    conn.close()


# =========================================================
# JLPT PRACTICE
# =========================================================

@app.route("/jlpt")
def jlpt():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    progress = get_jlpt_progress(user_id)

    return render_template(
        "jlpt.html",

        username=session["user"],

        highest_unlocked_level=(
            progress["highest_unlocked_level"]
        ),

        n5_score=(
            progress["n5_score"]
        ),

        n4_score=(
            progress["n4_score"]
        ),

        n3_score=(
            progress["n3_score"]
        ),

        n2_score=(
            progress["n2_score"]
        ),

        n1_score=(
            progress["n1_score"]
        ),

        demo_unlocked=(
            progress["demo_unlocked"]
        )
    )
# =========================================================
# JLPT N5 PRACTICE
# 32 QUESTION TEST + ANSWER REVIEW
# =========================================================

@app.route("/jlpt/n5", methods=["GET", "POST"])
def jlpt_n5():

    if "user_id" not in session:
        return redirect("/login")

    # =====================================================
    # 32 N5 QUESTIONS
    # =====================================================

    questions = [

        # -------------------------------------------------
        # VOCABULARY
        # -------------------------------------------------

        {
            "category": "Vocabulary",
            "question": "「水」の意味はどれですか？",
            "english": "What does 「水」 mean?",
            "options": [
                "Water",
                "Fire",
                "Book",
                "School"
            ],
            "answer": "Water"
        },

        {
            "category": "Vocabulary",
            "question": "「猫」の意味はどれですか？",
            "english": "What does 「猫」 mean?",
            "options": [
                "Cat",
                "Dog",
                "Bird",
                "Fish"
            ],
            "answer": "Cat"
        },

        {
            "category": "Vocabulary",
            "question": "「犬」の意味はどれですか？",
            "english": "What does 「犬」 mean?",
            "options": [
                "Dog",
                "Cat",
                "Teacher",
                "Student"
            ],
            "answer": "Dog"
        },

        {
            "category": "Vocabulary",
            "question": "「学校」の意味はどれですか？",
            "english": "What does 「学校」 mean?",
            "options": [
                "School",
                "Hospital",
                "Station",
                "Library"
            ],
            "answer": "School"
        },

        {
            "category": "Vocabulary",
            "question": "「先生」の意味はどれですか？",
            "english": "What does 「先生」 mean?",
            "options": [
                "Teacher",
                "Student",
                "Friend",
                "Parent"
            ],
            "answer": "Teacher"
        },

        {
            "category": "Vocabulary",
            "question": "「友達」の意味はどれですか？",
            "english": "What does 「友達」 mean?",
            "options": [
                "Friend",
                "Teacher",
                "Brother",
                "Student"
            ],
            "answer": "Friend"
        },

        # -------------------------------------------------
        # HIRAGANA
        # -------------------------------------------------

        {
            "category": "Hiragana",
            "question": "「あ」の読み方はどれですか？",
            "english": "How is 「あ」 read?",
            "options": [
                "a",
                "i",
                "u",
                "e"
            ],
            "answer": "a"
        },

        {
            "category": "Hiragana",
            "question": "「か」の読み方はどれですか？",
            "english": "How is 「か」 read?",
            "options": [
                "ka",
                "ki",
                "ku",
                "ke"
            ],
            "answer": "ka"
        },

        {
            "category": "Hiragana",
            "question": "「さ」の読み方はどれですか？",
            "english": "How is 「さ」 read?",
            "options": [
                "sa",
                "shi",
                "su",
                "se"
            ],
            "answer": "sa"
        },

        {
            "category": "Hiragana",
            "question": "「た」の読み方はどれですか？",
            "english": "How is 「た」 read?",
            "options": [
                "ta",
                "chi",
                "tsu",
                "te"
            ],
            "answer": "ta"
        },

        {
            "category": "Hiragana",
            "question": "「な」の読み方はどれですか？",
            "english": "How is 「な」 read?",
            "options": [
                "na",
                "ni",
                "nu",
                "ne"
            ],
            "answer": "na"
        },

        # -------------------------------------------------
        # KATAKANA
        # -------------------------------------------------

        {
            "category": "Katakana",
            "question": "「ア」の読み方はどれですか？",
            "english": "How is 「ア」 read?",
            "options": [
                "a",
                "i",
                "u",
                "e"
            ],
            "answer": "a"
        },

        {
            "category": "Katakana",
            "question": "「カ」の読み方はどれですか？",
            "english": "How is 「カ」 read?",
            "options": [
                "ka",
                "ki",
                "ku",
                "ke"
            ],
            "answer": "ka"
        },

        {
            "category": "Katakana",
            "question": "「サ」の読み方はどれですか？",
            "english": "How is 「サ」 read?",
            "options": [
                "sa",
                "shi",
                "su",
                "se"
            ],
            "answer": "sa"
        },

        {
            "category": "Katakana",
            "question": "「タ」の読み方はどれですか？",
            "english": "How is 「タ」 read?",
            "options": [
                "ta",
                "chi",
                "tsu",
                "te"
            ],
            "answer": "ta"
        },

        {
            "category": "Katakana",
            "question": "「ナ」の読み方はどれですか？",
            "english": "How is 「ナ」 read?",
            "options": [
                "na",
                "ni",
                "nu",
                "ne"
            ],
            "answer": "na"
        },

        # -------------------------------------------------
        # GRAMMAR
        # -------------------------------------------------

        {
            "category": "Grammar",
            "question": "私は学生___。",
            "english": "I am a student.",
            "options": [
                "です",
                "ます",
                "でした",
                "ません"
            ],
            "answer": "です"
        },

        {
            "category": "Grammar",
            "question": "これは本___。",
            "english": "This is a book.",
            "options": [
                "です",
                "ます",
                "でした",
                "ません"
            ],
            "answer": "です"
        },

        {
            "category": "Grammar",
            "question": "毎日学校へ___。",
            "english": "I go to school every day.",
            "options": [
                "行きます",
                "食べます",
                "見ます",
                "飲みます"
            ],
            "answer": "行きます"
        },

        {
            "category": "Grammar",
            "question": "りんごを___。",
            "english": "I eat an apple.",
            "options": [
                "食べます",
                "行きます",
                "来ます",
                "寝ます"
            ],
            "answer": "食べます"
        },

        {
            "category": "Grammar",
            "question": "水を___。",
            "english": "I drink water.",
            "options": [
                "飲みます",
                "食べます",
                "読みます",
                "書きます"
            ],
            "answer": "飲みます"
        },

        {
            "category": "Grammar",
            "question": "本を___。",
            "english": "I read a book.",
            "options": [
                "読みます",
                "飲みます",
                "行きます",
                "寝ます"
            ],
            "answer": "読みます"
        },

        # -------------------------------------------------
        # KANJI
        # -------------------------------------------------

        {
            "category": "Kanji",
            "question": "「山」の意味はどれですか？",
            "english": "What does 「山」 mean?",
            "options": [
                "Mountain",
                "River",
                "Tree",
                "Road"
            ],
            "answer": "Mountain"
        },

        {
            "category": "Kanji",
            "question": "「川」の意味はどれですか？",
            "english": "What does 「川」 mean?",
            "options": [
                "River",
                "Mountain",
                "School",
                "House"
            ],
            "answer": "River"
        },

        {
            "category": "Kanji",
            "question": "「木」の意味はどれですか？",
            "english": "What does 「木」 mean?",
            "options": [
                "Tree",
                "River",
                "Mountain",
                "Fire"
            ],
            "answer": "Tree"
        },

        {
            "category": "Kanji",
            "question": "「日」の意味はどれですか？",
            "english": "What does 「日」 mean?",
            "options": [
                "Day / Sun",
                "Moon",
                "Fire",
                "Water"
            ],
            "answer": "Day / Sun"
        },

        {
            "category": "Kanji",
            "question": "「月」の意味はどれですか？",
            "english": "What does 「月」 mean?",
            "options": [
                "Moon / Month",
                "Sun",
                "Tree",
                "Mountain"
            ],
            "answer": "Moon / Month"
        },

        # -------------------------------------------------
        # READING
        # -------------------------------------------------

        {
            "category": "Reading",
            "question": "「これは本です。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "This is a book.",
                "This is water.",
                "That is a teacher.",
                "I read a book."
            ],
            "answer": "This is a book."
        },
                {
            "category": "Reading",
            "question": "「私は毎日学校へ行きます。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "I go to school every day.",
                "I eat at school every day.",
                "I read a book every day.",
                "I drink water every day."
            ],
            "answer": "I go to school every day."
        },

        {
            "category": "Reading",
            "question": "「私は学生です。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "I am a student.",
                "I am a teacher.",
                "I go to school.",
                "I read a book."
            ],
            "answer": "I am a student."
        },

        {
            "category": "Reading",
            "question": "「水をください。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Please give me water.",
                "I drink water.",
                "This is water.",
                "I have water."
            ],
            "answer": "Please give me water."
        },

        {
            "category": "Reading",
            "question": "「おはようございます。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Good morning.",
                "Good afternoon.",
                "Good night.",
                "Goodbye."
            ],
            "answer": "Good morning."
        }
    ]

    # =====================================================
    # QUIZ STATE
    # =====================================================

    quiz_questions = session.get(
        "jlpt_n5_questions"
    )

    current_index = session.get(
        "jlpt_n5_index",
        0
    )

    score = session.get(
        "jlpt_n5_score",
        0
    )

    category_scores = session.get(
        "jlpt_n5_category_scores",
        {
            "Vocabulary": 0,
            "Hiragana": 0,
            "Katakana": 0,
            "Grammar": 0,
            "Kanji": 0,
            "Reading": 0
        }
    )

    # =====================================================
    # ANSWER REVIEW STATE
    # =====================================================

    n5_answers = session.get(
        "jlpt_n5_answers",
        {}
    )

    # =====================================================
    # START NEW QUIZ
    # =====================================================

    if request.method == "GET":

        quiz_questions = questions.copy()

        random.shuffle(
            quiz_questions
        )

        current_index = 0

        score = 0

        category_scores = {
            "Vocabulary": 0,
            "Hiragana": 0,
            "Katakana": 0,
            "Grammar": 0,
            "Kanji": 0,
            "Reading": 0
        }

        n5_answers = {}

        session["jlpt_n5_questions"] = (
            quiz_questions
        )

        session["jlpt_n5_index"] = 0

        session["jlpt_n5_score"] = 0

        session["jlpt_n5_category_scores"] = (
            category_scores
        )

        session["jlpt_n5_answers"] = (
            n5_answers
        )

    # =====================================================
    # SAFETY
    # =====================================================

    if not quiz_questions:

        quiz_questions = questions.copy()

        random.shuffle(
            quiz_questions
        )

        current_index = 0

        score = 0

        category_scores = {
            "Vocabulary": 0,
            "Hiragana": 0,
            "Katakana": 0,
            "Grammar": 0,
            "Kanji": 0,
            "Reading": 0
        }

        n5_answers = {}

        session["jlpt_n5_questions"] = (
            quiz_questions
        )

        session["jlpt_n5_index"] = 0

        session["jlpt_n5_score"] = 0

        session["jlpt_n5_category_scores"] = (
            category_scores
        )

        session["jlpt_n5_answers"] = (
            n5_answers
        )

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if request.method == "POST":

        answer = request.form.get(
            "answer",
            ""
        ).strip()

        # -------------------------------------------------
        # Make sure the question exists
        # -------------------------------------------------

        if (
            0 <= current_index <
            len(quiz_questions)
        ):

            current_question = (
                quiz_questions[current_index]
            )

            # -------------------------------------------------
            # SAVE ANSWER FOR REVIEW
            # -------------------------------------------------

            n5_answers[str(current_index)] = {

                "question":
                    current_question.get(
                        "question",
                        ""
                    ),

                "english":
                    current_question.get(
                        "english",
                        ""
                    ),

                "category":
                    current_question.get(
                        "category",
                        ""
                    ),

                "your_answer":
                    answer,

                "correct_answer":
                    current_question.get(
                        "answer",
                        ""
                    )
            }

            session["jlpt_n5_answers"] = (
                n5_answers
            )

            # -------------------------------------------------
            # CHECK CORRECT ANSWER
            # -------------------------------------------------

            if (
                answer ==
                current_question["answer"]
            ):

                score += 1

                category = (
                    current_question["category"]
                )

                category_scores[category] = (
                    category_scores.get(
                        category,
                        0
                    ) + 1
                )

        # -------------------------------------------------
        # MOVE TO NEXT QUESTION
        # -------------------------------------------------

        current_index += 1

        session["jlpt_n5_index"] = (
            current_index
        )

        session["jlpt_n5_score"] = (
            score
        )

        session["jlpt_n5_category_scores"] = (
            category_scores
        )

    # =====================================================
    # FINISHED
    # =====================================================

    if current_index >= len(quiz_questions):

        total = len(quiz_questions)

        percentage = round(
            (score / total) * 100
        )

        result_category_scores = (
            category_scores.copy()
        )

        result_n5_answers = (
            n5_answers.copy()
        )

        # =================================================
        # SAVE N5 SCORE + UNLOCK N4
        # =================================================

        save_jlpt_score(
            session["user_id"],
            "N5",
            percentage
        )

        # -------------------------------------------------
        # CLEAR QUIZ STATE
        # -------------------------------------------------

        session.pop(
            "jlpt_n5_questions",
            None
        )

        session.pop(
            "jlpt_n5_index",
            None
        )

        session.pop(
            "jlpt_n5_score",
            None
        )

        session.pop(
            "jlpt_n5_category_scores",
            None
        )

        session.pop(
            "jlpt_n5_answers",
            None
        )

        # -------------------------------------------------
        # RESULT PAGE
        # -------------------------------------------------

        return render_template(
            "jlpt_n5_result.html",

            username=session["user"],

            score=score,

            total=total,

            total_questions=total,

            percentage=percentage,

            category_scores=(
                result_category_scores
            ),

            review=(
                result_n5_answers
            )
        )

    # =====================================================
    # CURRENT QUESTION
    # =====================================================

    current_question = (
        quiz_questions[current_index]
    )

    # =====================================================
    # SHUFFLE ANSWER OPTIONS
    # =====================================================

    display_question = (
        current_question.copy()
    )

    options = (
        display_question["options"].copy()
    )

    random.shuffle(
        options
    )

    display_question["options"] = (
        options
    )

    # =====================================================
    # RENDER QUESTION
    # =====================================================

    return render_template(
        "jlpt_n5.html",

        username=session["user"],

        question=display_question,

        question_number=(
            current_index + 1
        ),

        total_questions=(
            len(quiz_questions)
        ),

        score=score
    )

# =========================================================
# JLPT N4 PRACTICE
# 32 QUESTIONS
# =========================================================
@app.route("/jlpt/n4", methods=["GET", "POST"])
def jlpt_n4():

    if "user_id" not in session:
        return redirect("/login")

    # =====================================================
    # CHECK N4 ACCESS
    # =====================================================

    progress = get_jlpt_progress(
        session["user_id"]
    )

    if not jlpt_level_unlocked(
        "N4",
        progress
    ):
        return redirect("/jlpt")
    # =====================================================
    # 32 QUESTIONS
    # =====================================================

    questions = [

        # =================================================
        # VOCABULARY - 8
        # =================================================

        {
            "category": "Vocabulary",
            "question": "「必要」の意味はどれですか？",
            "english": "What does 「必要」 mean?",
            "options": [
                "Necessary",
                "Convenient",
                "Dangerous",
                "Difficult"
            ],
            "answer": "Necessary"
        },

        {
            "category": "Vocabulary",
            "question": "「経験」の意味はどれですか？",
            "english": "What does 「経験」 mean?",
            "options": [
                "Experience",
                "Promise",
                "Question",
                "Reason"
            ],
            "answer": "Experience"
        },

        {
            "category": "Vocabulary",
            "question": "「準備」の意味はどれですか？",
            "english": "What does 「準備」 mean?",
            "options": [
                "Preparation",
                "Invitation",
                "Explanation",
                "Decision"
            ],
            "answer": "Preparation"
        },

        {
            "category": "Vocabulary",
            "question": "「連絡」の意味はどれですか？",
            "english": "What does 「連絡」 mean?",
            "options": [
                "Contact",
                "Travel",
                "Change",
                "Repair"
            ],
            "answer": "Contact"
        },

        {
            "category": "Vocabulary",
            "question": "「約束」の意味はどれですか？",
            "english": "What does 「約束」 mean?",
            "options": [
                "Promise / Appointment",
                "Memory",
                "Weather",
                "Address"
            ],
            "answer": "Promise / Appointment"
        },

        {
            "category": "Vocabulary",
            "question": "「最近」の意味はどれですか？",
            "english": "What does 「最近」 mean?",
            "options": [
                "Recently",
                "Usually",
                "Finally",
                "Already"
            ],
            "answer": "Recently"
        },

        {
            "category": "Vocabulary",
            "question": "「簡単」の意味はどれですか？",
            "english": "What does 「簡単」 mean?",
            "options": [
                "Easy / Simple",
                "Expensive",
                "Crowded",
                "Quiet"
            ],
            "answer": "Easy / Simple"
        },

        {
            "category": "Vocabulary",
            "question": "「特別」の意味はどれですか？",
            "english": "What does 「特別」 mean?",
            "options": [
                "Special",
                "Normal",
                "Famous",
                "Similar"
            ],
            "answer": "Special"
        },

        # =================================================
        # KANJI - 6
        # =================================================

        {
            "category": "Kanji",
            "question": "「経験」の「験」は何と読みますか？",
            "english": "How is 「験」 read in 「経験」?",
            "options": [
                "けん",
                "げん",
                "かん",
                "せん"
            ],
            "answer": "けん"
        },

        {
            "category": "Kanji",
            "question": "「旅行」の意味はどれですか？",
            "english": "What does 「旅行」 mean?",
            "options": [
                "Travel / Trip",
                "Study",
                "Work",
                "Shopping"
            ],
            "answer": "Travel / Trip"
        },

        {
            "category": "Kanji",
            "question": "「問題」の意味はどれですか？",
            "english": "What does 「問題」 mean?",
            "options": [
                "Problem / Question",
                "Answer",
                "Example",
                "Lesson"
            ],
            "answer": "Problem / Question"
        },

        {
            "category": "Kanji",
            "question": "「必要」の読み方はどれですか？",
            "english": "How do you read 「必要」?",
            "options": [
                "ひつよう",
                "ひっよう",
                "ひつよ",
                "ひじょう"
            ],
            "answer": "ひつよう"
        },

        {
            "category": "Kanji",
            "question": "「全部」の意味はどれですか？",
            "english": "What does 「全部」 mean?",
            "options": [
                "All / Entire",
                "Part",
                "Half",
                "Only"
            ],
            "answer": "All / Entire"
        },

        {
            "category": "Kanji",
            "question": "「始める」の意味はどれですか？",
            "english": "What does 「始める」 mean?",
            "options": [
                "To start / begin",
                "To finish",
                "To forget",
                "To return"
            ],
            "answer": "To start / begin"
        },

        # =================================================
        # GRAMMAR - 8
        # =================================================

        {
            "category": "Grammar",
            "question": "「明日、学校へ___と思います。」に入るものはどれですか？",
            "english": "What completes the sentence: 'I think I will go to school tomorrow.'?",
            "options": [
                "行こう",
                "行って",
                "行った",
                "行かない"
            ],
            "answer": "行こう"
        },

        {
            "category": "Grammar",
            "question": "「日本へ行った___があります。」に入るものはどれですか？",
            "english": "Which expression completes 'I have been to Japan'?",
            "options": [
                "こと",
                "もの",
                "ため",
                "ところ"
            ],
            "answer": "こと"
        },

        {
            "category": "Grammar",
            "question": "「宿題をし___、テレビを見ました。」に入るものはどれですか？",
            "english": "Which form means 'After doing my homework, I watched TV'?",
            "options": [
                "てから",
                "ながら",
                "たり",
                "そうに"
            ],
            "answer": "てから"
        },

        {
            "category": "Grammar",
            "question": "「雨が降った___、試合は中止です。」に入るものはどれですか？",
            "english": "Which expression means 'Because it rained, the game was canceled'?",
            "options": [
                "ので",
                "まで",
                "しか",
                "ほど"
            ],
            "answer": "ので"
        },

        {
            "category": "Grammar",
            "question": "「この本は子ども___読めます。」に入るものはどれですか？",
            "english": "Which expression means 'Children can read this book'?",
            "options": [
                "でも",
                "しか",
                "だけ",
                "ほど"
            ],
            "answer": "でも"
        },

        {
            "category": "Grammar",
            "question": "「日本語を話す___ができます。」に入るものはどれですか？",
            "english": "Which expression means 'I can speak Japanese'?",
            "options": [
                "こと",
                "もの",
                "ため",
                "ところ"
            ],
            "answer": "こと"
        },

        {
            "category": "Grammar",
            "question": "「食べ___寝るのはよくありません。」に入るものはどれですか？",
            "english": "Which form completes 'It is not good to sleep right after eating'?",
            "options": [
                "てすぐ",
                "たばかり",
                "ながら",
                "そうで"
            ],
            "answer": "てすぐ"
        },

        {
            "category": "Grammar",
            "question": "「毎日勉強すれば、上手に___と思います。」に入るものはどれですか？",
            "english": "Which expression completes 'If I study every day, I think I will improve'?",
            "options": [
                "なる",
                "なった",
                "なって",
                "ならない"
            ],
            "answer": "なる"
        },

        # =================================================
        # READING - 6
        # =================================================

        {
            "category": "Reading",
            "question": "「駅に着いたら、電話してください。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Please call me when you arrive at the station.",
                "Please go to the station and wait.",
                "Please call the station.",
                "Please leave the station."
            ],
            "answer": "Please call me when you arrive at the station."
        },

        {
            "category": "Reading",
            "question": "「今日は忙しいので、明日会いましょう。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "I am busy today, so let's meet tomorrow.",
                "I was busy yesterday, so I met today.",
                "I will be busy tomorrow, so let's meet today.",
                "I am not busy today."
            ],
            "answer": "I am busy today, so let's meet tomorrow."
        },

        {
            "category": "Reading",
            "question": "「この薬を飲んだ後で、少し休んでください。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Please rest a little after taking this medicine.",
                "Please take this medicine after resting.",
                "Please stop taking this medicine.",
                "Please buy some medicine."
            ],
            "answer": "Please rest a little after taking this medicine."
        },

        {
            "category": "Reading",
            "question": "「この店は安いし、駅から近いです。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "This shop is cheap and close to the station.",
                "This shop is expensive and far from the station.",
                "This shop is closed near the station.",
                "This shop is small but expensive."
            ],
            "answer": "This shop is cheap and close to the station."
        },

        {
            "category": "Reading",
            "question": "「来週の月曜日までにレポートを出してください。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Please submit the report by next Monday.",
                "Please write the report next month.",
                "Please read the report on Monday.",
                "Please submit the report after Monday."
            ],
            "answer": "Please submit the report by next Monday."
        },

        {
            "category": "Reading",
            "question": "「忘れないように、カレンダーに書いておきました。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "I wrote it on the calendar so I would not forget.",
                "I forgot to write it on the calendar.",
                "I bought a new calendar yesterday.",
                "I threw away the calendar."
            ],
            "answer": "I wrote it on the calendar so I would not forget."
        },

        # =================================================
        # EXPRESSIONS - 4
        # =================================================

        {
            "category": "Expressions",
            "question": "「お大事に」はどんなときに使いますか？",
            "english": "When do you use 「お大事に」?",
            "options": [
                "When someone is sick",
                "When someone arrives",
                "When someone wins",
                "When someone buys something"
            ],
            "answer": "When someone is sick"
        },

        {
            "category": "Expressions",
            "question": "「よろしくお願いします」は主にどんな意味ですか？",
            "english": "What is a common meaning of 「よろしくお願いします」?",
            "options": [
                "Please treat me well / I look forward to working with you",
                "I am hungry",
                "Good night",
                "I am sorry"
            ],
            "answer": "Please treat me well / I look forward to working with you"
        },

        {
            "category": "Expressions",
            "question": "「どういたしまして」は何と言われたときに使いますか？",
            "english": "When do you say 「どういたしまして」?",
            "options": [
                "After someone says ありがとう",
                "After someone says おはよう",
                "Before eating",
                "When leaving school"
            ],
            "answer": "After someone says ありがとう"
        },

        {
            "category": "Expressions",
            "question": "「気をつけて」はどんな意味ですか？",
            "english": "What does 「気をつけて」 mean?",
            "options": [
                "Take care / Be careful",
                "Come quickly",
                "Eat well",
                "Study harder"
            ],
            "answer": "Take care / Be careful"
        }
    ]

    # =====================================================
    # QUIZ SETTINGS
    # =====================================================

    total_questions = len(questions)

    categories = [
        "Vocabulary",
        "Kanji",
        "Grammar",
        "Reading",
        "Expressions"
    ]

    # =====================================================
    # START NEW QUIZ
    # =====================================================

    if request.method == "GET":

        # -------------------------------------------------
        # IMPORTANT:
        # Store ONLY question indexes.
        # Do NOT store the full question dictionaries
        # inside Flask's default cookie session.
        # -------------------------------------------------

        question_order = list(range(total_questions))

        random.shuffle(question_order)

        session["jlpt_n4_order"] = question_order
        session["jlpt_n4_index"] = 0
        session["jlpt_n4_score"] = 0

        session["jlpt_n4_category_scores"] = {
            category: 0
            for category in categories
        }

        # Store only the selected answer for each question.
        # Question text itself is NOT stored.
        session["jlpt_n4_answers"] = {}

        session.modified = True

        first_question = questions[
            question_order[0]
        ].copy()

        first_options = first_question[
            "options"
        ].copy()

        random.shuffle(first_options)

        first_question["options"] = first_options

        return render_template(
            "jlpt_n4.html",

            username=session.get(
                "user",
                ""
            ),

            question=first_question,

            question_number=1,

            total_questions=total_questions,

            score=0
        )

    # =====================================================
    # POST
    # =====================================================

    question_order = session.get(
        "jlpt_n4_order"
    )

    # -----------------------------------------------------
    # If quiz state is missing, restart.
    # -----------------------------------------------------

    if not question_order:

        return redirect("/jlpt/n4")

    current_index = int(
        session.get(
            "jlpt_n4_index",
            0
        )
    )

    score = int(
        session.get(
            "jlpt_n4_score",
            0
        )
    )

    category_scores = session.get(
        "jlpt_n4_category_scores"
    )

    if not category_scores:

        category_scores = {
            category: 0
            for category in categories
        }

    n4_answers = session.get(
        "jlpt_n4_answers"
    )

    if not n4_answers:

        n4_answers = {}

    # =====================================================
    # SAFETY
    # =====================================================

    if current_index < 0:

        current_index = 0

    if current_index >= total_questions:

        return redirect("/jlpt/n4")

    # =====================================================
    # CURRENT QUESTION
    # =====================================================

    question_id = question_order[
        current_index
    ]

    current_question = questions[
        question_id
    ]

    # =====================================================
    # GET ANSWER
    # =====================================================

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    correct_answer = current_question[
        "answer"
    ]

    category = current_question[
        "category"
    ]

    # =====================================================
    # SAVE ANSWER
    # =====================================================

    # Store ONLY the answer data.
    # The actual question can be reconstructed later.
    n4_answers[str(question_id)] = answer

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if answer == correct_answer:

        score += 1

        category_scores[category] = (
            category_scores.get(category, 0) + 1
        )

    # =====================================================
    # MOVE FORWARD
    # =====================================================

    current_index += 1

    # =====================================================
    # SAVE SESSION
    # =====================================================

    session["jlpt_n4_index"] = current_index
    session["jlpt_n4_score"] = score
    session["jlpt_n4_category_scores"] = category_scores
    session["jlpt_n4_answers"] = n4_answers

    session.modified = True

    # =====================================================
    # FINISHED
    # =====================================================

    if current_index >= total_questions:

        total = total_questions

        percentage = round(
            (score / total) * 100
        )

        # =================================================
        # SAVE N4 SCORE + UNLOCK NEXT LEVEL
        # =================================================

        save_jlpt_score(
            session["user_id"],
            "N4",
            percentage
        )


        # -------------------------------------------------
        # COPY category scores
        # -------------------------------------------------

        result_category_scores = (
            category_scores.copy()
        )

        # -------------------------------------------------
        # BUILD COMPLETE REVIEW
        # -------------------------------------------------

        result_review = {}

        for review_number, question_id in enumerate(
            question_order
        ):

            question_data = questions[
                question_id
            ]

            your_answer = n4_answers.get(
                str(question_id),
                ""
            )

            result_review[str(review_number)] = {

                "question":
                    question_data["question"],

                "english":
                    question_data["english"],

                "your_answer":
                    your_answer,

                "correct_answer":
                    question_data["answer"],

                "category":
                    question_data["category"]
            }

        # -------------------------------------------------
        # SAVE USERNAME BEFORE CLEARING QUIZ
        # -------------------------------------------------

        username = session.get(
            "user",
            ""
        )

        # =================================================
        # CLEAR ONLY N4 QUIZ STATE
        # =================================================

        session.pop(
            "jlpt_n4_order",
            None
        )

        session.pop(
            "jlpt_n4_index",
            None
        )

        session.pop(
            "jlpt_n4_score",
            None
        )

        session.pop(
            "jlpt_n4_category_scores",
            None
        )

        session.pop(
            "jlpt_n4_answers",
            None
        )

        session.modified = True

        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(
            "jlpt_n4_result.html",

            username=username,

            score=score,

            total=total,

            total_questions=total,

            percentage=percentage,

            category_scores=result_category_scores,

            review=result_review
        )

    # =====================================================
    # NEXT QUESTION
    # =====================================================

    next_question_id = question_order[
        current_index
    ]

    next_question = questions[
        next_question_id
    ].copy()

    # -----------------------------------------------------
    # Shuffle OPTIONS ONLY
    # -----------------------------------------------------

    next_options = next_question[
        "options"
    ].copy()

    random.shuffle(next_options)

    next_question["options"] = next_options

    # =====================================================
    # SHOW NEXT QUESTION
    # =====================================================

    return render_template(
        "jlpt_n4.html",

        username=session.get(
            "user",
            ""
        ),

        question=next_question,

        question_number=current_index + 1,

        total_questions=total_questions,

        score=score
    )


# =========================================================
# JLPT N3 PRACTICE
# 32 QUESTIONS
# =========================================================
@app.route("/jlpt/n3", methods=["GET", "POST"])
def jlpt_n3():

    if "user_id" not in session:
        return redirect("/login")

    # =====================================================
    # CHECK N3 ACCESS
    # =====================================================

    progress = get_jlpt_progress(
        session["user_id"]
    )

    if not jlpt_level_unlocked(
        "N3",
        progress
    ):
        return redirect("/jlpt")
    # =====================================================
    # 32 QUESTIONS
    # =====================================================

    questions = [

        # =================================================
        # VOCABULARY - 8
        # =================================================

        {
            "category": "Vocabulary",
            "question": "「影響」の意味はどれですか？",
            "english": "What does 「影響」 mean?",
            "options": [
                "Influence / Effect",
                "Opportunity",
                "Experience",
                "Condition"
            ],
            "answer": "Influence / Effect"
        },

        {
            "category": "Vocabulary",
            "question": "「必要」の意味はどれですか？",
            "english": "What does 「必要」 mean?",
            "options": [
                "Necessary",
                "Successful",
                "Convenient",
                "Famous"
            ],
            "answer": "Necessary"
        },

        {
            "category": "Vocabulary",
            "question": "「原因」の意味はどれですか？",
            "english": "What does 「原因」 mean?",
            "options": [
                "Cause",
                "Result",
                "Method",
                "Reasonable price"
            ],
            "answer": "Cause"
        },

        {
            "category": "Vocabulary",
            "question": "「結果」の意味はどれですか？",
            "english": "What does 「結果」 mean?",
            "options": [
                "Result",
                "Beginning",
                "Purpose",
                "Plan"
            ],
            "answer": "Result"
        },

        {
            "category": "Vocabulary",
            "question": "「確認」の意味はどれですか？",
            "english": "What does 「確認」 mean?",
            "options": [
                "Confirmation / Checking",
                "Competition",
                "Translation",
                "Invitation"
            ],
            "answer": "Confirmation / Checking"
        },

        {
            "category": "Vocabulary",
            "question": "「増加」の意味はどれですか？",
            "english": "What does 「増加」 mean?",
            "options": [
                "Increase",
                "Decrease",
                "Movement",
                "Change of place"
            ],
            "answer": "Increase"
        },

        {
            "category": "Vocabulary",
            "question": "「減少」の意味はどれですか？",
            "english": "What does 「減少」 mean?",
            "options": [
                "Decrease",
                "Increase",
                "Development",
                "Success"
            ],
            "answer": "Decrease"
        },

        {
            "category": "Vocabulary",
            "question": "「態度」の意味はどれですか？",
            "english": "What does 「態度」 mean?",
            "options": [
                "Attitude / Manner",
                "Ability",
                "Distance",
                "Schedule"
            ],
            "answer": "Attitude / Manner"
        },

        # =================================================
        # KANJI - 6
        # =================================================

        {
            "category": "Kanji",
            "question": "「経験」の「験」は何と読みますか？",
            "english": "How is 「験」 read in 「経験」?",
            "options": [
                "けん",
                "げん",
                "せん",
                "かん"
            ],
            "answer": "けん"
        },

        {
            "category": "Kanji",
            "question": "「必要」は何と読みますか？",
            "english": "How do you read 「必要」?",
            "options": [
                "ひつよう",
                "ひっよう",
                "ひじょう",
                "ひつよ"
            ],
            "answer": "ひつよう"
        },

        {
            "category": "Kanji",
            "question": "「影響」は何と読みますか？",
            "english": "How do you read 「影響」?",
            "options": [
                "えいきょう",
                "えきょう",
                "ようきょう",
                "えいしょう"
            ],
            "answer": "えいきょう"
        },

        {
            "category": "Kanji",
            "question": "「原因」の読み方はどれですか？",
            "english": "How do you read 「原因」?",
            "options": [
                "げんいん",
                "げんねん",
                "がんいん",
                "けんいん"
            ],
            "answer": "げんいん"
        },

        {
            "category": "Kanji",
            "question": "「状態」の意味はどれですか？",
            "english": "What does 「状態」 mean?",
            "options": [
                "Condition / State",
                "Reason",
                "Future",
                "Relationship"
            ],
            "answer": "Condition / State"
        },

        {
            "category": "Kanji",
            "question": "「判断」の意味はどれですか？",
            "english": "What does 「判断」 mean?",
            "options": [
                "Judgment / Decision",
                "Explanation",
                "Invitation",
                "Memory"
            ],
            "answer": "Judgment / Decision"
        },

        # =================================================
        # GRAMMAR - 8
        # =================================================

        {
            "category": "Grammar",
            "question": "「雨が降っている___、出かけます。」に入るものはどれですか？",
            "english": "Which expression means 'Although it is raining, I will go out'?",
            "options": [
                "のに",
                "ので",
                "ために",
                "ながらも"
            ],
            "answer": "のに"
        },

        {
            "category": "Grammar",
            "question": "「日本に住んでいる___、日本語がまだ上手ではありません。」に入るものはどれですか？",
            "english": "Which expression fits 'Although I live in Japan, my Japanese is still not good'?",
            "options": [
                "のに",
                "ので",
                "から",
                "ため"
            ],
            "answer": "のに"
        },

        {
            "category": "Grammar",
            "question": "「忘れない___、メモしてください。」に入るものはどれですか？",
            "english": "Which expression means 'Please take a note so that you don't forget'?",
            "options": [
                "ように",
                "ために",
                "そうに",
                "らしく"
            ],
            "answer": "ように"
        },

        {
            "category": "Grammar",
            "question": "「健康の___、毎日運動しています。」に入るものはどれですか？",
            "english": "Which expression means 'I exercise every day for my health'?",
            "options": [
                "ために",
                "ように",
                "そうに",
                "のに"
            ],
            "answer": "ために"
        },

        {
            "category": "Grammar",
            "question": "「忙しくて、昼ご飯を食べる___ありませんでした。」に入るものはどれですか？",
            "english": "Which expression means 'I was so busy that I had no time to eat lunch'?",
            "options": [
                "時間が",
                "ことが",
                "ためが",
                "ようが"
            ],
            "answer": "時間が"
        },

        {
            "category": "Grammar",
            "question": "「彼は来る___言っていました。」に入るものはどれですか？",
            "english": "Which expression means 'He said that he would come'?",
            "options": [
                "と",
                "ので",
                "のに",
                "まで"
            ],
            "answer": "と"
        },

        {
            "category": "Grammar",
            "question": "「この薬を飲めば、病気が治る___です。」に入るものはどれですか？",
            "english": "Which expression means 'If you take this medicine, you are supposed to get better'?",
            "options": [
                "はず",
                "ため",
                "よう",
                "わけ"
            ],
            "answer": "はず"
        },

        {
            "category": "Grammar",
            "question": "「田中さんは来ない___です。」に入るものはどれですか？",
            "english": "Which expression means 'Tanaka is not supposed to come'?",
            "options": [
                "はず",
                "こと",
                "ため",
                "そう"
            ],
            "answer": "はず"
        },

        # =================================================
        # READING - 6
        # =================================================

        {
            "category": "Reading",
            "question": "「この町では、最近外国人の観光客が増えている。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Recently, the number of foreign tourists in this town has increased.",
                "Foreign tourists have stopped visiting this town.",
                "The town has fewer tourists than before.",
                "Only Japanese tourists visit this town."
            ],
            "answer": "Recently, the number of foreign tourists in this town has increased."
        },

        {
            "category": "Reading",
            "question": "「仕事が終わったら、会社の近くのレストランで食事をする予定です。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "I plan to eat at a restaurant near the company after work.",
                "I already ate at the company.",
                "I plan to work at a restaurant.",
                "I will go home before finishing work."
            ],
            "answer": "I plan to eat at a restaurant near the company after work."
        },

        {
            "category": "Reading",
            "question": "「電車が遅れたため、会議に少し遅れてしまいました。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Because the train was delayed, I arrived late to the meeting.",
                "The meeting was canceled because of the train.",
                "I arrived early because the train was fast.",
                "I missed the train after the meeting."
            ],
            "answer": "Because the train was delayed, I arrived late to the meeting."
        },

        {
            "category": "Reading",
            "question": "「この商品は便利なだけでなく、値段も安い。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "This product is not only convenient but also inexpensive.",
                "This product is expensive but convenient.",
                "This product is neither convenient nor cheap.",
                "This product is cheap but difficult to use."
            ],
            "answer": "This product is not only convenient but also inexpensive."
        },

        {
            "category": "Reading",
            "question": "「健康のためには、食事だけでなく、十分な睡眠も必要です。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "For good health, sufficient sleep is necessary as well as a proper diet.",
                "Only food is important for health.",
                "Sleeping is unnecessary if you eat well.",
                "Health depends only on exercise."
            ],
            "answer": "For good health, sufficient sleep is necessary as well as a proper diet."
        },

        {
            "category": "Reading",
            "question": "「忘れ物をしないように、出かける前にもう一度確認してください。」の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "Please check once more before leaving so that you do not forget anything.",
                "Please leave without checking anything.",
                "Please check after returning home.",
                "Please buy something before leaving."
            ],
            "answer": "Please check once more before leaving so that you do not forget anything."
        },

        # =================================================
        # EXPRESSIONS - 4
        # =================================================

        {
            "category": "Expressions",
            "question": "「お世話になっております」は主にどんなときに使いますか？",
            "english": "When is 「お世話になっております」 commonly used?",
            "options": [
                "In business or polite communication with someone you have a relationship with",
                "When ordering food",
                "When saying good night to family",
                "When someone is sick"
            ],
            "answer": "In business or polite communication with someone you have a relationship with"
        },

        {
            "category": "Expressions",
            "question": "「念のため」はどんな意味ですか？",
            "english": "What does 「念のため」 mean?",
            "options": [
                "Just in case",
                "For the first time",
                "Immediately",
                "By accident"
            ],
            "answer": "Just in case"
        },

        {
            "category": "Expressions",
            "question": "「たとえば」はどんな意味ですか？",
            "english": "What does 「たとえば」 mean?",
            "options": [
                "For example",
                "However",
                "Therefore",
                "Usually"
            ],
            "answer": "For example"
        },

        {
            "category": "Expressions",
            "question": "「つまり」はどんな意味ですか？",
            "english": "What does 「つまり」 mean?",
            "options": [
                "In other words / In short",
                "Suddenly",
                "Fortunately",
                "At first"
            ],
            "answer": "In other words / In short"
        }
    ]

    # =====================================================
    # QUIZ SETTINGS
    # =====================================================

    total_questions = len(questions)

    categories = [
        "Vocabulary",
        "Kanji",
        "Grammar",
        "Reading",
        "Expressions"
    ]

    # =====================================================
    # START NEW QUIZ
    # =====================================================

    if request.method == "GET":

        # -------------------------------------------------
        # Store ONLY question indexes.
        # Do NOT store full question dictionaries.
        # -------------------------------------------------

        question_order = list(range(total_questions))

        random.shuffle(question_order)

        session["jlpt_n3_order"] = question_order
        session["jlpt_n3_index"] = 0
        session["jlpt_n3_score"] = 0

        session["jlpt_n3_category_scores"] = {
            category: 0
            for category in categories
        }

        # Store only selected answers.
        session["jlpt_n3_answers"] = {}

        session.modified = True

        first_question = questions[
            question_order[0]
        ].copy()

        first_options = first_question[
            "options"
        ].copy()

        random.shuffle(first_options)

        first_question["options"] = first_options

        return render_template(
            "jlpt_n3.html",

            username=session.get(
                "user",
                ""
            ),

            question=first_question,

            question_number=1,

            total_questions=total_questions,

            score=0
        )

    # =====================================================
    # POST
    # =====================================================

    question_order = session.get(
        "jlpt_n3_order"
    )

    # -----------------------------------------------------
    # If quiz state is missing, restart.
    # -----------------------------------------------------

    if not question_order:

        return redirect("/jlpt/n3")

    current_index = int(
        session.get(
            "jlpt_n3_index",
            0
        )
    )

    score = int(
        session.get(
            "jlpt_n3_score",
            0
        )
    )

    category_scores = session.get(
        "jlpt_n3_category_scores"
    )

    if not category_scores:

        category_scores = {
            category: 0
            for category in categories
        }

    n3_answers = session.get(
        "jlpt_n3_answers"
    )

    if not n3_answers:

        n3_answers = {}

    # =====================================================
    # SAFETY
    # =====================================================

    if current_index < 0:

        current_index = 0

    if current_index >= total_questions:

        return redirect("/jlpt/n3")

    # =====================================================
    # CURRENT QUESTION
    # =====================================================

    question_id = question_order[
        current_index
    ]

    current_question = questions[
        question_id
    ]

    # =====================================================
    # GET ANSWER
    # =====================================================

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    correct_answer = current_question[
        "answer"
    ]

    category = current_question[
        "category"
    ]

    # =====================================================
    # SAVE ANSWER
    # =====================================================

    n3_answers[str(question_id)] = answer

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if answer == correct_answer:

        score += 1

        category_scores[category] = (
            category_scores.get(category, 0) + 1
        )

    # =====================================================
    # MOVE FORWARD
    # =====================================================

    current_index += 1

    # =====================================================
    # SAVE SESSION
    # =====================================================

    session["jlpt_n3_index"] = current_index
    session["jlpt_n3_score"] = score
    session["jlpt_n3_category_scores"] = category_scores
    session["jlpt_n3_answers"] = n3_answers

    session.modified = True

    # =====================================================
    # FINISHED
    # =====================================================

    if current_index >= total_questions:

        total = total_questions

        percentage = round(
            (score / total) * 100
        )

        # =================================================
        # SAVE N3 SCORE + UNLOCK NEXT LEVEL
        # =================================================

        save_jlpt_score(
            session["user_id"],
            "N3",
            percentage
        )


        # -------------------------------------------------
        # COPY category scores
        # -------------------------------------------------

        result_category_scores = (
            category_scores.copy()
        )

        # -------------------------------------------------
        # BUILD COMPLETE REVIEW
        # -------------------------------------------------

        result_review = {}

        for review_number, question_id in enumerate(
            question_order
        ):

            question_data = questions[
                question_id
            ]

            your_answer = n3_answers.get(
                str(question_id),
                ""
            )

            result_review[str(review_number)] = {

                "question":
                    question_data["question"],

                "english":
                    question_data["english"],

                "your_answer":
                    your_answer,

                "correct_answer":
                    question_data["answer"],

                "category":
                    question_data["category"]
            }

        # -------------------------------------------------
        # SAVE USERNAME BEFORE CLEARING QUIZ
        # -------------------------------------------------

        username = session.get(
            "user",
            ""
        )

        # =================================================
        # CLEAR ONLY N3 QUIZ STATE
        # =================================================

        session.pop(
            "jlpt_n3_order",
            None
        )

        session.pop(
            "jlpt_n3_index",
            None
        )

        session.pop(
            "jlpt_n3_score",
            None
        )

        session.pop(
            "jlpt_n3_category_scores",
            None
        )

        session.pop(
            "jlpt_n3_answers",
            None
        )

        session.modified = True

        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(
            "jlpt_n3_result.html",

            username=username,

            score=score,

            total=total,

            total_questions=total,

            percentage=percentage,

            category_scores=result_category_scores,

            review=result_review
        )

    # =====================================================
    # NEXT QUESTION
    # =====================================================

    next_question_id = question_order[
        current_index
    ]

    next_question = questions[
        next_question_id
    ].copy()

    # -----------------------------------------------------
    # Shuffle OPTIONS ONLY
    # -----------------------------------------------------

    next_options = next_question[
        "options"
    ].copy()

    random.shuffle(next_options)

    next_question["options"] = next_options

    # =====================================================
    # SHOW NEXT QUESTION
    # =====================================================

    return render_template(
        "jlpt_n3.html",

        username=session.get(
            "user",
            ""
        ),

        question=next_question,

        question_number=current_index + 1,

        total_questions=total_questions,

        score=score
    )

# =========================================================
# JLPT N2 PRACTICE
# 40 QUESTIONS
# =========================================================
@app.route("/jlpt/n2", methods=["GET", "POST"])
def jlpt_n2():

    if "user_id" not in session:
        return redirect("/login")

    # =====================================================
    # CHECK N2 ACCESS
    # =====================================================

    progress = get_jlpt_progress(
        session["user_id"]
    )

    if not jlpt_level_unlocked(
        "N2",
        progress
    ):
        return redirect("/jlpt")
    # =====================================================
    # 40 QUESTIONS
    # =====================================================

    questions = [

        # =================================================
        # VOCABULARY - 10
        # =================================================

        {
            "category": "Vocabulary",
            "question": "「維持」の意味はどれですか？",
            "english": "What does 「維持」 mean?",
            "options": [
                "Maintain / Preserve",
                "Destroy",
                "Increase",
                "Compare"
            ],
            "answer": "Maintain / Preserve"
        },

        {
            "category": "Vocabulary",
            "question": "「改善」の意味はどれですか？",
            "english": "What does 「改善」 mean?",
            "options": [
                "Improvement",
                "Failure",
                "Competition",
                "Decision"
            ],
            "answer": "Improvement"
        },

        {
            "category": "Vocabulary",
            "question": "「傾向」の意味はどれですか？",
            "english": "What does 「傾向」 mean?",
            "options": [
                "Tendency / Trend",
                "Reason",
                "Result",
                "Ability"
            ],
            "answer": "Tendency / Trend"
        },

        {
            "category": "Vocabulary",
            "question": "「判断」の意味はどれですか？",
            "english": "What does 「判断」 mean?",
            "options": [
                "Judgment / Decision",
                "Explanation",
                "Invitation",
                "Memory"
            ],
            "answer": "Judgment / Decision"
        },

        {
            "category": "Vocabulary",
            "question": "「適切」の意味はどれですか？",
            "english": "What does 「適切」 mean?",
            "options": [
                "Appropriate",
                "Unusual",
                "Dangerous",
                "Temporary"
            ],
            "answer": "Appropriate"
        },

        {
            "category": "Vocabulary",
            "question": "「影響」の意味はどれですか？",
            "english": "What does 「影響」 mean?",
            "options": [
                "Influence / Effect",
                "Opportunity",
                "Condition",
                "Distance"
            ],
            "answer": "Influence / Effect"
        },

        {
            "category": "Vocabulary",
            "question": "「解決」の意味はどれですか？",
            "english": "What does 「解決」 mean?",
            "options": [
                "Solution / Resolution",
                "Continuation",
                "Confusion",
                "Preparation"
            ],
            "answer": "Solution / Resolution"
        },

        {
            "category": "Vocabulary",
            "question": "「協力」の意味はどれですか？",
            "english": "What does 「協力」 mean?",
            "options": [
                "Cooperation",
                "Opposition",
                "Competition",
                "Independence"
            ],
            "answer": "Cooperation"
        },

        {
            "category": "Vocabulary",
            "question": "「主張」の意味はどれですか？",
            "english": "What does 「主張」 mean?",
            "options": [
                "Claim / Assertion",
                "Question",
                "Permission",
                "Prediction"
            ],
            "answer": "Claim / Assertion"
        },

        {
            "category": "Vocabulary",
            "question": "「予測」の意味はどれですか？",
            "english": "What does 「予測」 mean?",
            "options": [
                "Prediction / Forecast",
                "Memory",
                "Explanation",
                "Permission"
            ],
            "answer": "Prediction / Forecast"
        },

        # =================================================
        # KANJI - 8
        # =================================================

        {
            "category": "Kanji",
            "question": "「維持」は何と読みますか？",
            "english": "How do you read 「維持」?",
            "options": [
                "いじ",
                "いち",
                "ゆじ",
                "えじ"
            ],
            "answer": "いじ"
        },

        {
            "category": "Kanji",
            "question": "「改善」は何と読みますか？",
            "english": "How do you read 「改善」?",
            "options": [
                "かいぜん",
                "かいせん",
                "がいぜん",
                "けいぜん"
            ],
            "answer": "かいぜん"
        },

        {
            "category": "Kanji",
            "question": "「傾向」は何と読みますか？",
            "english": "How do you read 「傾向」?",
            "options": [
                "けいこう",
                "けこう",
                "きょうこう",
                "けいごう"
            ],
            "answer": "けいこう"
        },

        {
            "category": "Kanji",
            "question": "「適切」の読み方はどれですか？",
            "english": "How do you read 「適切」?",
            "options": [
                "てきせつ",
                "てきぜつ",
                "できせつ",
                "ていせつ"
            ],
            "answer": "てきせつ"
        },

        {
            "category": "Kanji",
            "question": "「解決」の読み方はどれですか？",
            "english": "How do you read 「解決」?",
            "options": [
                "かいけつ",
                "かいげつ",
                "がいけつ",
                "かえけつ"
            ],
            "answer": "かいけつ"
        },

        {
            "category": "Kanji",
            "question": "「協力」の読み方はどれですか？",
            "english": "How do you read 「協力」?",
            "options": [
                "きょうりょく",
                "きょりょく",
                "きょうりき",
                "きょうろく"
            ],
            "answer": "きょうりょく"
        },

        {
            "category": "Kanji",
            "question": "「主張」の意味はどれですか？",
            "english": "What does 「主張」 mean?",
            "options": [
                "Claim / Assertion",
                "Support",
                "Agreement",
                "Research"
            ],
            "answer": "Claim / Assertion"
        },

        {
            "category": "Kanji",
            "question": "「予測」の意味はどれですか？",
            "english": "What does 「予測」 mean?",
            "options": [
                "Prediction / Forecast",
                "Past experience",
                "Explanation",
                "Instruction"
            ],
            "answer": "Prediction / Forecast"
        },

        # =================================================
        # GRAMMAR - 10
        # =================================================

        {
            "category": "Grammar",
            "question": "「この問題は専門家___難しい。」に入るものはどれですか？",
            "english": "Which expression means 'This problem is difficult even for an expert'?",
            "options": [
                "にとっても",
                "についても",
                "によっても",
                "としても"
            ],
            "answer": "にとっても"
        },

        {
            "category": "Grammar",
            "question": "「健康のために、毎日運動する___している。」に入るものはどれですか？",
            "english": "Which expression means 'I make an effort to exercise every day for my health'?",
            "options": [
                "ように",
                "ことに",
                "ために",
                "わけに"
            ],
            "answer": "ように"
        },

        {
            "category": "Grammar",
            "question": "「彼は何も知らない___、知っているような顔をしている。」に入るものはどれですか？",
            "english": "Which expression means 'Although he knows nothing, he acts as if he knows'?",
            "options": [
                "くせに",
                "ために",
                "わけで",
                "ところで"
            ],
            "answer": "くせに"
        },

        {
            "category": "Grammar",
            "question": "「忙しい___、毎日運動しています。」に入るものはどれですか？",
            "english": "Which expression means 'Despite being busy, I exercise every day'?",
            "options": [
                "ながらも",
                "ところが",
                "ばかりか",
                "わけで"
            ],
            "answer": "ながらも"
        },

        {
            "category": "Grammar",
            "question": "「この仕事は今日中に終わる___ありません。」に入るものはどれですか？",
            "english": "Which expression means 'There is no way this work will be finished today'?",
            "options": [
                "はずが",
                "わけが",
                "ことが",
                "ためが"
            ],
            "answer": "はずが"
        },

        {
            "category": "Grammar",
            "question": "「彼が来る___、私は先に帰ります。」に入るものはどれですか？",
            "english": "Which expression means 'Regardless of whether he comes, I will go home first'?",
            "options": [
                "かどうかにかかわらず",
                "ために",
                "ように",
                "ばかりに"
            ],
            "answer": "かどうかにかかわらず"
        },

        {
            "category": "Grammar",
            "question": "「雨が降った___、試合は予定通り行われた。」に入るものはどれですか？",
            "english": "Which expression means 'Even though it rained, the game was held as scheduled'?",
            "options": [
                "にもかかわらず",
                "にしたがって",
                "を通じて",
                "にともなって"
            ],
            "answer": "にもかかわらず"
        },

        {
            "category": "Grammar",
            "question": "「経験を重ねる___、仕事が上手になっていく。」に入るものはどれですか？",
            "english": "Which expression means 'As one gains experience, one becomes better at the job'?",
            "options": [
                "につれて",
                "に対して",
                "に反して",
                "において"
            ],
            "answer": "につれて"
        },

        {
            "category": "Grammar",
            "question": "「この薬は子ども___使わないでください。」に入るものはどれですか？",
            "english": "Which expression means 'Please do not use this medicine on children'?",
            "options": [
                "に対して",
                "に関して",
                "について",
                "にとって"
            ],
            "answer": "に対して"
        },

        {
            "category": "Grammar",
            "question": "「彼は忙しい___、友達の相談に乗ってくれた。」に入るものはどれですか？",
            "english": "Which expression means 'Even though he was busy, he listened to his friend's concerns'?",
            "options": [
                "にもかかわらず",
                "わけで",
                "ところを",
                "ためか"
            ],
            "answer": "にもかかわらず"
        },

        # =================================================
        # READING - 8
        # =================================================

        {
            "category": "Reading",
            "question": "「近年、インターネットを利用して買い物をする人が増えている。その理由の一つは、店に行かなくても商品を比較できることである。」この文章の内容として正しいものはどれですか？",
            "english": "Which statement is correct according to the passage?",
            "options": [
                "More people shop online because they can compare products without visiting stores.",
                "People have stopped comparing products.",
                "Online shopping requires visiting many stores.",
                "Fewer people use the internet for shopping."
            ],
            "answer": "More people shop online because they can compare products without visiting stores."
        },

        {
            "category": "Reading",
            "question": "「この会社では、社員が働きやすい環境を作るために、勤務時間を自由に選べる制度を導入した。」この文章の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "The company introduced a system allowing employees to choose their working hours.",
                "The company increased everyone's working hours.",
                "Employees can no longer choose their schedules.",
                "The company stopped improving the workplace."
            ],
            "answer": "The company introduced a system allowing employees to choose their working hours."
        },

        {
            "category": "Reading",
            "question": "「失敗したからといって、すぐにあきらめる必要はない。失敗から学ぶことで、次に成功する可能性が高くなる。」筆者の考えとして最も近いものはどれですか？",
            "english": "Which best represents the author's opinion?",
            "options": [
                "Failure can provide lessons that increase the chance of future success.",
                "People should always give up after failing.",
                "Failure has no useful meaning.",
                "Success is impossible after failure."
            ],
            "answer": "Failure can provide lessons that increase the chance of future success."
        },

        {
            "category": "Reading",
            "question": "「環境問題を解決するためには、政府だけでなく、一人一人が日常生活を見直すことも重要である。」何が重要だと言っていますか？",
            "english": "What does the passage say is important?",
            "options": [
                "Both government action and individual changes in daily life are important.",
                "Only government action is necessary.",
                "Individuals should ignore environmental problems.",
                "Environmental problems cannot be solved."
            ],
            "answer": "Both government action and individual changes in daily life are important."
        },

        {
            "category": "Reading",
            "question": "「このサービスは便利である一方、利用料金が高いという問題もある。」この文章から分かることはどれですか？",
            "english": "What can be understood from this sentence?",
            "options": [
                "The service is convenient but expensive.",
                "The service is cheap but inconvenient.",
                "The service is neither useful nor expensive.",
                "The service is free."
            ],
            "answer": "The service is convenient but expensive."
        },

        {
            "category": "Reading",
            "question": "「予定では午後3時に出発することになっていたが、交通渋滞のため、出発は30分遅れた。」何が起きましたか？",
            "english": "What happened?",
            "options": [
                "The departure was delayed by 30 minutes because of traffic.",
                "The departure happened 30 minutes early.",
                "The trip was canceled because of traffic.",
                "The destination changed."
            ],
            "answer": "The departure was delayed by 30 minutes because of traffic."
        },

        {
            "category": "Reading",
            "question": "「新しい制度を導入した結果、仕事の効率が以前より向上した。」何が起きましたか？",
            "english": "What happened after the new system was introduced?",
            "options": [
                "Work efficiency improved.",
                "Work efficiency decreased.",
                "The system was immediately canceled.",
                "Employees stopped working."
            ],
            "answer": "Work efficiency improved."
        },

        {
            "category": "Reading",
            "question": "「この調査によれば、睡眠時間が短い人ほど、日中に集中できない傾向がある。」この文章の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "People who sleep less tend to have difficulty concentrating during the day.",
                "People who sleep less always concentrate better.",
                "Sleep has no relationship with concentration.",
                "Everyone sleeps the same amount."
            ],
            "answer": "People who sleep less tend to have difficulty concentrating during the day."
        },

        # =================================================
        # EXPRESSIONS - 4
        # =================================================

        {
            "category": "Expressions",
            "question": "「おかげで」はどんな意味で使われますか？",
            "english": "What does 「おかげで」 generally express?",
            "options": [
                "Thanks to / Because of a positive factor",
                "Despite",
                "Without",
                "Instead of"
            ],
            "answer": "Thanks to / Because of a positive factor"
        },

        {
            "category": "Expressions",
            "question": "「せっかく」はどんな気持ちを表しますか？",
            "english": "What feeling does 「せっかく」 often express?",
            "options": [
                "Something was done with effort or special opportunity",
                "Complete indifference",
                "Fear of something",
                "Uncertainty"
            ],
            "answer": "Something was done with effort or special opportunity"
        },

        {
            "category": "Expressions",
            "question": "「あいにく」はどんな意味ですか？",
            "english": "What does 「あいにく」 mean?",
            "options": [
                "Unfortunately",
                "Fortunately",
                "Suddenly",
                "Exactly"
            ],
            "answer": "Unfortunately"
        },

        {
            "category": "Expressions",
            "question": "「念のため」はどんな意味ですか？",
            "english": "What does 「念のため」 mean?",
            "options": [
                "Just in case",
                "For the first time",
                "Without permission",
                "By accident"
            ],
            "answer": "Just in case"
        }
    ]

    # =====================================================
    # QUIZ SETTINGS
    # =====================================================

    total_questions = len(questions)

    categories = [
        "Vocabulary",
        "Kanji",
        "Grammar",
        "Reading",
        "Expressions"
    ]

    # =====================================================
    # START NEW QUIZ
    # =====================================================

    if request.method == "GET":

        # -------------------------------------------------
        # Store ONLY question indexes.
        # -------------------------------------------------

        question_order = list(range(total_questions))

        random.shuffle(question_order)

        session["jlpt_n2_order"] = question_order
        session["jlpt_n2_index"] = 0
        session["jlpt_n2_score"] = 0

        session["jlpt_n2_category_scores"] = {
            category: 0
            for category in categories
        }

        session["jlpt_n2_answers"] = {}

        session.modified = True

        first_question = questions[
            question_order[0]
        ].copy()

        first_options = first_question[
            "options"
        ].copy()

        random.shuffle(first_options)

        first_question["options"] = first_options

        return render_template(
            "jlpt_n2.html",

            username=session.get(
                "user",
                ""
            ),

            question=first_question,

            question_number=1,

            total_questions=total_questions,

            score=0
        )

    # =====================================================
    # POST
    # =====================================================

    question_order = session.get(
        "jlpt_n2_order"
    )

    if not question_order:

        return redirect("/jlpt/n2")

    current_index = int(
        session.get(
            "jlpt_n2_index",
            0
        )
    )

    score = int(
        session.get(
            "jlpt_n2_score",
            0
        )
    )

    category_scores = session.get(
        "jlpt_n2_category_scores"
    )

    if not category_scores:

        category_scores = {
            category: 0
            for category in categories
        }

    n2_answers = session.get(
        "jlpt_n2_answers"
    )

    if not n2_answers:

        n2_answers = {}

    # =====================================================
    # SAFETY
    # =====================================================

    if current_index < 0:

        current_index = 0

    if current_index >= total_questions:

        return redirect("/jlpt/n2")

    # =====================================================
    # CURRENT QUESTION
    # =====================================================

    question_id = question_order[
        current_index
    ]

    current_question = questions[
        question_id
    ]

    # =====================================================
    # GET ANSWER
    # =====================================================

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    correct_answer = current_question[
        "answer"
    ]

    category = current_question[
        "category"
    ]

    # =====================================================
    # SAVE ANSWER
    # =====================================================

    n2_answers[str(question_id)] = answer

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if answer == correct_answer:

        score += 1

        category_scores[category] = (
            category_scores.get(category, 0) + 1
        )

    # =====================================================
    # MOVE FORWARD
    # =====================================================

    current_index += 1

    # =====================================================
    # SAVE SESSION
    # =====================================================

    session["jlpt_n2_index"] = current_index
    session["jlpt_n2_score"] = score
    session["jlpt_n2_category_scores"] = category_scores
    session["jlpt_n2_answers"] = n2_answers

    session.modified = True

    # =====================================================
    # FINISHED
    # =====================================================

    if current_index >= total_questions:

        total = total_questions

        percentage = round(
            (score / total) * 100
        )

        # =================================================
        # SAVE N2 SCORE + UNLOCK NEXT LEVEL
        # =================================================

        save_jlpt_score(
            session["user_id"],
            "N2",
            percentage
        )


        # -------------------------------------------------
        # COPY CATEGORY SCORES
        # -------------------------------------------------

        result_category_scores = (
            category_scores.copy()
        )

        # -------------------------------------------------
        # BUILD COMPLETE REVIEW
        # -------------------------------------------------

        result_review = {}

        for review_number, question_id in enumerate(
            question_order
        ):

            question_data = questions[
                question_id
            ]

            your_answer = n2_answers.get(
                str(question_id),
                ""
            )

            result_review[str(review_number)] = {

                "question":
                    question_data["question"],

                "english":
                    question_data["english"],

                "your_answer":
                    your_answer,

                "correct_answer":
                    question_data["answer"],

                "category":
                    question_data["category"]
            }

        # -------------------------------------------------
        # SAVE USERNAME
        # -------------------------------------------------

        username = session.get(
            "user",
            ""
        )

        # =================================================
        # CLEAR ONLY N2 QUIZ STATE
        # =================================================

        session.pop(
            "jlpt_n2_order",
            None
        )

        session.pop(
            "jlpt_n2_index",
            None
        )

        session.pop(
            "jlpt_n2_score",
            None
        )

        session.pop(
            "jlpt_n2_category_scores",
            None
        )

        session.pop(
            "jlpt_n2_answers",
            None
        )

        session.modified = True

        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(
            "jlpt_n2_result.html",

            username=username,

            score=score,

            total=total,

            total_questions=total,

            percentage=percentage,

            category_scores=result_category_scores,

            review=result_review
        )

    # =====================================================
    # NEXT QUESTION
    # =====================================================

    next_question_id = question_order[
        current_index
    ]

    next_question = questions[
        next_question_id
    ].copy()

    # -----------------------------------------------------
    # Shuffle OPTIONS ONLY
    # -----------------------------------------------------

    next_options = next_question[
        "options"
    ].copy()

    random.shuffle(next_options)

    next_question["options"] = next_options

    # =====================================================
    # SHOW NEXT QUESTION
    # =====================================================

    return render_template(
        "jlpt_n2.html",

        username=session.get(
            "user",
            ""
        ),

        question=next_question,

        question_number=current_index + 1,

        total_questions=total_questions,

        score=score
    )

# =========================================================
# JLPT N1 PRACTICE
# 50 QUESTIONS
# =========================================================
@app.route("/jlpt/n1", methods=["GET", "POST"])
def jlpt_n1():

    if "user_id" not in session:
        return redirect("/login")

    # =====================================================
    # CHECK N1 ACCESS
    # =====================================================

    progress = get_jlpt_progress(
        session["user_id"]
    )

    if not jlpt_level_unlocked(
        "N1",
        progress
    ):
        return redirect("/jlpt")
    # =====================================================
    # 50 QUESTIONS
    # =====================================================

    questions = [

        # =================================================
        # VOCABULARY - 12
        # =================================================

        {
            "category": "Vocabulary",
            "question": "「曖昧」の意味はどれですか？",
            "english": "What does 「曖昧」 mean?",
            "options": [
                "Ambiguous / Vague",
                "Obvious",
                "Accurate",
                "Permanent"
            ],
            "answer": "Ambiguous / Vague"
        },

        {
            "category": "Vocabulary",
            "question": "「促進」の意味はどれですか？",
            "english": "What does 「促進」 mean?",
            "options": [
                "Promotion / Facilitation",
                "Prevention",
                "Reduction",
                "Cancellation"
            ],
            "answer": "Promotion / Facilitation"
        },

        {
            "category": "Vocabulary",
            "question": "「妥当」の意味はどれですか？",
            "english": "What does 「妥当」 mean?",
            "options": [
                "Valid / Appropriate",
                "Impossible",
                "Unclear",
                "Temporary"
            ],
            "answer": "Valid / Appropriate"
        },

        {
            "category": "Vocabulary",
            "question": "「懸念」の意味はどれですか？",
            "english": "What does 「懸念」 mean?",
            "options": [
                "Concern / Apprehension",
                "Celebration",
                "Agreement",
                "Achievement"
            ],
            "answer": "Concern / Apprehension"
        },

        {
            "category": "Vocabulary",
            "question": "「顕著」の意味はどれですか？",
            "english": "What does 「顕著」 mean?",
            "options": [
                "Remarkable / Noticeable",
                "Hidden",
                "Ordinary",
                "Uncertain"
            ],
            "answer": "Remarkable / Noticeable"
        },

        {
            "category": "Vocabulary",
            "question": "「柔軟」の意味はどれですか？",
            "english": "What does 「柔軟」 mean?",
            "options": [
                "Flexible",
                "Strict",
                "Fragile",
                "Permanent"
            ],
            "answer": "Flexible"
        },

        {
            "category": "Vocabulary",
            "question": "「概略」の意味はどれですか？",
            "english": "What does 「概略」 mean?",
            "options": [
                "Outline / Summary",
                "Detailed explanation",
                "Conclusion",
                "Prediction"
            ],
            "answer": "Outline / Summary"
        },

        {
            "category": "Vocabulary",
            "question": "「阻止」の意味はどれですか？",
            "english": "What does 「阻止」 mean?",
            "options": [
                "Prevent / Block",
                "Encourage",
                "Support",
                "Continue"
            ],
            "answer": "Prevent / Block"
        },

        {
            "category": "Vocabulary",
            "question": "「配慮」の意味はどれですか？",
            "english": "What does 「配慮」 mean?",
            "options": [
                "Consideration / Care",
                "Competition",
                "Opposition",
                "Prediction"
            ],
            "answer": "Consideration / Care"
        },

        {
            "category": "Vocabulary",
            "question": "「著しい」の意味はどれですか？",
            "english": "What does 「著しい」 mean?",
            "options": [
                "Remarkable / Significant",
                "Unimportant",
                "Hidden",
                "Ordinary"
            ],
            "answer": "Remarkable / Significant"
        },

        {
            "category": "Vocabulary",
            "question": "「緩和」の意味はどれですか？",
            "english": "What does 「緩和」 mean?",
            "options": [
                "Relaxation / Mitigation",
                "Strengthening",
                "Expansion",
                "Opposition"
            ],
            "answer": "Relaxation / Mitigation"
        },

        {
            "category": "Vocabulary",
            "question": "「一貫」の意味はどれですか？",
            "english": "What does 「一貫」 mean?",
            "options": [
                "Consistency / Coherence",
                "Confusion",
                "Interruption",
                "Variation"
            ],
            "answer": "Consistency / Coherence"
        },

        # =================================================
        # KANJI - 10
        # =================================================

        {
            "category": "Kanji",
            "question": "「曖昧」は何と読みますか？",
            "english": "How do you read 「曖昧」?",
            "options": [
                "あいまい",
                "あいばい",
                "あまい",
                "あいみ"
            ],
            "answer": "あいまい"
        },

        {
            "category": "Kanji",
            "question": "「促進」は何と読みますか？",
            "english": "How do you read 「促進」?",
            "options": [
                "そくしん",
                "そくじん",
                "ぞくしん",
                "しょくしん"
            ],
            "answer": "そくしん"
        },

        {
            "category": "Kanji",
            "question": "「妥当」は何と読みますか？",
            "english": "How do you read 「妥当」?",
            "options": [
                "だとう",
                "たとう",
                "だどう",
                "たいとう"
            ],
            "answer": "だとう"
        },

        {
            "category": "Kanji",
            "question": "「懸念」は何と読みますか？",
            "english": "How do you read 「懸念」?",
            "options": [
                "けねん",
                "けんねん",
                "けいねん",
                "かねん"
            ],
            "answer": "けねん"
        },

        {
            "category": "Kanji",
            "question": "「顕著」は何と読みますか？",
            "english": "How do you read 「顕著」?",
            "options": [
                "けんちょ",
                "げんちょ",
                "けんしょ",
                "けいちょ"
            ],
            "answer": "けんちょ"
        },

        {
            "category": "Kanji",
            "question": "「柔軟」の読み方はどれですか？",
            "english": "How do you read 「柔軟」?",
            "options": [
                "じゅうなん",
                "じゅなん",
                "にゅうなん",
                "じょうなん"
            ],
            "answer": "じゅうなん"
        },

        {
            "category": "Kanji",
            "question": "「概略」の読み方はどれですか？",
            "english": "How do you read 「概略」?",
            "options": [
                "がいりゃく",
                "かいりゃく",
                "がいりょく",
                "けいりゃく"
            ],
            "answer": "がいりゃく"
        },

        {
            "category": "Kanji",
            "question": "「阻止」の読み方はどれですか？",
            "english": "How do you read 「阻止」?",
            "options": [
                "そし",
                "そじ",
                "しょうし",
                "ぞし"
            ],
            "answer": "そし"
        },

        {
            "category": "Kanji",
            "question": "「配慮」の意味はどれですか？",
            "english": "What does 「配慮」 mean?",
            "options": [
                "Consideration",
                "Opposition",
                "Prediction",
                "Competition"
            ],
            "answer": "Consideration"
        },

        {
            "category": "Kanji",
            "question": "「緩和」の意味はどれですか？",
            "english": "What does 「緩和」 mean?",
            "options": [
                "Mitigation / Relaxation",
                "Expansion",
                "Strengthening",
                "Replacement"
            ],
            "answer": "Mitigation / Relaxation"
        },

        # =================================================
        # GRAMMAR - 12
        # =================================================

        {
            "category": "Grammar",
            "question": "「彼の説明は理解できない___ではないが、少し分かりにくい。」に入るものはどれですか？",
            "english": "Which expression means 'It is not that I cannot understand his explanation, but it is a little difficult to understand'?",
            "options": [
                "わけ",
                "ほど",
                "もの",
                "こと"
            ],
            "answer": "わけ"
        },

        {
            "category": "Grammar",
            "question": "「忙しい___、彼は最後まで仕事を手伝ってくれた。」に入るものはどれですか？",
            "english": "Which expression means 'Despite being busy, he helped with the work until the end'?",
            "options": [
                "にもかかわらず",
                "にしたがって",
                "をめぐって",
                "にともなって"
            ],
            "answer": "にもかかわらず"
        },

        {
            "category": "Grammar",
            "question": "「この問題は簡単に解決できる___。」に入るものはどれですか？",
            "english": "Which expression means 'It is not necessarily the case that this problem can be solved easily'?",
            "options": [
                "とは限らない",
                "に違いない",
                "わけがない",
                "にほかならない"
            ],
            "answer": "とは限らない"
        },

        {
            "category": "Grammar",
            "question": "「努力した___、必ず成功するとは限らない。」に入るものはどれですか？",
            "english": "Which expression means 'Even if you make an effort, it does not necessarily mean you will succeed'?",
            "options": [
                "からといって",
                "ことから",
                "ばかりに",
                "ものなら"
            ],
            "answer": "からといって"
        },

        {
            "category": "Grammar",
            "question": "「彼は何も知らない___、知っているように話している。」に入るものはどれですか？",
            "english": "Which expression means 'Although he knows nothing, he talks as if he knows everything'?",
            "options": [
                "くせに",
                "おかげで",
                "ために",
                "ものの"
            ],
            "answer": "くせに"
        },

        {
            "category": "Grammar",
            "question": "「この研究は将来の医療に大きな影響を与える___。」に入るものはどれですか？",
            "english": "Which expression means 'This research is likely to have a major influence on future medicine'?",
            "options": [
                "に違いない",
                "わけではない",
                "ことはない",
                "どころではない"
            ],
            "answer": "に違いない"
        },

        {
            "category": "Grammar",
            "question": "「彼の話を聞く___、考え方が少しずつ変わってきた。」に入るものはどれですか？",
            "english": "Which expression means 'As I listened to him, my way of thinking gradually changed'?",
            "options": [
                "につれて",
                "に先立って",
                "を問わず",
                "に反して"
            ],
            "answer": "につれて"
        },

        {
            "category": "Grammar",
            "question": "「状況___、計画を変更する必要がある。」に入るものはどれですか？",
            "english": "Which expression means 'Depending on the situation, we may need to change the plan'?",
            "options": [
                "によっては",
                "にかかわらず",
                "を通じて",
                "に先立って"
            ],
            "answer": "によっては"
        },

        {
            "category": "Grammar",
            "question": "「彼は責任者___、最後まで問題に対応した。」に入るものはどれですか？",
            "english": "Which expression means 'As the person responsible, he dealt with the problem until the end'?",
            "options": [
                "として",
                "にして",
                "に対して",
                "をめぐって"
            ],
            "answer": "として"
        },

        {
            "category": "Grammar",
            "question": "「この結果は予想___ものだった。」に入るものはどれですか？",
            "english": "Which expression means 'This result was something that could not have been predicted'?",
            "options": [
                "だにしない",
                "にすぎない",
                "とは限らない",
                "わけではない"
            ],
            "answer": "だにしない"
        },

        {
            "category": "Grammar",
            "question": "「彼は約束した___、最後まで責任を果たした。」に入るものはどれですか？",
            "english": "Which expression means 'Having promised, he fulfilled his responsibility until the end'?",
            "options": [
                "以上",
                "ほど",
                "ばかり",
                "ところ"
            ],
            "answer": "以上"
        },

        {
            "category": "Grammar",
            "question": "「そんなことを言った___、みんなに誤解されるよ。」に入るものはどれですか？",
            "english": "Which expression means 'If you say something like that, people will misunderstand you'?",
            "options": [
                "が最後",
                "ものなら",
                "ところで",
                "ばかりか"
            ],
            "answer": "が最後"
        },

        # =================================================
        # READING - 10
        # =================================================

        {
            "category": "Reading",
            "question": "「近年、働き方に対する考え方が大きく変化している。以前は会社に毎日通勤することが一般的だったが、現在では在宅勤務を選択する人も増えている。」文章の内容として正しいものはどれですか？",
            "english": "Which statement is correct according to the passage?",
            "options": [
                "More people are choosing to work from home as attitudes toward work change.",
                "Everyone still works at the office every day.",
                "Working from home has completely disappeared.",
                "People no longer care about working conditions."
            ],
            "answer": "More people are choosing to work from home as attitudes toward work change."
        },

        {
            "category": "Reading",
            "question": "「便利な技術が普及する一方で、それに頼りすぎることで自分で考える機会が減るという問題も指摘されている。」筆者が指摘している問題は何ですか？",
            "english": "What problem does the author point out?",
            "options": [
                "Overdependence on convenient technology may reduce opportunities to think independently.",
                "Technology is becoming less convenient.",
                "People have stopped using technology.",
                "Technology makes everyone think better."
            ],
            "answer": "Overdependence on convenient technology may reduce opportunities to think independently."
        },

        {
            "category": "Reading",
            "question": "「環境を守るためには、大きな制度改革だけでなく、日常生活の中で一人一人が小さな行動を積み重ねることが重要である。」筆者の主張として正しいものはどれですか？",
            "english": "Which best represents the author's claim?",
            "options": [
                "Individual everyday actions are also important for protecting the environment.",
                "Only large government reforms matter.",
                "Individuals cannot affect the environment.",
                "Environmental protection requires no changes."
            ],
            "answer": "Individual everyday actions are also important for protecting the environment."
        },

        {
            "category": "Reading",
            "question": "「新しい制度を導入した当初は反対意見も多かった。しかし、実際に運用してみると、予想以上に効果があることが分かった。」最も近い内容はどれですか？",
            "english": "Which statement is closest to the passage?",
            "options": [
                "Although many people initially opposed the system, it proved more effective than expected.",
                "Everyone supported the system from the beginning.",
                "The system failed completely.",
                "The system was never implemented."
            ],
            "answer": "Although many people initially opposed the system, it proved more effective than expected."
        },

        {
            "category": "Reading",
            "question": "「成功するためには、失敗を避けることだけを考えるのではなく、失敗から何を学ぶかを考えることが重要だ。」筆者は何が重要だと考えていますか？",
            "english": "What does the author consider important?",
            "options": [
                "Learning from failures rather than simply trying to avoid them.",
                "Never making any mistakes.",
                "Giving up after failure.",
                "Ignoring past experiences."
            ],
            "answer": "Learning from failures rather than simply trying to avoid them."
        },

        {
            "category": "Reading",
            "question": "「人口の減少にともない、地方では公共交通機関の維持が難しくなっている。そのため、地域全体で新しい交通手段を考える必要がある。」何が必要だと言っていますか？",
            "english": "What does the passage say is necessary?",
            "options": [
                "Communities need to consider new forms of transportation.",
                "Public transportation should immediately disappear.",
                "Population should move only to cities.",
                "No changes are necessary."
            ],
            "answer": "Communities need to consider new forms of transportation."
        },

        {
            "category": "Reading",
            "question": "「情報が多ければ多いほど、正しい判断ができるとは限らない。重要なのは、必要な情報を選び、その信頼性を確認することである。」文章の内容として正しいものはどれですか？",
            "english": "Which statement is correct?",
            "options": [
                "Having more information does not necessarily lead to better decisions; selecting reliable information is important.",
                "All information is equally reliable.",
                "More information always guarantees correct decisions.",
                "Information should never be checked."
            ],
            "answer": "Having more information does not necessarily lead to better decisions; selecting reliable information is important."
        },

        {
            "category": "Reading",
            "question": "「企業が利益を追求することは当然だが、それだけを優先すると、社会や環境への影響を無視することになりかねない。」筆者が問題視しているのは何ですか？",
            "english": "What does the author consider problematic?",
            "options": [
                "Prioritizing profit alone may cause companies to ignore social and environmental effects.",
                "Companies should never make profits.",
                "Environmental issues have no relation to companies.",
                "Companies should stop operating."
            ],
            "answer": "Prioritizing profit alone may cause companies to ignore social and environmental effects."
        },

        {
            "category": "Reading",
            "question": "「教育では知識を覚えることも必要だが、それをどのように活用するかを考える力も身につけなければならない。」教育について何を述べていますか？",
            "english": "What does the passage say about education?",
            "options": [
                "Education should develop both knowledge and the ability to use it.",
                "Memorizing knowledge is completely unnecessary.",
                "Only practical skills matter.",
                "Students should avoid learning knowledge."
            ],
            "answer": "Education should develop both knowledge and the ability to use it."
        },

        {
            "category": "Reading",
            "question": "「社会が変化するにつれて、これまで当然だと思われていた価値観も見直される必要がある。」この文章の意味はどれですか？",
            "english": "What does this sentence mean?",
            "options": [
                "As society changes, values that were previously taken for granted may need to be reconsidered.",
                "Social values never change.",
                "Old values must always be protected.",
                "Society should stop changing."
            ],
            "answer": "As society changes, values that were previously taken for granted may need to be reconsidered."
        },

        # =================================================
        # EXPRESSIONS - 6
        # =================================================

        {
            "category": "Expressions",
            "question": "「〜にほかならない」はどんな意味ですか？",
            "english": "What does 「〜にほかならない」 mean?",
            "options": [
                "Nothing other than / Precisely",
                "Perhaps",
                "Despite",
                "Before"
            ],
            "answer": "Nothing other than / Precisely"
        },

        {
            "category": "Expressions",
            "question": "「〜を余儀なくされる」はどんな意味ですか？",
            "english": "What does 「〜を余儀なくされる」 mean?",
            "options": [
                "Be forced to",
                "Be praised for",
                "Be allowed to",
                "Be invited to"
            ],
            "answer": "Be forced to"
        },

        {
            "category": "Expressions",
            "question": "「〜を踏まえて」はどんな意味ですか？",
            "english": "What does 「〜を踏まえて」 mean?",
            "options": [
                "Based on / Taking into consideration",
                "Without knowing",
                "Against",
                "Before seeing"
            ],
            "answer": "Based on / Taking into consideration"
        },

        {
            "category": "Expressions",
            "question": "「〜を問わず」はどんな意味ですか？",
            "english": "What does 「〜を問わず」 mean?",
            "options": [
                "Regardless of",
                "Because of",
                "Only if",
                "Instead of"
            ],
            "answer": "Regardless of"
        },

        {
            "category": "Expressions",
            "question": "「〜にかかわらず」はどんな意味ですか？",
            "english": "What does 「〜にかかわらず」 mean?",
            "options": [
                "Regardless of / Irrespective of",
                "According to",
                "Because of",
                "In addition to"
            ],
            "answer": "Regardless of / Irrespective of"
        },

        {
            "category": "Expressions",
            "question": "「〜をめぐって」はどんな意味ですか？",
            "english": "What does 「〜をめぐって」 mean?",
            "options": [
                "Concerning / Regarding",
                "Without",
                "After",
                "Instead of"
            ],
            "answer": "Concerning / Regarding"
        }
    ]

    # =====================================================
    # QUIZ SETTINGS
    # =====================================================

    total_questions = len(questions)

    categories = [
        "Vocabulary",
        "Kanji",
        "Grammar",
        "Reading",
        "Expressions"
    ]

    # =====================================================
    # START NEW QUIZ
    # =====================================================

    if request.method == "GET":

        # -------------------------------------------------
        # Store ONLY question indexes.
        # -------------------------------------------------

        question_order = list(range(total_questions))

        random.shuffle(question_order)

        session["jlpt_n1_order"] = question_order
        session["jlpt_n1_index"] = 0
        session["jlpt_n1_score"] = 0

        session["jlpt_n1_category_scores"] = {
            category: 0
            for category in categories
        }

        session["jlpt_n1_answers"] = {}

        session.modified = True

        first_question = questions[
            question_order[0]
        ].copy()

        first_options = first_question[
            "options"
        ].copy()

        random.shuffle(first_options)

        first_question["options"] = first_options

        return render_template(
            "jlpt_n1.html",

            username=session.get(
                "user",
                ""
            ),

            question=first_question,

            question_number=1,

            total_questions=total_questions,

            score=0
        )

    # =====================================================
    # POST
    # =====================================================

    question_order = session.get(
        "jlpt_n1_order"
    )

    if not question_order:

        return redirect("/jlpt/n1")

    current_index = int(
        session.get(
            "jlpt_n1_index",
            0
        )
    )

    score = int(
        session.get(
            "jlpt_n1_score",
            0
        )
    )

    category_scores = session.get(
        "jlpt_n1_category_scores"
    )

    if not category_scores:

        category_scores = {
            category: 0
            for category in categories
        }

    n1_answers = session.get(
        "jlpt_n1_answers"
    )

    if not n1_answers:

        n1_answers = {}

    # =====================================================
    # SAFETY
    # =====================================================

    if current_index < 0:

        current_index = 0

    if current_index >= total_questions:

        return redirect("/jlpt/n1")

    # =====================================================
    # CURRENT QUESTION
    # =====================================================

    question_id = question_order[
        current_index
    ]

    current_question = questions[
        question_id
    ]

    # =====================================================
    # GET ANSWER
    # =====================================================

    answer = request.form.get(
        "answer",
        ""
    ).strip()

    correct_answer = current_question[
        "answer"
    ]

    category = current_question[
        "category"
    ]

    # =====================================================
    # SAVE ANSWER
    # =====================================================

    n1_answers[str(question_id)] = answer

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if answer == correct_answer:

        score += 1

        category_scores[category] = (
            category_scores.get(category, 0) + 1
        )

    # =====================================================
    # MOVE FORWARD
    # =====================================================

    current_index += 1

    # =====================================================
    # SAVE SESSION
    # =====================================================

    session["jlpt_n1_index"] = current_index
    session["jlpt_n1_score"] = score
    session["jlpt_n1_category_scores"] = category_scores
    session["jlpt_n1_answers"] = n1_answers

    session.modified = True

    # =====================================================
    # FINISHED
    # =====================================================

    if current_index >= total_questions:

        total = total_questions

        percentage = round(
            (score / total) * 100
        )

        # =================================================
        # SAVE N1 SCORE + UNLOCK NEXT LEVEL
        # =================================================

        save_jlpt_score(
            session["user_id"],
            "N1",
            percentage
        )


        # -------------------------------------------------
        # COPY CATEGORY SCORES
        # -------------------------------------------------

        result_category_scores = (
            category_scores.copy()
        )

        # -------------------------------------------------
        # BUILD COMPLETE REVIEW
        # -------------------------------------------------

        result_review = {}

        for review_number, question_id in enumerate(
            question_order
        ):

            question_data = questions[
                question_id
            ]

            your_answer = n1_answers.get(
                str(question_id),
                ""
            )

            result_review[str(review_number)] = {

                "question":
                    question_data["question"],

                "english":
                    question_data["english"],

                "your_answer":
                    your_answer,

                "correct_answer":
                    question_data["answer"],

                "category":
                    question_data["category"]
            }

        # -------------------------------------------------
        # SAVE USERNAME
        # -------------------------------------------------

        username = session.get(
            "user",
            ""
        )

        # =================================================
        # CLEAR ONLY N1 QUIZ STATE
        # =================================================

        session.pop(
            "jlpt_n1_order",
            None
        )

        session.pop(
            "jlpt_n1_index",
            None
        )

        session.pop(
            "jlpt_n1_score",
            None
        )

        session.pop(
            "jlpt_n1_category_scores",
            None
        )

        session.pop(
            "jlpt_n1_answers",
            None
        )

        session.modified = True

        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(
            "jlpt_n1_result.html",

            username=username,

            score=score,

            total=total,

            total_questions=total,

            percentage=percentage,

            category_scores=result_category_scores,

            review=result_review
        )

    # =====================================================
    # NEXT QUESTION
    # =====================================================

    next_question_id = question_order[
        current_index
    ]

    next_question = questions[
        next_question_id
    ].copy()

    # -----------------------------------------------------
    # Shuffle OPTIONS ONLY
    # -----------------------------------------------------

    next_options = next_question[
        "options"
    ].copy()

    random.shuffle(next_options)

    next_question["options"] = next_options

    # =====================================================
    # SHOW NEXT QUESTION
    # =====================================================

    return render_template(
        "jlpt_n1.html",

        username=session.get(
            "user",
            ""
        ),

        question=next_question,

        question_number=current_index + 1,

        total_questions=total_questions,

        score=score
    )
#==========================================================
# NOTES
# =========================================================

@app.route("/notes")
def notes():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "notes.html",
        username=session["user"]
    )


# =========================================================
# NOTES BY CATEGORY
# =========================================================

@app.route("/notes/<category>")
def notes_category(category):

    if "user" not in session:
        return redirect("/login")

    allowed_categories = [
        "Hiragana",
        "Katakana",
        "Grammar",
        "Vocabulary"
    ]

    if category not in allowed_categories:
        return "Category not found!", 404

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM notes
        WHERE category = ?
        ORDER BY id
    """, (
        category,
    ))

    notes = cursor.fetchall()

    conn.close()

    return render_template(
        "category_notes.html",
        notes=notes,
        category=category,
        username=session["user"]
    )


# =========================================================
# CATEGORY LESSONS
# =========================================================

@app.route("/lessons/<category>")
def lessons(category):

    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM notes
        WHERE category = ?
        ORDER BY id
    """, (
        category,
    ))

    notes = cursor.fetchall()

    conn.close()

    return render_template(
        "category_notes.html",
        notes=notes,
        category=category,
        username=session["user"]
    )


# =========================================================
# SINGLE NOTE
# =========================================================

@app.route("/note/<int:note_id>")
def single_note(note_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get the lesson
    cursor.execute("""
        SELECT *
        FROM notes
        WHERE id = ?
    """, (
        note_id,
    ))

    note = cursor.fetchone()

    if note is None:
        conn.close()
        return "Note not found!", 404

    # Check whether this user completed this lesson
    cursor.execute("""
        SELECT completed
        FROM lesson_progress
        WHERE user_id = ?
        AND lesson_id = ?
    """, (
        session["user_id"],
        note_id
    ))

    progress = cursor.fetchone()

    # True if completed, otherwise False
    completed = (
        progress is not None
        and progress[0] == 1
    )

    conn.close()

    return render_template(
        "single_note.html",
        note=note,
        username=session["user"],
        completed=completed
    )

# =========================================================
# COMPLETE LESSON
# =========================================================

@app.route(
    "/complete_lesson/<int:lesson_id>",
    methods=["POST"]
)
def complete_lesson(lesson_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # Check current completion status
    cursor.execute("""
        SELECT completed
        FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ?
    """, (
        user_id,
        lesson_id
    ))

    progress = cursor.fetchone()

    # ==========================================
    # LESSON IS ALREADY COMPLETED → UNDO
    # ==========================================

    if progress and progress[0] == 1:

        cursor.execute("""
            UPDATE lesson_progress
            SET completed = 0,
                completed_at = NULL
            WHERE user_id = ? AND lesson_id = ?
        """, (
            user_id,
            lesson_id
        ))

        cursor.execute("""
            DELETE FROM completed_lessons
            WHERE user_id = ? AND note_id = ?
        """, (
            user_id,
            lesson_id
        ))

    # ==========================================
    # LESSON IS NOT COMPLETED → MARK COMPLETED
    # ==========================================

    else:

        cursor.execute("""
            INSERT INTO lesson_progress
            (
                user_id,
                lesson_id,
                completed,
                completed_at
            )
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id, lesson_id)
            DO UPDATE SET
                completed = 1,
                completed_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            lesson_id
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO completed_lessons
            (
                user_id,
                note_id
            )
            VALUES (?, ?)
        """, (
            user_id,
            lesson_id
        ))

        # ==========================================
        # CREATE LESSON COMPLETED NOTIFICATION
        # ==========================================

        cursor.execute("""
            SELECT title
            FROM notes
            WHERE id = ?
        """, (lesson_id,))

        lesson = cursor.fetchone()

        if lesson:
            cursor.execute("""
                INSERT INTO notifications
                (
                    user_id,
                    title,
                    message,
                    notification_type
                )
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                "Lesson Completed",
                f"You completed the lesson: {lesson['title']}",
                "lesson"
            ))

        # ==========================================
        # CHECK IF CATEGORY IS NOW COMPLETE
        # ==========================================

        cursor.execute("""
            SELECT category
            FROM notes
            WHERE id = ?
        """, (lesson_id,))

        category_row = cursor.fetchone()

        if category_row:

            category = category_row["category"]

            cursor.execute("""
                SELECT COUNT(*)
                FROM notes
                WHERE category = ?
            """, (category,))

            total_lessons = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM lesson_progress lp
                JOIN notes n
                    ON lp.lesson_id = n.id
                WHERE lp.user_id = ?
                  AND n.category = ?
                  AND lp.completed = 1
            """, (
                user_id,
                category
            ))

            completed_lessons = cursor.fetchone()[0]

            if (
                total_lessons > 0
                and completed_lessons == total_lessons
            ):

                cursor.execute("""
                    SELECT id
                    FROM notifications
                    WHERE user_id = ?
                      AND notification_type = 'certificate'
                      AND message = ?
                    LIMIT 1
                """, (
                    user_id,
                    f"Your {category} certificate is now available!"
                ))

                certificate_notification = cursor.fetchone()

                if not certificate_notification:

                    cursor.execute("""
                        INSERT INTO notifications
                        (
                            user_id,
                            title,
                            message,
                            notification_type
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        user_id,
                        "Certificate Unlocked",
                        f"Your {category} certificate is now available!",
                        "certificate"
                    ))

    # ==========================================
    # SAVE ALL CHANGES
    # ==========================================

    conn.commit()
    conn.close()

    return redirect(
        f"/note/{lesson_id}"
    )
    # =========================================================
# JLPT DEMO SETTINGS
# =========================================================

@app.route("/settings/jlpt-demo", methods=["POST"])
def settings_jlpt_demo():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    if session.get("email", "").strip().lower() != DEMO_JLPT_EMAIL.lower():
        return jsonify({
            "success": False,
            "message": "Demo access is not available for this account."
        }), 403

    data = request.get_json(silent=True) or {}

    entered_key = data.get("key", "").strip()

    if entered_key != JLPT_DEMO_KEY:
        return jsonify({
            "success": False,
            "message": "Invalid unlock key."
        })

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jlpt_progress
        (
            user_id,
            highest_unlocked_level,
            demo_unlocked
        )
        VALUES (?, 'N5', 0)
    """, (session["user_id"],))

    cursor.execute("""
        UPDATE jlpt_progress
        SET
            demo_unlocked = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "JLPT Demo Mode unlocked."
    })


@app.route("/settings/jlpt-demo/lock", methods=["POST"])
def settings_jlpt_demo_lock():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    if session.get("email", "").strip().lower() != DEMO_JLPT_EMAIL.lower():
        return jsonify({
            "success": False,
            "message": "Demo access is not available for this account."
        }), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jlpt_progress
        (
            user_id,
            highest_unlocked_level,
            demo_unlocked
        )
        VALUES (?, 'N5', 0)
    """, (session["user_id"],))

    cursor.execute("""
        UPDATE jlpt_progress
        SET
            demo_unlocked = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (session["user_id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "JLPT Demo Mode locked."
    })
# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jlpt_progress
        (
            user_id,
            highest_unlocked_level,
            demo_unlocked
        )
        VALUES (?, 'N5', 0)
    """, (session["user_id"],))

    conn.commit()

    cursor.execute("""
        SELECT demo_unlocked
        FROM jlpt_progress
        WHERE user_id = ?
    """, (session["user_id"],))

    progress = cursor.fetchone()

    conn.close()

    demo_unlocked = progress["demo_unlocked"] if progress else 0

    return render_template(
        "settings.html",
        username=session["user"],
        demo_unlocked=demo_unlocked
    )
# =========================================================
# SAVE SETTINGS
# =========================================================

@app.route("/save_settings", methods=["POST"])
def save_settings():

    if "user_id" not in session:
        return {
            "success": False,
            "message": "Not logged in"
        }, 401

    data = request.get_json()

    theme = data.get("theme", "light")

    pronunciation = (
        1 if data.get("pronunciation") else 0
    )

    english_display = (
        1 if data.get("english_display") else 0
    )

    notifications = (
        1 if data.get("notifications") else 0
    )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_settings
        (
            user_id,
            theme,
            pronunciation,
            english_display,
            notifications
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            theme = excluded.theme,
            pronunciation = excluded.pronunciation,
            english_display = excluded.english_display,
            notifications = excluded.notifications
    """, (
        session["user_id"],
        theme,
        pronunciation,
        english_display,
        notifications
    ))

    conn.commit()
    conn.close()

    return {
        "success": True
    }
# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, email, dob
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    ))

    user = cursor.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )

# =========================================================
# EDIT PROFILE
# =========================================================

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    # User must be logged in
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Get current logged-in user's information
    cursor.execute("""
        SELECT id, name, email, dob
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    ))

    user = cursor.fetchone()

    # User not found
    if not user:
        conn.close()
        return redirect("/settings")

    # =====================================================
    # SAVE CHANGES
    # =====================================================

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        dob = request.form.get("dob", "").strip()

        # Validate
        if not name or not email or not dob:

            conn.close()

            return render_template(
                "edit_profile.html",
                user=user,
                error="Please fill in all fields."
            )


        # Check whether another user already uses this email
        cursor.execute("""
            SELECT id
            FROM users
            WHERE email = ?
            AND id != ?
        """, (
            email,
            session["user_id"]
        ))

        existing_user = cursor.fetchone()


        if existing_user:

            conn.close()

            return render_template(
                "edit_profile.html",
                user=user,
                error="That email address is already in use."
            )


        # Update database
        cursor.execute("""
            UPDATE users
            SET name = ?,
                email = ?,
                dob = ?
            WHERE id = ?
        """, (
            name,
            email,
            dob,
            session["user_id"]
        ))


        conn.commit()
        conn.close()


        # Update session values
        session["user"] = name
        session["email"] = email


        # Return to profile after saving
        return redirect("/profile")


    # =====================================================
    # SHOW EDIT PAGE
    # =====================================================

    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )
# =========================================================
# CHANGE PASSWORD
# =========================================================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not current_password
            or not new_password
            or not confirm_password
        ):
            return render_template(
                "change_password.html",
                error="Please fill in all fields."
            )

        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT password
            FROM users
            WHERE id = ?
        """, (
            session["user_id"],
        ))

        user = cursor.fetchone()

        if not user:
            conn.close()

            return redirect("/login")

        stored_password = user["password"]

        try:

            password_valid = check_password_hash(
                stored_password,
                current_password
            )

        except (ValueError, TypeError):

            password_valid = False

        if not password_valid:
            conn.close()

            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        new_password_hash = generate_password_hash(
            new_password
        )

        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (
            new_password_hash,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return render_template(
            "change_password.html",
            success="Password changed successfully."
        )

    return render_template(
        "change_password.html"
    )
# =========================================================
# =========================================================
# JLPT QUIZ SYSTEM
# =========================================================
# =========================================================


# =========================================================
# EXTRACT JAPANESE / ENGLISH PAIRS
# =========================================================

def extract_pairs(content):

    pairs = []

    lines = content.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if "=" not in line:
            continue

        parts = [
            p.strip()
            for p in line.split("=")
        ]

        if len(parts) < 2:
            continue

        japanese = parts[0]
        middle = parts[1]
        english = parts[-1]

        if not japanese or not english:
            continue

        if len(japanese) > 30:
            continue

        if len(english) > 80:
            continue

        if re.search(
            r"[\u3040-\u30ff\u3400-\u9fff]",
            japanese
        ):

            pairs.append({
                "japanese": japanese,
                "reading": middle,
                "meaning": english
            })

    return pairs


# =========================================================
# EXTRACT JAPANESE WORDS
# =========================================================

def extract_japanese_words(content):

    words = []

    pairs = extract_pairs(content)

    for pair in pairs:

        word = pair["japanese"]

        if word not in words:
            words.append(word)

    return words


# =========================================================
# EXTRACT ENGLISH MEANINGS
# =========================================================

def extract_meanings(content):

    meanings = []

    pairs = extract_pairs(content)

    for pair in pairs:

        meaning = pair["meaning"]

        if meaning not in meanings:
            meanings.append(meaning)

    return meanings


# =========================================================
# MAKE OPTIONS
#
# IMPORTANT:
# THIS FUNCTION NEVER RETURNS MORE THAN 4 OPTIONS
# =========================================================

def make_options(correct, wrong_answers, amount=4):

    amount = min(int(amount), 4)

    options = []

    # Correct answer first
    if correct:
        options.append(correct)

    # Add wrong answers
    for answer in wrong_answers:

        if not answer:
            continue

        if answer == correct:
            continue

        if answer in options:
            continue

        options.append(answer)

        if len(options) >= amount:
            break

    # If there are somehow too few options,
    # we simply return what is available.
    random.shuffle(options)

    return options[:4]


# =========================================================
# GENERATE QUESTIONS FOR ONE LESSON
# =========================================================

def generate_lesson_questions(lesson):

    lesson_id = str(lesson["id"])
    category = lesson["category"]
    content = lesson["content"]

    pairs = extract_pairs(content)

    questions = []

    # =====================================================
    # CLEAN VOCABULARY
    # =====================================================

    vocabulary = []

    for pair in pairs:

        japanese = str(
            pair.get("japanese", "")
        ).strip()

        reading = str(
            pair.get("reading", "")
        ).strip()

        meaning = str(
            pair.get("meaning", "")
        ).strip()

        item = (
            japanese,
            reading,
            meaning
        )

        if (
            japanese
            and reading
            and meaning
            and item not in vocabulary
        ):
            vocabulary.append(item)

    # =====================================================
    # QUESTION ID COUNTER
    # =====================================================

    question_number = 1

    # =====================================================
    # HELPER: ADD QUESTION
    # =====================================================

    def add_question(
        question_type,
        question_text,
        answer,
        options
    ):

        nonlocal question_number

        # -------------------------------------------------
        # Remove duplicate options
        # -------------------------------------------------

        clean_options = []

        for option in options:

            option = str(option).strip()

            if (
                option
                and option not in clean_options
            ):
                clean_options.append(option)

        # -------------------------------------------------
        # Make sure correct answer exists
        # -------------------------------------------------

        if answer not in clean_options:
            clean_options.insert(
                0,
                answer
            )

        # -------------------------------------------------
        # We need exactly 4 options
        # -------------------------------------------------

        if len(clean_options) < 4:
            return

        clean_options = clean_options[:4]

        # -------------------------------------------------
        # SHUFFLE ANSWER POSITIONS
        # -------------------------------------------------

        random.shuffle(
            clean_options
        )

        questions.append({
            "id": f"{lesson_id}_q{question_number}",
            "type": question_type,
            "question": question_text,
            "question_en": question_text,
            "answer": answer,
            "options": clean_options
        })

        question_number += 1

    # =====================================================
    # BUILD WRONG ANSWER POOLS FROM THIS LESSON
    # =====================================================

    meanings = [
        item[2]
        for item in vocabulary
    ]

    readings = [
        item[1]
        for item in vocabulary
    ]

    japanese_words = [
        item[0]
        for item in vocabulary
    ]

    # =====================================================
    # VOCABULARY QUESTIONS
    # =====================================================

    if vocabulary:

        # -------------------------------------------------
        # Generate multiple question styles for every word
        # -------------------------------------------------

        for index, item in enumerate(vocabulary):

            japanese, reading, meaning = item

            wrong_meanings = [
                value
                for value in meanings
                if value != meaning
            ]

            wrong_readings = [
                value
                for value in readings
                if value != reading
            ]

            wrong_japanese = [
                value
                for value in japanese_words
                if value != japanese
            ]

            # =================================================
            # JAPANESE -> ENGLISH
            # =================================================

            if len(wrong_meanings) >= 3:

                add_question(
                    "vocabulary",
                    f'What does 「{japanese}」 mean?',
                    meaning,
                    [meaning] + wrong_meanings
                )

            # =================================================
            # JAPANESE -> READING
            # =================================================

            if len(wrong_readings) >= 3:

                add_question(
                    "reading",
                    f'How do you read 「{japanese}」?',
                    reading,
                    [reading] + wrong_readings
                )

            # =================================================
            # ENGLISH -> JAPANESE
            # =================================================

            if len(wrong_japanese) >= 3:

                add_question(
                    "vocabulary",
                    f'Which Japanese word means "{meaning}"?',
                    japanese,
                    [japanese] + wrong_japanese
                )

            # =================================================
            # ENGLISH -> READING
            # =================================================

            if len(wrong_readings) >= 3:

                add_question(
                    "reading",
                    f'What is the correct reading for "{meaning}"?',
                    reading,
                    [reading] + wrong_readings
                )

            # =================================================
            # READING -> JAPANESE
            # =================================================

            if len(wrong_japanese) >= 3:

                add_question(
                    "reading_word",
                    f'Which Japanese word is read "{reading}"?',
                    japanese,
                    [japanese] + wrong_japanese
                )

            # =================================================
            # JAPANESE -> ENGLISH VARIATION
            # =================================================

            if len(wrong_meanings) >= 3:

                add_question(
                    "vocabulary",
                    f'Choose the correct meaning of 「{japanese}」.',
                    meaning,
                    [meaning] + wrong_meanings
                )

            # =================================================
            # READING CHECK VARIATION
            # =================================================

            if len(wrong_readings) >= 3:

                add_question(
                    "reading",
                    f'Choose the correct reading of 「{japanese}」.',
                    reading,
                    [reading] + wrong_readings
                )

            # =================================================
            # ENGLISH -> JAPANESE VARIATION
            # =================================================

            if len(wrong_japanese) >= 3:

                add_question(
                    "vocabulary",
                    f'Choose the Japanese word for "{meaning}".',
                    japanese,
                    [japanese] + wrong_japanese
                )

    # =====================================================
    # GRAMMAR QUESTIONS
    # =====================================================

    if category == "Grammar":

        if "は" in content:

            grammar_questions = [
                (
                    "「わたし___学生です。」に入る助詞はどれですか？",
                    "は",
                    ["は", "を", "に", "で"]
                ),
                (
                    "「これは本___です。」に入る助詞はどれですか？",
                    "は",
                    ["は", "を", "に", "で"]
                ),
                (
                    "「わたしは学生です。」で「は」は何ですか？",
                    "助詞",
                    ["助詞", "動詞", "形容詞", "名詞"]
                )
            ]

            for (
                question_text,
                answer,
                options
            ) in grammar_questions:

                add_question(
                    "grammar",
                    question_text,
                    answer,
                    options
                )

        if "です" in content:

            grammar_questions = [
                (
                    "「です」はこの文で何を表しますか？",
                    "is / am / are",
                    [
                        "is / am / are",
                        "past tense",
                        "negative",
                        "question only"
                    ]
                ),
                (
                    "「です」の基本的な役割はどれですか？",
                    "polite sentence ending",
                    [
                        "polite sentence ending",
                        "plural marker",
                        "past tense marker",
                        "object marker"
                    ]
                ),
                (
                    "「学生です」の意味に最も近いものはどれですか？",
                    "is a student",
                    [
                        "is a student",
                        "was a student",
                        "is not a student",
                        "will become a student"
                    ]
                )
            ]

            for (
                question_text,
                answer,
                options
            ) in grammar_questions:

                add_question(
                    "grammar",
                    question_text,
                    answer,
                    options
                )

    # =====================================================
    # HIRAGANA
    # =====================================================

    if category == "Hiragana":

        hiragana = [
            ("あ", "A"),
            ("い", "I"),
            ("う", "U"),
            ("え", "E"),
            ("お", "O"),
            ("か", "KA"),
            ("き", "KI"),
            ("く", "KU"),
            ("け", "KE"),
            ("こ", "KO"),
            ("さ", "SA"),
            ("し", "SHI"),
            ("す", "SU"),
            ("せ", "SE"),
            ("そ", "SO"),
            ("た", "TA"),
            ("ち", "CHI"),
            ("つ", "TSU"),
            ("て", "TE"),
            ("と", "TO")
        ]

        relevant = [
            item
            for item in hiragana
            if item[0] in content
        ]

        if len(relevant) >= 4:

            for kana, reading in relevant:

                wrong = [
                    value
                    for key, value in relevant
                    if value != reading
                ]

                if len(wrong) >= 3:

                    add_question(
                        "kana",
                        f'「{kana}」の読み方はどれですか？',
                        reading,
                        [reading] + wrong
                    )

                if len(questions) >= 20:
                    break

    # =====================================================
    # KATAKANA
    # =====================================================

    if category == "Katakana":

        katakana = [
            ("ア", "A"),
            ("イ", "I"),
            ("ウ", "U"),
            ("エ", "E"),
            ("オ", "O"),
            ("カ", "KA"),
            ("キ", "KI"),
            ("ク", "KU"),
            ("ケ", "KE"),
            ("コ", "KO"),
            ("サ", "SA"),
            ("シ", "SHI"),
            ("ス", "SU"),
            ("セ", "SE"),
            ("ソ", "SO"),
            ("タ", "TA"),
            ("チ", "CHI"),
            ("ツ", "TSU"),
            ("テ", "TE"),
            ("ト", "TO")
        ]

        relevant = [
            item
            for item in katakana
            if item[0] in content
        ]

        if len(relevant) >= 4:

            for kana, reading in relevant:

                wrong = [
                    value
                    for key, value in relevant
                    if value != reading
                ]

                if len(wrong) >= 3:

                    add_question(
                        "kana",
                        f'「{kana}」の読み方はどれですか？',
                        reading,
                        [reading] + wrong
                    )

                if len(questions) >= 20:
                    break

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_questions = []
    seen = set()

    for question in questions:

        key = (
            question["question"],
            question["answer"]
        )

        if key not in seen:

            seen.add(key)

            unique_questions.append(
                question
            )

    # =====================================================
    # SHUFFLE QUESTION ORDER
    # =====================================================

    random.shuffle(
        unique_questions
    )

    # =====================================================
    # RETURN ALL GENERATED QUESTIONS
    #
    # DO NOT LIMIT TO 10 ANYMORE
    # =====================================================

    return unique_questions
# =========================================================
# QUIZ SELECTION
# =========================================================

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            notes.id,
            notes.category,
            notes.title,
            notes.content
        FROM notes
        INNER JOIN lesson_progress
            ON notes.id = lesson_progress.lesson_id
        WHERE lesson_progress.user_id = ?
        AND lesson_progress.completed = 1
        ORDER BY notes.id
    """, (
        user_id,
    ))

    completed_lessons = cursor.fetchall()

    conn.close()

    if not completed_lessons:

        return render_template(
            "quiz_select.html",
            completed_lessons=[],
            username=session["user"]
        )

    # =====================================================
    # START QUIZ
    # =====================================================

    if request.method == "POST":

        quiz_type = request.form.get(
            "quiz_type"
        )

        lesson_id = request.form.get(
            "lesson_id"
        )

        if quiz_type == "lesson":

            if not lesson_id:
                return redirect("/quiz")

            session["quiz_lesson_id"] = int(
                lesson_id
            )

        elif quiz_type == "all":

            session["quiz_lesson_id"] = "all"

        else:

            return redirect("/quiz")

        # RESET QUIZ
        session["quiz_index"] = 0
        session["quiz_score"] = 0

        # New attempt
        session["quiz_attempt"] = (
            session.get("quiz_attempt", 0) + 1
        )

        # Remove old questions
        session.pop(
            "quiz_questions",
            None
        )

        return redirect(
            "/quiz/questions"
        )

    return render_template(
        "quiz_select.html",
        completed_lessons=completed_lessons,
        username=session["user"]
    )

# =========================================================
# QUIZ QUESTIONS
# =========================================================

@app.route(
    "/quiz/questions",
    methods=["GET", "POST"]
)
def quiz_questions():

    if "user_id" not in session:
        return redirect("/login")

    if "quiz_lesson_id" not in session:
        return redirect("/quiz")

    user_id = session["user_id"]

    quiz_lesson_id = session[
        "quiz_lesson_id"
    ]

    quiz_index = session.get(
        "quiz_index",
        0
    )

    quiz_score = session.get(
        "quiz_score",
        0
    )

    quiz_attempt = session.get(
        "quiz_attempt",
        1
    )

    # =====================================================
    # GENERATE QUESTIONS ONLY ONCE
    # =====================================================

    if "quiz_questions" not in session:

        conn = get_db()
        cursor = conn.cursor()

        # -------------------------------------------------
        # GET COMPLETED LESSONS
        # -------------------------------------------------

        if quiz_lesson_id == "all":

            cursor.execute("""
                SELECT
                    notes.id,
                    notes.category,
                    notes.title,
                    notes.content
                FROM notes
                INNER JOIN lesson_progress
                    ON notes.id = lesson_progress.lesson_id
                WHERE lesson_progress.user_id = ?
                AND lesson_progress.completed = 1
                ORDER BY notes.id
            """, (
                user_id,
            ))

        else:

            cursor.execute("""
                SELECT
                    notes.id,
                    notes.category,
                    notes.title,
                    notes.content
                FROM notes
                INNER JOIN lesson_progress
                    ON notes.id = lesson_progress.lesson_id
                WHERE lesson_progress.user_id = ?
                AND lesson_progress.completed = 1
                AND notes.id = ?
            """, (
                user_id,
                quiz_lesson_id
            ))

        lessons = cursor.fetchall()

        conn.close()

        # =================================================
        # GENERATE QUESTIONS
        # =================================================

        all_questions = []

        for lesson in lessons:

            lesson_questions = (
                generate_lesson_questions(
                    lesson
                )
            )

            all_questions.extend(
                lesson_questions
            )

        # =================================================
        # REMOVE DUPLICATE QUESTIONS
        # =================================================

        unique_questions = []

        seen_questions = set()

        for question in all_questions:

            key = (
                question.get("question", ""),
                question.get("answer", "")
            )

            if key not in seen_questions:

                seen_questions.add(key)

                unique_questions.append(
                    question
                )

        # =================================================
        # SHUFFLE QUESTION ORDER
        # =================================================

        random.shuffle(
            unique_questions
        )

        # =================================================
        # DETERMINE QUIZ SIZE
        # =================================================

        completed_count = len(
            lessons
        )

        if completed_count >= 6:

            target_questions = random.randint(
                40,
                50
            )

        else:

            target_questions = 20

        # =================================================
        # IF ENOUGH QUESTIONS EXIST
        # =================================================

        if len(unique_questions) >= target_questions:

            selected_questions = (
                unique_questions[
                    :target_questions
                ]
            )

        else:

            # -------------------------------------------------
            # We need at least 20 questions.
            #
            # If the lessons do not contain enough unique
            # questions, reuse questions while making sure
            # their option positions are shuffled.
            # -------------------------------------------------

            selected_questions = []

            question_pool = list(
                unique_questions
            )

            if question_pool:

                while (
                    len(selected_questions)
                    < target_questions
                ):

                    available = list(
                        question_pool
                    )

                    random.shuffle(
                        available
                    )

                    for question in available:

                        if (
                            len(selected_questions)
                            >= target_questions
                        ):
                            break

                        copied_question = dict(
                            question
                        )

                        copied_question[
                            "options"
                        ] = list(
                            question.get(
                                "options",
                                []
                            )
                        )

                        # -------------------------------------------------
                        # SHUFFLE ANSWER OPTIONS
                        # -------------------------------------------------

                        random.shuffle(
                            copied_question[
                                "options"
                            ]
                        )

                        selected_questions.append(
                            copied_question
                        )

            else:

                selected_questions = []

        # =================================================
        # FINAL OPTION SHUFFLE
        # =================================================

        for question in selected_questions:

            options = list(
                question.get(
                    "options",
                    []
                )
            )

            # Remove duplicate options

            options = list(
                dict.fromkeys(
                    options
                )
            )

            # Keep maximum four options

            options = options[:4]

            # Shuffle positions

            random.shuffle(
                options
            )

            question["options"] = options

        # =================================================
        # FINAL QUESTION SHUFFLE
        # =================================================

        random.shuffle(
            selected_questions
        )

        # =================================================
        # SAVE QUESTIONS
        # =================================================

        session[
            "quiz_questions"
        ] = selected_questions

    # =====================================================
    # GET QUESTIONS
    # =====================================================

    questions = session.get(
        "quiz_questions",
        []
    )

    # =====================================================
    # NO QUESTIONS
    # =====================================================

    if not questions:

        session.pop(
            "quiz_questions",
            None
        )

        session.pop(
            "quiz_lesson_id",
            None
        )

        return """
        <h2>No quiz questions available.</h2>
        <a href="/quiz">Back to Quiz</a>
        """

    # =====================================================
    # QUIZ FINISHED
    # =====================================================

    if quiz_index >= len(questions):

        total_questions = len(
            questions
        )

        percentage = 0

        if total_questions > 0:

            percentage = round(
                (
                    quiz_score
                    / total_questions
                ) * 100
            )

        # -------------------------------------------------
        # CLEAR QUIZ DATA
        # -------------------------------------------------

        session.pop(
            "quiz_questions",
            None
        )

        session.pop(
            "quiz_lesson_id",
            None
        )

        session.pop(
            "quiz_index",
            None
        )

        session.pop(
            "quiz_score",
            None
        )

        return render_template(
            "quiz_result.html",
            username=session["user"],
            score=quiz_score,
            total=total_questions,
            percentage=percentage
        )

    # =====================================================
    # CHECK ANSWER
    # =====================================================

    if request.method == "POST":

        selected_answer = request.form.get(
            "answer",
            ""
        )

        current_question = questions[
            quiz_index
        ]

        is_correct = (
            selected_answer
            == current_question["answer"]
        )

        if is_correct:

            quiz_score += 1

            session[
                "quiz_score"
            ] = quiz_score

        # =================================================
        # SAVE QUIZ HISTORY
        # =================================================

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO quiz_history
            (
                user_id,
                question_id,
                quiz_attempt,
                selected_answer,
                correct_answer,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            current_question["id"],
            quiz_attempt,
            selected_answer,
            current_question["answer"],
            1 if is_correct else 0
        ))

        conn.commit()
        conn.close()

        # =================================================
        # NEXT QUESTION
        # =================================================

        session[
            "quiz_index"
        ] = quiz_index + 1

        return redirect(
            "/quiz/questions"
        )

    # =====================================================
    # SHOW CURRENT QUESTION
    # =====================================================

    current_question = questions[
        quiz_index
    ]

    return render_template(
        "quiz_questions.html",
        username=session["user"],
        question=current_question,
        question_number=quiz_index + 1,
        total_questions=len(questions),
        score=quiz_score
    )
# =========================================================
# QUIZ HISTORY
# =========================================================
@app.route("/quiz/history")
@app.route("/quiz_history")
def quiz_history():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            quiz_attempt,
            question_id,
            selected_answer,
            correct_answer,
            is_correct,
            created_at
        FROM quiz_history
        WHERE user_id = ?
        ORDER BY quiz_attempt DESC, id ASC
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    # =====================================================
    # GROUP QUESTIONS BY QUIZ ATTEMPT
    # =====================================================

    attempts = {}

    for row in rows:

        attempt_number = row["quiz_attempt"]

        if attempt_number not in attempts:

            attempts[attempt_number] = {
                "attempt": attempt_number,
                "questions": [],
                "score": 0,
                "total": 0,
                "date": row["created_at"]
            }

        attempts[attempt_number]["questions"].append({
            "question_id": row["question_id"],
            "selected_answer": row["selected_answer"],
            "correct_answer": row["correct_answer"],
            "is_correct": row["is_correct"],
            "created_at": row["created_at"]
        })

        attempts[attempt_number]["total"] += 1

        if row["is_correct"]:
            attempts[attempt_number]["score"] += 1

    # =====================================================
    # CALCULATE PERCENTAGE
    # =====================================================

    history = []

    for attempt in attempts.values():

        if attempt["total"] > 0:

            attempt["percentage"] = round(
                (
                    attempt["score"]
                    / attempt["total"]
                ) * 100
            )

        else:

            attempt["percentage"] = 0

        history.append(attempt)

    # =====================================================
    # SORT NEWEST ATTEMPT FIRST
    # =====================================================

    history.sort(
        key=lambda x: x["attempt"],
        reverse=True
    )

    return render_template(
        "quiz_history.html",
        history=history,
        username=session["user"]
    )
# =========================================================
# STUDENT PROGRESS / STATISTICS
# =========================================================

@app.route("/progress")
def progress():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Completed lessons
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM lesson_progress
        WHERE user_id = ?
        AND completed = 1
    """, (
        user_id,
    ))

    completed_lessons = (
        cursor.fetchone()[0]
    )
    total_lessons = cursor.execute("""
    SELECT COUNT(*)
    FROM notes
    """).fetchone()[0]

    lesson_progress_percent = 0
    if total_lessons > 0:
        lesson_progress_percent = round(
        (completed_lessons / total_lessons) * 100
      )

    # -----------------------------------------------------
    # Quiz attempts
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(DISTINCT quiz_attempt)
        FROM quiz_history
        WHERE user_id = ?
    """, (
        user_id,
    ))

    quiz_attempts = (
        cursor.fetchone()[0]
    )

    # -----------------------------------------------------
    # Correct answers
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM quiz_history
        WHERE user_id = ?
        AND is_correct = 1
    """, (
        user_id,
    ))

    correct_answers = (
        cursor.fetchone()[0]
    )

    # -----------------------------------------------------
    # Total answers
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM quiz_history
        WHERE user_id = ?
    """, (
        user_id,
    ))

    total_answers = (
        cursor.fetchone()[0]
    )

    # -----------------------------------------------------
    # Wrong answers
    # -----------------------------------------------------

    wrong_answers = (
        total_answers
        - correct_answers
    )

    # -----------------------------------------------------
    # Accuracy
    # -----------------------------------------------------

    accuracy = 0

    if total_answers > 0:

        accuracy = round(
            (
                correct_answers
                / total_answers
            ) * 100
        )

    conn.close()

    return render_template(
        "progress.html",
        username=session["user"],
        completed_lessons=completed_lessons,
        quiz_attempts=quiz_attempts,
        correct_answers=correct_answers,
        wrong_answers=wrong_answers,
        total_answers=total_answers,
        accuracy=accuracy,
        total_lessons=total_lessons,
        lesson_progress_percent=lesson_progress_percent
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=False
    )