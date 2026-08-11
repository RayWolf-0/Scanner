import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave_secreta_scanner_2026')

    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_DIR, 'scanner.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH.replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Previene bloquedos del archivo SQLite en peticiones concurrentes
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 30}
    }

    STORAGE_FOLDER = os.path.join(BASE_DIR, 'storage')
    UPLOAD_FOLDER = os.path.join(STORAGE_FOLDER, 'uploads')
    PDFS_FOLDER = os.path.join(STORAGE_FOLDER, 'pdf_generado')
    FIRMAS_FOLDER = os.path.join(STORAGE_FOLDER, 'firmas')
    PLANTILLA_FOLDER = os.path.join(STORAGE_FOLDER, 'plantilla')

    @classmethod
    def init_app(cls, app=None):
        for carpeta in [cls.INSTANCE_DIR, cls.STORAGE_FOLDER, cls.UPLOAD_FOLDER, 
                        cls.PDFS_FOLDER, cls.FIRMAS_FOLDER, cls.PLANTILLA_FOLDER]:
            os.makedirs(carpeta, exist_ok=True)

Config.init_app()