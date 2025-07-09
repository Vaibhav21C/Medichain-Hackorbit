from flask import Flask, render_template, request, g, redirect,url_for,jsonify, session, flash
import sqlite3
import os
from datetime import datetime, timedelta
app = Flask(__name__)
app.secret_key = os.urandom(24) 
DATABASE = "medica.db"

# === connection to DB ===
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# === Home Page ===
@app.route("/")
def index():
    return render_template("index.html")

# === Signup ===
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["Choice"]

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                        (name, email, password, role))
            conn.commit()
            conn.close()
            flash("Account created! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists. Please use a different one.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

# === Login ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["Choice"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ? AND role = ?", (email, password, role))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            flash("Login successful!", "success")

            if role == "Doctor":
                return redirect(url_for("doctor_dashboard"))
            else:
                return redirect(url_for("patient_dashboard"))
        else:
            flash("Invalid credentials. Try again.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# === Logout ===
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# === Doctor Dashboard ===
@app.route("/doctor/dashboard")
def doctor_dashboard():
    if "user_id" not in session or session.get("role") != "Doctor":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    doctor_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(CASE WHEN status = 'approved' THEN 1 END),
            COUNT(CASE WHEN status = 'pending' THEN 1 END),
            COUNT(CASE WHEN diagnosis_added = 1 THEN 1 END),
            COUNT(CASE WHEN timestamp >= datetime('now', '-2 days') THEN 1 END)
        FROM requests
        WHERE doctor_id = ?
    """, (doctor_id,))
    active_patients, pending_requests, diagnosis_notes, recent_activities = cur.fetchone()

    cur.execute("""
        SELECT r.id, r.timestamp, r.reason, r.status, u.name AS patient_name
        FROM requests r
        JOIN users u ON r.patient_id = u.id
        WHERE r.doctor_id = ? AND r.status = 'approved'
        ORDER BY r.timestamp DESC
        LIMIT 3
    """, (doctor_id,))
    recent_patients = cur.fetchall()

    cur.execute("""
        SELECT r.id, r.timestamp, r.reason, u.name AS patient_name
        FROM requests r
        JOIN users u ON r.patient_id = u.id
        WHERE r.doctor_id = ? AND r.status = 'pending'
        ORDER BY r.timestamp DESC
        LIMIT 2
    """, (doctor_id,))
    pending_requests_list = cur.fetchall()

    conn.close()
    return render_template("doctor-dashboard.html", name=session.get("name"),
                           active_patients=active_patients,
                           pending_requests=pending_requests,
                           recent_activities=recent_activities,
                           diagnosis_notes=diagnosis_notes,
                           recent_patients=recent_patients,
                           pending_requests_list=pending_requests_list)


@app.route("/doctor/patients")
def doctor_patients():
    if "user_id" not in session or session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT r.timestamp, r.reason, r.access_type, r.access_expiration, u.name, u.gender, u.age
    FROM requests r
    JOIN users u ON r.patient_id = u.id
    WHERE r.doctor_id = ? AND r.status = 'approved'
    """, (doctor_id,))

    patients = [
    {
        "timestamp": row[0],
        "reason": row[1],
        "access_type": row[2],
        "access_expiration": row[3],
        "name": row[4],
        "gender": row[5],
        "age": row[6]
    } for row in cur.fetchall()
    ]
    conn.close()
    return render_template("doctor-patients.html",name=session.get("name"), patients=patients)


@app.route("/doctor/requests")
def doctor_requests():
    if "user_id" not in session or session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT status, COUNT(*) 
        FROM requests 
        WHERE doctor_id = ?
        GROUP BY status
    """, (doctor_id,))
    status_counts = {row[0].lower(): row[1] for row in cur.fetchall()}
    counts = {
        "pending": status_counts.get("pending", 0),
        "approved": status_counts.get("approved", 0),
        "denied": status_counts.get("denied", 0)
    }

    cur.execute("""
        SELECT r.id, r.timestamp, r.reason, r.access_type, r.status, r.access_expiration, u.name
        FROM requests r
        JOIN users u ON r.patient_id = u.id
        WHERE r.doctor_id = ?
        ORDER BY r.timestamp DESC
    """, (doctor_id,))
    rows = cur.fetchall()

    pending_requests = []
    approved_requests = []
    denied_requests = []

    for row in rows:
        req = {
            "id": row[0],
            "timestamp": row[1],
            "reason": row[2],
            "access_type": row[3],
            "status": row[4],
            "access_expiration": row[5],
            "patient_name": row[6]
        }
        if req["status"].lower() == "pending":
            pending_requests.append(req)
        elif req["status"].lower() == "approved":
            approved_requests.append(req)
        elif req["status"].lower() == "denied":
            denied_requests.append(req)

    conn.close()
    return render_template(
        "doctor-requests.html",
        name=session.get("name"),
        counts=counts,
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        denied_requests=denied_requests
    )

@app.route("/submit-request", methods=["POST"])
def submit_request():
    if "user_id" not in session or session.get("role") != "Doctor":
        return redirect(url_for("login"))

    doctor_id = session["user_id"]
    patient_identifier = request.form["patient_identifier"]
    access_type = request.form["access_level"]
    reason = request.form["reason"]
    record_types = request.form.getlist("record_types")
    duration = request.form["access_duration"]

    days_map = {
        "1month": 30,
        "3months": 90,
        "6months": 180,
        "1year": 365
    }
    expiration_date = datetime.now() + timedelta(days=days_map.get(duration, 180))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE id = ? OR name = ?", (patient_identifier, patient_identifier))
    patient = cur.fetchone()
    if not patient:
        flash("Patient not found.")
        return redirect(url_for("doctor_requests"))

    patient_id = patient[0]

    cur.execute("""
        INSERT INTO requests (doctor_id, patient_id, access_type, reason, record_types, status, timestamp, access_expiration)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (
        doctor_id, patient_id, access_type, reason, ','.join(record_types),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        expiration_date.strftime("%Y-%m-%d")
    ))
    conn.commit()
    conn.close()

    flash("Access request submitted successfully.")
    return redirect(url_for("doctor_requests"))

