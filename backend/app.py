import os
from flask import Flask
from config import Config
from models import db, RolUsuario, EstadoDocumento
from routes.vendedor_routes import vendedor_bp
from routes.supervisor_routes import supervisor_bp

app = Flask(__name__)
app.config.from_object(Config)

# Registro de Blueprints
app.register_blueprint(vendedor_bp)
app.register_blueprint(supervisor_bp)

# Inicialización de ORM
db.init_app(app)

# Creación de carpetas necesarias
os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
os.makedirs(app.config.get('PDFS_FOLDER', 'storage/pdfs'), exist_ok=True)
os.makedirs(app.config.get('FIRMAS_FOLDER', 'storage/firmas'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

@app.cli.command("init-db")
def init_db():
    """Inicializa las tablas y los registros base en la BD."""
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)