# StudentPath — Student Performance & Academic Support Website

A beginner-friendly Flask + SQLite project based on the provided reference screenshots.

## Features in this starter version
- Dashboard with subject marks, attendance, risk status, notifications, and a chart.
- What-if calculator for estimated score, grade, risk, and recommendations.
- Attendance tracker with subject-wise updates.
- Study planner with persistent study logs and subject totals.
- Create make-up/remedial class entries.
- Add assignments, notes, questions, and video links.
- Notifications generated when users update data.
- JSON endpoint: `/api/summary`.

## Important note about prediction
The current prediction is a transparent rule-based demonstration in `app.py`, not a trained machine-learning model. Do not use it for real academic decisions. A proper ML model requires an appropriate dataset, train/test split, evaluation, and responsible handling of student data.

## Requirements
- Python 3.10 or newer recommended
- VS Code
- Internet connection for the Chart.js CDN (the rest runs locally)

## Run on Windows (VS Code)
1. Download and extract `student_performance_website.zip`.
2. Open VS Code.
3. Choose **File → Open Folder** and select the extracted `student_performance_website` folder.
4. Open **Terminal → New Terminal**.
5. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
6. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
7. Install packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```
8. Start the website:
   ```powershell
   python app.py
   ```
9. Open the URL shown in terminal, normally `http://127.0.0.1:5000`.

## Run on macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Project structure
```text
student_performance_website/
├── app.py
├── requirements.txt
├── students.db          # created automatically on first run
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── predictions.html
│   ├── attendance.html
│   ├── planner.html
│   ├── classes.html
│   ├── materials.html
│   └── notifications.html
└── static/
    ├── style.css
    └── app.js
```

## How frontend and backend work
- **Frontend:** `templates/*.html` contains page layouts. `static/style.css` controls colors, spacing, cards, tables, and responsive layout. `static/app.js` is for optional browser-side JavaScript.
- **Backend:** `app.py` defines Flask routes, validates form input, calculates the demo prediction, and reads/writes SQLite data.
- **Database:** `students.db` is created automatically and holds demo subject records, study logs, materials, classes, and notifications.
- **Chart:** Dashboard fetches `/api/summary` and displays a chart using Chart.js.

## Common problems
- `python is not recognized`: try `py app.py` on Windows, or install Python and tick **Add Python to PATH** during installation.
- `No module named flask`: activate `.venv`, then run `python -m pip install -r requirements.txt`.
- Port 5000 already in use: stop the other server or change the last line in `app.py` to `app.run(debug=True, port=5001)` and open port 5001.
- To reset demo data: stop the app, delete `students.db`, and run `python app.py` again.
- Keep the terminal running while using the local website. Press `Ctrl+C` to stop it.

## Before using it as a real college system
Add login and role-based access (student/teacher/admin), password hashing, CSRF protection, authorization checks, secure file uploads, backups, audit logs, privacy/consent controls, and production deployment settings. The starter app is for learning/demo use and should not be exposed publicly as-is.
