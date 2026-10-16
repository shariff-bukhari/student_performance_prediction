from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3, os, json
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "students.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-key")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, subject TEXT NOT NULL,
            marks REAL NOT NULL DEFAULT 0,
            attendance REAL NOT NULL DEFAULT 0,
            study_hours REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL, hours REAL NOT NULL,
            note TEXT DEFAULT '', log_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, kind TEXT NOT NULL,
            link TEXT NOT NULL, subject TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, subject TEXT NOT NULL,
            class_type TEXT NOT NULL, class_date TEXT NOT NULL,
            description TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL, category TEXT NOT NULL,
            created_at TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            now = datetime.now().isoformat(timespec="minutes")
            demo = [
                ("Aarav", "Mathematics", 72, 82, 5, now),
                ("Aarav", "Physics", 48, 68, 3, now),
                ("Aarav", "DBMS", 81, 91, 6, now),
                ("Aarav", "Computer Networks", 59, 76, 4, now),
            ]
            con.executemany("INSERT INTO students(name,subject,marks,attendance,study_hours,updated_at) VALUES(?,?,?,?,?,?)", demo)
            con.execute("INSERT INTO notifications(message,category,created_at) VALUES(?,?,?)",
                        ("Welcome! Review your subjects and update your progress.", "General", now))
            con.execute("INSERT INTO materials(title,kind,link,subject,created_at) VALUES(?,?,?,?,?)",
                        ("DBMS revision notes", "Notes", "https://example.com/dbms-notes", "DBMS", now))

init_db()

def get_subjects():
    with db() as con:
        return con.execute("SELECT * FROM students ORDER BY subject").fetchall()

def classify(marks, attendance):
    if attendance < 75 or marks < 40:
        return "High risk"
    if attendance < 85 or marks < 60:
        return "Needs attention"
    return "On track"

def prediction(marks, attendance, hours):
    # Transparent demo scoring rule, NOT a trained ML model.
    score = max(0, min(100, 0.60 * marks + 0.25 * attendance + 3 * hours))
    risk = classify(score, attendance)
    if score >= 85: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 55: grade = "C"
    elif score >= 40: grade = "D"
    else: grade = "F"
    return round(score, 1), grade, risk

@app.route("/")
def dashboard():
    rows = get_subjects()
    if not rows:
        rows = []
    avg_marks = round(sum(r["marks"] for r in rows)/len(rows), 1) if rows else 0
    avg_att = round(sum(r["attendance"] for r in rows)/len(rows), 1) if rows else 0
    scores = [prediction(r["marks"], r["attendance"], r["study_hours"])[0] for r in rows]
    risks = sum(1 for r in rows if classify(r["marks"], r["attendance"]) == "High risk")
    with db() as con:
        notices = con.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 5").fetchall()
        logs = con.execute("SELECT * FROM study_logs ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", rows=rows, avg_marks=avg_marks, avg_att=avg_att,
                           risks=risks, notices=notices, logs=logs)

@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    result = None
    if request.method == "POST":
        try:
            marks = float(request.form["marks"])
            attendance = float(request.form["attendance"])
            hours = float(request.form["hours"])
            if not (0 <= marks <= 100 and 0 <= attendance <= 100 and 0 <= hours <= 60):
                raise ValueError
            score, grade, risk = prediction(marks, attendance, hours)
            result = {"score": score, "grade": grade, "risk": risk,
                      "recommendations": [
                          "Attend upcoming classes and meet your subject teacher." if attendance < 75 else "Maintain your attendance.",
                          "Schedule 30–60 minutes of focused practice for this subject." if marks < 60 else "Use weekly revision to maintain your marks.",
                          "Log your study hours so planned and completed work can be compared."
                      ]}
        except (ValueError, KeyError):
            flash("Enter valid values: marks and attendance from 0–100, study hours from 0–60.", "error")
    return render_template("predictions.html", result=result)

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if request.method == "POST":
        try:
            subject = request.form["subject"].strip()
            value = float(request.form["attendance"])
            if not subject or not 0 <= value <= 100: raise ValueError
            with db() as con:
                con.execute("UPDATE students SET attendance=?, updated_at=? WHERE subject=?",
                            (value, datetime.now().isoformat(timespec="minutes"), subject))
                con.execute("INSERT INTO notifications(message,category,created_at) VALUES(?,?,?)",
                            (f"Attendance updated for {subject}: {value:.1f}%.", "Attendance", datetime.now().isoformat(timespec="minutes")))
            flash("Attendance updated.", "success")
        except (ValueError, KeyError):
            flash("Please enter a valid attendance percentage.", "error")
        return redirect(url_for("attendance"))
    rows = get_subjects()
    return render_template("attendance.html", rows=rows)

