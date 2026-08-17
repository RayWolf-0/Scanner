import os
import sqlite3
from flask_cors import CORS 
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine
from config import Config
from models import db, RolUsuario, EstadoDocumento
from routes.auth_routes import auth_bp
from routes.encuesta_routes import encuesta_bp

from routes.vendedor_routes import vendedor_bp
from routes.supervisor_routes import supervisor_bp

from routes.auth_routes import auth_bp
from routes.encuesta_routes import encuesta_bp

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
CORS(app)

# iniciar
db.init_app(app)

# evita bloqueos con sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

# blueprints
app.register_blueprint(vendedor_bp)
app.register_blueprint(supervisor_bp)

# nuevos
app.register_blueprint(auth_bp)
app.register_blueprint(encuesta_bp)

# Creación de carpetas necesarias
os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
os.makedirs(app.config.get('PDFS_FOLDER', 'storage/pdfs'), exist_ok=True)
os.makedirs(app.config.get('FIRMAS_FOLDER', 'storage/firmas'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

@app.cli.command("init-db")
def init_db():
    """Inicializa las tablas y los registros base en la BD."""
    with app.app_context():
        db.create_all()

        if not RolUsuario.query.first():
            db.session.add_all([
                RolUsuario(nombre_rol='VENDEDOR'),
                RolUsuario(nombre_rol='SUPERVISOR')
            ])

        if not EstadoDocumento.query.first():
            db.session.add_all([
                EstadoDocumento(nombre_estado='PENDIENTE'),
                EstadoDocumento(nombre_estado='EN_REVISION'),
                EstadoDocumento(nombre_estado='APROBADO'),
                EstadoDocumento(nombre_estado='RECHAZADO'),
                EstadoDocumento(nombre_estado='Procesado')
            ])

        db.session.commit()
        print("Base de datos y carpetas creadas con éxito.")
    app.register_blueprint(auth_bp)
    app.register_blueprint(encuesta_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)