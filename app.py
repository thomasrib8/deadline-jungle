import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# Initialisation de l'application Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SECRET_KEY'] = 'your_secret_key'

# Créer le dossier d'upload s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    # Récupération des tâches urgentes pour le panneau des priorités
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT assigned_to, title, end_date, id
        FROM tasks
        WHERE status = "Pending" AND end_date >= ?
        ORDER BY end_date ASC
    ''', (today,))
    tasks = cursor.fetchall()
    conn.close()

    # Organisation des tâches par personne et limitation à 3 tâches par personne
    priorities = {}
    for assigned_to, title, end_date, task_id in tasks:
        if assigned_to not in priorities:
            priorities[assigned_to] = []
        if len(priorities[assigned_to]) < 3:  # Limite à 3 tâches par personne
            priorities[assigned_to].append((task_id, title, end_date))

    # Récupération des événements du mois prochain pour le calendrier
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    next_month_start = (datetime.now().replace(day=1) + timedelta(days=31)).strftime('%Y-%m-%d')
    next_month_end = (datetime.now().replace(day=1) + timedelta(days=61)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT title, start_date, end_date, assigned_to
        FROM tasks
        WHERE end_date BETWEEN ? AND ?
        ORDER BY end_date ASC
    ''', (next_month_start, next_month_end))
    next_month_events = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', priorities=priorities, today=today, next_month_events=next_month_events)

@app.route('/add_tasks')
def add_tasks():
    return render_template('add_tasks.html')

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    assigned_to = request.form['assigned_to']
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (title, start_date, end_date, assigned_to) VALUES (?, ?, ?, ?)', 
                   (title, start_date, end_date, assigned_to))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    import_csv(file_path)
    return redirect('/dashboard')

def import_csv(file_path):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file.readlines()[1:]:
            title, start_date, end_date, assigned_to = line.strip().split(',')
            cursor.execute('INSERT INTO tasks (title, start_date, end_date, assigned_to) VALUES (?, ?, ?, ?)', 
                           (title, start_date, end_date, assigned_to))
    conn.commit()
    conn.close()

@app.route('/all_tasks')
def all_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, end_date, assigned_to FROM tasks ORDER BY end_date ASC')
    tasks = cursor.fetchall()
    conn.close()
    return render_template('all_tasks.html', tasks=tasks)

@app.route('/update_assigned/<int:task_id>', methods=['POST'])
def update_assigned(task_id):
    new_assigned_to = request.form['new_assigned_to']
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET assigned_to=? WHERE id=?', (new_assigned_to, task_id))
    conn.commit()
    conn.close()
    return redirect('/all_tasks')

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect('/all_tasks')

@app.route('/calendar')
def calendar():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    future_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT title, start_date, end_date, assigned_to
        FROM tasks
        WHERE end_date BETWEEN ? AND ?
        ORDER BY end_date ASC
    ''', (today, future_date))
    events = cursor.fetchall()
    conn.close()
    return render_template('calendar.html', events=events)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
