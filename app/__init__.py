from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = './uploads'
    app.config['SECRET_KEY'] = 'your_secret_key'

    # Créer le dossier d'upload s'il n'existe pas
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .routes import main
    app.register_blueprint(main)

    return app