@app.route("/doctor/request/view", methods=["POST"])
def view_request():
    if "user_id" not in session or session.get("role") != "Doctor":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    request_id = request.form["request_id"]
    flash(f"View Request #{request_id} (demo)", "info")
    return redirect(url_for("doctor_dashboard"))

@app.route("/doctor/request/cancel", methods=["POST"])
def cancel_request():
    if "user_id" not in session or session.get("role") != "Doctor":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    request_id = request.form["request_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM requests WHERE id = ? AND doctor_id = ?", (request_id, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Access request cancelled.", "success")
    return redirect(url_for("doctor_dashboard"))

@app.route("/doctor/search")
def doctor_search():
    if "user_id" not in session or session.get("role") != "Doctor":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()

    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("doctor_dashboard"))

    doctor_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.name, r.timestamp, r.reason, r.status
        FROM requests r
        JOIN users u ON r.patient_id = u.id
        WHERE r.doctor_id = ? AND u.name LIKE ?
        ORDER BY r.timestamp DESC
    """, (doctor_id, f"%{query}%"))
    results = cur.fetchall()
    conn.close()

    return render_template("doctor-search-results.html", name=session.get("name"), query=query, results=results)

def get_doctor_notes(doctor_id):
    conn = sqlite3.connect('medica.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT n.date, n.note_type, n.title,
               p.name AS patient_name,
               p.profile_image AS patient_image
        FROM doctor_notes n
        JOIN patients p ON n.patient_id = p.id
        WHERE n.doctor_id = ?
        ORDER BY n.date DESC
    """, (doctor_id,))
    
    return cur.fetchall()
