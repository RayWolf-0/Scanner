from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from database import Base
from datetime import datetime

# Tabla ROL_USUARIO
class RolUsuario(Base):
    __tablename__ = 'ROL_USUARIO'
    id_rol = Column(Integer, primary_key=True)
    nombre_rol = Column(String(50), nullable=False, unique=True)

# Tabla ESTADO_DOCUMENTO
class EstadoDocumento(Base):
    __tablename__ = 'ESTADO_DOCUMENTO'
    id_estado = Column(Integer, primary_key=True)
    nombre_estado = Column(String(50), nullable=False, unique=True)
    
# Tabla USUARIO
class Usuario(Base):
    __tablename__ = 'USUARIO'
    id_usuario = Column(Integer, primary_key=True)
    id_rol = Column(Integer, ForeignKey('ROL_USUARIO.id_rol'), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    mail = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    run = Column(String(20), unique=True, nullable=False)
    user = Column(String(10), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)

# Tabla ENCUESTA (según tu base de datos existente)
class Encuesta(Base):
    __tablename__ = 'encuesta'
    id_encuesta = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('USUARIO.id_usuario'), nullable=True)
    empresa = Column(String(100))
    rut = Column(String(20))
    encuestado = Column(String(100))
    cargo = Column(String(100))
    fecha = Column(String(50))
    telefono = Column(String(20))
    correo = Column(String(100))
    
# Tabla PLANTILLA
class Plantilla(Base):
    __tablename__ = 'PLANTILLA'
    id_plantilla = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    version = Column(Integer, default=1)
    ancho_pagina = Column(Integer, nullable=False)
    alto_pagina = Column(Integer, nullable=False)
    
# Tabla CAMPO_PLANTILLA
class CampoPlantilla(Base):
    __tablename__ = 'CAMPO_PLANTILLA'
    id_campo = Column(Integer, primary_key=True)
    id_plantilla = Column(Integer, ForeignKey('PLANTILLA.id_plantilla'), nullable=False)
    nombre_campo = Column(String(100), nullable=False)
    tipo_dato = Column(String(50), nullable=False)
    pos_x = Column(Integer, nullable=False)
    pos_y = Column(Integer, nullable=False)
    ancho = Column(Integer, nullable=False)
    alto = Column(Integer, nullable=False)
    
# Tabla DOCUMENTO
class Documento(Base):
    __tablename__ = 'DOCUMENTO'
    id_documento = Column(Integer, primary_key=True)
    id_plantilla = Column(Integer, ForeignKey('PLANTILLA.id_plantilla'), nullable=False)
    id_vendedor = Column(Integer, ForeignKey('USUARIO.id_usuario'), nullable=False)
    id_supervisor = Column(Integer, ForeignKey('USUARIO.id_usuario'), nullable=False)
    id_estado = Column(Integer, ForeignKey('ESTADO_DOCUMENTO.id_estado'), nullable=False)
    ruta_imagen = Column(String(300), nullable=False)
    ruta_pdf_final = Column(String(300), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
# Tabla DATO_EXTRAIDO 
class DatoExtraido(Base):
    __tablename__ = 'dato_extraido'
    id = Column(Integer, primary_key=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    nombre_empresa = Column(String(100))
    rut_empresa = Column(String(20))
    nombre_encuestado = Column(String(100))
    cargo = Column(String(100))
    correo = Column(String(100))
    telefono = Column(String(20))
    fecha = Column(String(50))
    firma = Column(String(100))
    p1_1 = Column(Text)
    p1_2 = Column(Text)
    p1_3 = Column(Text)
    p2_1 = Column(Text)
    p2_2 = Column(Text)
    p2_3 = Column(Text)
    p3_1 = Column(Text)
    p3_2 = Column(Text)
    p3_3 = Column(Text)
    red_mas_usa = Column(Text)
    red_sigue = Column(Text)
    correo_informativo = Column(Integer)
    observaciones = Column(Text)
    
# Tabla AUDITORIA
class Auditoria(Base):
    __tablename__ = 'AUDITORIA'
    id_auditoria = Column(Integer, primary_key=True)
    id_documento = Column(Integer, ForeignKey('DOCUMENTO.id_documento'), nullable=False)
    id_usuario = Column(Integer, ForeignKey('USUARIO.id_usuario'), nullable=False)
    observaciones = Column(String(500), nullable=False)
    fecha_hora = Column(DateTime, default=datetime.utcnow)