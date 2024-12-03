import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

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

# Route pour la page de connexion
@app.route('/')
def login():
    return render_template('login.html')

# Route pour afficher le tableau de bord
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, end_date, assigned_to FROM tasks WHERE status='Pending' ORDER BY end_date ASC LIMIT 5")
    deadlines = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', deadlines=deadlines)

# Route pour uploader un fichier CSV
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

# Fonction pour importer les données d'un fichier CSV
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

# Route pour mettre à jour le statut d'une tâche
@app.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status="Completed" WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# Point d'entrée de l'application
if __name__ == '__main__':
    init_db()  # Initialisation de la base de données
    port = int(os.environ.get('PORT', 5000))  # Utilisation du port fourni par Render
    app.run(host='0.0.0.0', port=port, debug=True)

@app.route('/priorities')
def priorities():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Sélection des tâches urgentes pour chaque personne
    cursor.execute('''
        SELECT assigned_to, title, end_date, id
        FROM tasks
        WHERE status = "Pending" AND end_date >= ?
        ORDER BY end_date ASC
    ''', (today,))
    tasks = cursor.fetchall()
    conn.close()
    
    # Organisation des tâches par personne
    priorities = {}
    for assigned_to, title, end_date, task_id in tasks:
        if assigned_to not in priorities:
            priorities[assigned_to] = []
        priorities[assigned_to].append((task_id, title, end_date))
    
    return render_template('priorities.html', priorities=priorities, today=today)