@app.route('/doctor/notes')
def doctor_notes():
    doctor_id = session.get('user_id', 1)  
    notes = get_doctor_notes(doctor_id)
    return render_template('doctor-notes.html', notes=notes)


@app.route("/doctor/settings")
def doctor_settings():
    if "user_id" not in session or session.get("role") != "Doctor":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    return render_template("doctor-settings.html", name=session.get("name"))



# === Patient Dashboard ===
@app.route("/patient/dashboard")
def patient_dashboard():
    if "user_id" not in session or session.get("role") != "Patient":
        return redirect(url_for("login"))

    patient_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM requests WHERE patient_id = ?", (patient_id,))
    medical_records = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT doctor_id) 
        FROM requests 
        WHERE patient_id = ? AND status = 'approved'
    """, (patient_id,))
    authorized_doctors = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) 
        FROM requests 
        WHERE patient_id = ? AND status = 'approved' AND updated_at >= DATE('now', '-30 days')
    """, (patient_id,))
    recent_activities = cur.fetchone()[0]

    cur.execute("""
        SELECT r.access_type, r.reason, r.updated_at, u.name AS doctor_name
        FROM requests r
        LEFT JOIN users u ON r.doctor_id = u.id
        WHERE r.patient_id = ? AND r.status = 'approved'
        ORDER BY r.updated_at DESC
        LIMIT 3
    """, (patient_id,))
    recent_records = [
        {
            "type": row[0],
            "reason": row[1],
            "timestamp": row[2],
            "doctor": row[3] or "N/A"
        }
        for row in cur.fetchall()
    ]
    cur.execute("""
    SELECT u.name, u.gender, u.specialization
    FROM requests r
    JOIN users u ON r.doctor_id = u.id
    WHERE r.patient_id = ? AND r.status = 'approved'
    GROUP BY r.doctor_id
    ORDER BY r.updated_at DESC
    LIMIT 3
    """, (patient_id,))
    authorized_doctor_list = cur.fetchall()

    conn.close()

    return render_template(
    "patient-dashboard.html",
    name=session.get("name"),
    stats={
        "medical_records": medical_records,
        "authorized_doctors": authorized_doctors,
        "recent_activities": recent_activities
    },
    recent_records=recent_records,
    authorized_doctor_list=authorized_doctor_list
)

@app.route("/patient/search")
def patient_search():
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    query = request.args.get("q", "").strip()
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("patient_dashboard"))
    patient_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.access_type, r.reason, r.updated_at, u.name AS doctor_name
        FROM requests r
        JOIN users u ON r.doctor_id = u.id
        WHERE r.patient_id = ? AND r.status = 'approved'
          AND (
              r.reason LIKE ? OR 
              r.access_type LIKE ? OR 
              u.name LIKE ?
          )
        ORDER BY r.updated_at DESC
    """, (patient_id, f"%{query}%", f"%{query}%", f"%{query}%"))
    results = cur.fetchall()
    conn.close()

    return render_template(
        "patient-search-results.html",
        name=session.get("name"),
        query=query,
        results=results
    )

@app.route("/patient/access")
def patient_access():
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    patient_id = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT status, COUNT(*) FROM requests
        WHERE patient_id = ?
        GROUP BY status
    """, (patient_id,))
    result = {row[0].lower(): row[1] for row in cur.fetchall()}
    access_counts = {
        "active": result.get("approved", 0),
        "pending": result.get("pending", 0),
        "revoked": result.get("revoked", 0)
    }
    cur.execute("""SELECT * FROM requests WHERE patient_id = ? AND status = 'approved'""", (patient_id,))
    active_access = cur.fetchall()

    cur.execute("""SELECT * FROM requests WHERE patient_id = ? AND status = 'pending'""", (patient_id,))
    pending_requests = cur.fetchall()

    cur.execute("""SELECT * FROM requests WHERE patient_id = ? AND status = 'revoked'""", (patient_id,))
    revoked_access = cur.fetchall()

    conn.close()

    return render_template("patient-access.html",
                           name=session.get("name"),
                           access_counts=access_counts,
                           active_access=active_access,
                           pending_requests=pending_requests,
                           revoked_access=revoked_access)


