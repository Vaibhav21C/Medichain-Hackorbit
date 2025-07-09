import sqlite3

# Connect to the database
conn = sqlite3.connect("medica.db")
cur = conn.cursor()

# === Create users table ===    
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Doctor', 'Patient'))
)
""")

# === Create requests table ===
cur.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    diagnosis_added INTEGER DEFAULT 0,
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (patient_id) REFERENCES users(id)
)
""")
cur.execute("""CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    gender TEXT,
    age INTEGER,
    profile_image TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS doctor_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER,
    patient_id INTEGER,
    note_type TEXT,
    title TEXT,
    content TEXT,
    date TEXT
)""")

# Commit the changes
conn.commit()

print("Database and tables initialized successfully.\n")

# === Optional: Print current users for verification ===
cur.execute("SELECT id, name, email, role FROM users")
rows = cur.fetchall()

if rows:
    print("Existing users:")
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}")
else:
    print("No users found in the database.")

# Close the connection
conn.close()