@app.route("/planner", methods=["GET", "POST"])
def planner():
    if request.method == "POST":
        try:
            subject = request.form["subject"].strip()
            hours = float(request.form["hours"])
            note = request.form.get("note", "").strip()
            if not subject or not 0 < hours <= 24: raise ValueError
            with db() as con:
                con.execute("INSERT INTO study_logs(subject,hours,note,log_date) VALUES(?,?,?,?)",
                            (subject, hours, note, date.today().isoformat()))
                con.execute("INSERT INTO notifications(message,category,created_at) VALUES(?,?,?)",
                            (f"You logged {hours:g} study hour(s) for {subject}.", "Study planner", datetime.now().isoformat(timespec="minutes")))
            flash("Study session logged.", "success")
        except (ValueError, KeyError):
            flash("Enter a subject and hours between 0 and 24.", "error")
        return redirect(url_for("planner"))
    with db() as con:
        logs = con.execute("SELECT * FROM study_logs ORDER BY id DESC").fetchall()
        totals = con.execute("SELECT subject, SUM(hours) total FROM study_logs GROUP BY subject ORDER BY total DESC").fetchall()
    return render_template("planner.html", logs=logs, totals=totals)

@app.route("/classes", methods=["GET", "POST"])
def classes():
    if request.method == "POST":
        title = request.form["title"].strip()
        subject = request.form["subject"].strip()
        class_type = request.form["class_type"]
        class_date = request.form["class_date"]
        description = request.form.get("description", "").strip()
        if title and subject and class_date:
            with db() as con:
                con.execute("INSERT INTO classes(title,subject,class_type,class_date,description) VALUES(?,?,?,?,?)",
                            (title, subject, class_type, class_date, description))
                con.execute("INSERT INTO notifications(message,category,created_at) VALUES(?,?,?)",
                            (f"New {class_type.lower()} class: {title} ({subject}) on {class_date}.", "Classes", datetime.now().isoformat(timespec="minutes")))
            flash("Class created.", "success")
        else:
            flash("Fill in title, subject and date.", "error")
        return redirect(url_for("classes"))
    with db() as con:
        items = con.execute("SELECT * FROM classes ORDER BY class_date").fetchall()
    return render_template("classes.html", items=items)

@app.route("/materials", methods=["GET", "POST"])
def materials():
    if request.method == "POST":
        title = request.form["title"].strip()
        subject = request.form["subject"].strip()
        kind = request.form["kind"]
        link = request.form["link"].strip()
        if title and subject and link:
            with db() as con:
                con.execute("INSERT INTO materials(title,kind,link,subject,created_at) VALUES(?,?,?,?,?)",
                            (title, kind, link, subject, datetime.now().isoformat(timespec="minutes")))
                con.execute("INSERT INTO notifications(message,category,created_at) VALUES(?,?,?)",
                            (f"New {kind.lower()} added: {title} ({subject}).", "Teacher uploads", datetime.now().isoformat(timespec="minutes")))
            flash("Study material added.", "success")
        else:
            flash("Fill in all fields. Use a URL to a file or video.", "error")
        return redirect(url_for("materials"))
    with db() as con:
        items = con.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()
    return render_template("materials.html", items=items)

@app.route("/notifications", methods=["GET", "POST"])
def notifications():
    with db() as con:
        if request.method == "POST":
            con.execute("UPDATE notifications SET is_read=1")
            flash("All notifications marked as read.", "success")
        items = con.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
    return render_template("notifications.html", items=items)

@app.route("/api/summary")
def api_summary():
    rows = get_subjects()
    return jsonify([{"subject": r["subject"], "marks": r["marks"], "attendance": r["attendance"],
                     "study_hours": r["study_hours"], "risk": classify(r["marks"], r["attendance"])} for r in rows])

if __name__ == "__main__":
    app.run(debug=True)
