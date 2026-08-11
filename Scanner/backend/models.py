from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#Tabla ROL_USUARIO
class RolUsuario(db.Model):
    __tablename__ = 'ROL_USUARIO'
    id_rol = db.Column(db.Integer, primary_key = True)
    nombre_rol = db.Column(db.String(50), nullable=False, unique=True)

#Tabla ESTADO_DOCUMENTO
class EstadoDocumento(db.Model):
    __tablename__ = 'ESTADO_DOCUMENTO'
    id_estado = db.Column(db.Integer, primary_key = True)
    nombre_estado = db.Column(db.String(50), nullable=False, unique=True)
    
#Tabla USUARIO
class Usuario(db.Model):
    __tablename__ = 'USUARIO'
    id_usuario = db.Column(db.Integer, primary_key = True)
    id_rol = db.Column(db.Integer, db.ForeignKey('ROL_USUARIO.id_rol'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    run = db.Column(db.String(20), unique=True, nullable=False)
    user = db.Column(db.String(10), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    
#Tabla PLANTILLA
class Plantilla(db.Model):
    __tablename__ = 'PLANTILLA'
    id_plantilla = db.Column(db.Integer, primary_key = True)
    nombre = db.Column(db.String(100), nullable=False)
    version = db.Column(db.Integer, default=1)
    ancho_pagina = db.Column(db.Integer, nullable=False)
    alto_pagina = db.Column(db.Integer, nullable=False)
    
#Tabla CAMPO_PLANTILLA
class CampoPlantilla(db.Model):
    __tablename__ = 'CAMPO_PLANTILLA'
    id_campo = db.Column(db.Integer, primary_key=True)
    id_plantilla = db.Column(db.Integer, db.ForeignKey('PLANTILLA.id_plantilla'), nullable=False)
    nombre_campo = db.Column(db.String(100), nullable=False)
    tipo_dato = db.Column(db.String(50), nullable=False)
    pos_x = db.Column(db.Float, nullable=False)
    ancho = db.Column(db.Float, nullable=False)
    alto = db.Column(db.Float, nullable=False)
    pos_y = db.Column(db.Float, nullable=False)
    
#Tabla DOCUMENTO
class Documento(db.Model):
    __tablename__ = 'DOCUMENTO'
    id_documento = db.Column(db.Integer, primary_key=True)
    id_plantilla = db.Column(db.Integer, db.ForeignKey('PLANTILLA.id_plantilla'), nullable=False)
    id_vendedor = db.Column(db.Integer, db.ForeignKey('USUARIO.id_usuario'), nullable=False)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('USUARIO.id_usuario'), nullable=False)
    id_estado = db.Column(db.Integer, db.ForeignKey('ESTADO_DOCUMENTO.id_estado'), nullable=False)
    ruta_imagen = db.Column(db.String(300), nullable=False)
    ruta_pdf_final = db.Column(db.String(300), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
#Tabla DATO_EXTRAIDO 
class DatoExtraido(db.Model):
    __tablename__ = 'DATO_EXTRAIDO'
    id_dato = db.Column(db.Integer, primary_key=True)
    id_documento = db.Column(db.Integer, db.ForeignKey('DOCUMENTO.id_documento'), nullable=False)
    id_campo = db.Column(db.Integer, db.ForeignKey('CAMPO_PLANTILLA.id_campo'), nullable=False)
    valor_extraido = db.Column(db.Text, nullable=True)
    valor_corregido = db.Column(db.Text, nullable=True)
    
#Tabla AUDITORIA
class Auditoria(db.Model):
    __tablename__ = 'AUDITORIA'
    id_auditoria = db.Column(db.Integer, primary_key=True)
    id_documento = db.Column(db.Integer, db.ForeignKey('DOCUMENTO.id_documento'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('USUARIO.id_usuario'), nullable=False)
    observaciones = db.Column(db.String(500), nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    