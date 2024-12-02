from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = 'your_secret_key'

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

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, end_date, assigned_to FROM tasks WHERE status='Pending' ORDER BY end_date ASC LIMIT 5")
    deadlines = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', deadlines=deadlines)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    import_csv(file_path)
    return redirect(url_for('dashboard'))

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

@app.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status="Completed" WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
