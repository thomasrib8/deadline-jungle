from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        assigned_to TEXT NOT NULL,
                        status TEXT DEFAULT 'Pending'
                    )''')
    conn.commit()
    conn.close()

@main.route('/')
def login():
    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, end_date, assigned_to FROM tasks WHERE status='Pending' ORDER BY end_date ASC LIMIT 5")
    deadlines = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', deadlines=deadlines)

@main.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join('./uploads', filename)
    file.save(file_path)
    import_csv(file_path)
    return redirect(url_for('main.dashboard'))

def import_csv(file_path):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    with open(file_path, 'r') as file:
        for line in file.readlines()[1:]:
            title, start_date, end_date, assigned_to = line.strip().split(',')
            cursor.execute('INSERT INTO tasks (title, start_date, end_date, assigned_to) VALUES (?, ?, ?, ?)', 
                           (title, start_date, end_date, assigned_to))
    conn.commit()
    conn.close()

@main.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status="Completed" WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('main.dashboard'))
