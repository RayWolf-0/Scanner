import os
import pytesseract
from flask import Flask
from config import Config
from models import db, RolUsuario, EstadoDocumento
from routes.vendedor_routes import vendedor_bp
from routes.supervisor_routes import supervisor_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(vendedor_bp)
app.register_blueprint(supervisor_bp)

#Tesseract
pytesseract.pytesseract.tesseract_cmd = app.config['TESSERACT_CDM']

#ORM
db.init_app(app)

#Apartado de creacion de carpetas (si no están)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True),
os.makedirs(app.config['PDFS_FOLDER'], exist_ok=True),
os.makedirs(app.config['FIRMAS_FOLDER'], exist_ok=True),
os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not RolUsuario.query.first():
        db.session.add_all([
            RolUsuario(nombre_rol = 'VENDEDOR'),
            RolUsuario(nombre_rol = 'SUPERVISOR') 
        ])
    
    if not EstadoDocumento.query.first():
        db.session.add_all([ 
            EstadoDocumento(nombre_estado = 'PENDIENTE'),
            EstadoDocumento(nombre_estado = 'EN_REVISION'),
            EstadoDocumento(nombre_estado = 'APROBADO'),
            EstadoDocumento(nombre_estado = 'RECHAZADO')                     
        ])
        
    db.session.commit()
    print("Base de datos SQLite y Carpetas 'storage/' creadas")
        
if __name__ == '__main__':
    app.run(debug=True)
 