@app.route("/patient/records")
def patient_records(): 
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    patient_id = session["user_id"]

    record_type = request.args.get("record_type", "all")
    date_range = request.args.get("date_range", "all")
    provider = request.args.get("provider", "all")

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT r.access_type, r.reason, r.updated_at, u.name AS doctor_name, u.hospital
        FROM requests r
        JOIN users u ON r.doctor_id = u.id
        WHERE r.patient_id = ? AND r.status = 'approved'
    """
    params = [patient_id]

    if record_type != "all":
        query += " AND r.access_type = ?"
        params.append(record_type)

    if date_range == "month":
        query += " AND r.updated_at >= DATE('now', '-1 month')"
    elif date_range == "6months":
        query += " AND r.updated_at >= DATE('now', '-6 months')"
    elif date_range == "year":
        query += " AND r.updated_at >= DATE('now', '-1 year')"

    if provider != "all":
        query += " AND u.hospital = ?"
        params.append(provider)

    query += " ORDER BY r.updated_at DESC"

    cur.execute(query, params)
    records = cur.fetchall()
    conn.close()

    return render_template(
        "patient-records.html",
        name=session.get("name"),
        records=records,
        filters={
            "record_type": record_type,
            "date_range": date_range,
            "provider": provider
        }
    )

@app.route("/patient/upload", methods=["POST"])
def upload_record():
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    patient_id = session["user_id"]
    access_type = request.form["access_type"]
    reason = request.form["reason"]
    doctor_name = request.form["doctor_name"]
    hospital = request.form.get("hospital", "")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE name = ? AND role = 'Doctor'", (doctor_name,))
    doctor = cur.fetchone()

    if doctor:
        doctor_id = doctor["id"]
    else:
        cur.execute("INSERT INTO users (name, role, hospital) VALUES (?, 'Doctor', ?)", (doctor_name, hospital))
        doctor_id = cur.lastrowid

    cur.execute("""
        INSERT INTO requests (doctor_id, patient_id, access_type, reason, status, updated_at)
        VALUES (?, ?, ?, ?, 'approved', datetime('now'))
    """, (doctor_id, patient_id, access_type, reason))

    conn.commit()
    conn.close()

    flash("Medical record uploaded successfully.", "success")
    return redirect(url_for("patient_records"))

@app.route("/patient/grant-access", methods=["POST"])
def grant_access():
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    patient_id = session["user_id"]
    doctor_identifier = request.form["doctor_identifier"]
    access_type = request.form["access_type"]
    reason = request.form["reason"]
    duration = request.form["access_duration"]

    days_map = {
        "1month": 30,
        "3months": 90,
        "6months": 180,
        "1year": 365
    }
    expiration_date = datetime.now() + timedelta(days=days_map.get(duration, 30))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE (id = ? OR name = ?) AND role = 'Doctor'", (doctor_identifier, doctor_identifier))
    doctor = cur.fetchone()

    if not doctor:
        flash("Doctor not found.", "error")
        return redirect(url_for("patient_access"))

    doctor_id = doctor["id"]
    cur.execute("""
        INSERT INTO requests (doctor_id, patient_id, access_type, reason, status, timestamp, access_expiration)
        VALUES (?, ?, ?, ?, 'approved', ?, ?)
    """, (
        doctor_id, patient_id, access_type, reason,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        expiration_date.strftime("%Y-%m-%d")
    ))
    conn.commit()
    conn.close()

    flash("Access granted to doctor successfully.", "success")
    return redirect(url_for("patient_access"))

@app.route("/patient/settings")
def patient_settings(): 
    if "user_id" not in session or session.get("role") != "Patient":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    return render_template("patient-settings.html", name=session.get("name"))

if __name__ == '__main__':
    app.run(debug=True)