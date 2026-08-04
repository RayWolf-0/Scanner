import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'clave_secreta_para_desarrollo'
    
    #base de datos sqlite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'scanner.db').replace('\\','/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    #Carpetas de Almacenamiento
    STORAGE_FOLDER = os.path.join(BASE_DIR, 'storage')
    UPLOAD_FOLDER = os.path.join(STORAGE_FOLDER, 'uploads')
    PDFS_FOLDER = os.path.join(STORAGE_FOLDER, 'pdf_generado')
    FIRMAS_FOLDER = os.path.join(STORAGE_FOLDER, 'firmas')