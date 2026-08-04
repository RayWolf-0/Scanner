import os
import time
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from models import db, Usuario, Documento, EstadoDocumento, DatoExtraido
from services.processor import procesar_documento_completo
from services.pdf_service import PDFService

vendedor_bp = Blueprint('vendedor', __name__, url_prefix='/api/vendedor')


@vendedor_bp.route('/login', methods=['POST'])
def login():
  """Endpoint para autenticación de vendedor."""
  datos = request.json or {}
  usuario_ingresado = datos.get('user')
  password_ingresada = datos.get('contrasena')

  usuario = Usuario.query.filter(
      (Usuario.mail == usuario_ingresado) | (Usuario.user == usuario_ingresado)
  ).first()

  if usuario and check_password_hash(usuario.contrasena, password_ingresada):
    return (
        jsonify({
            'status': 'success',
            'id_usuario': usuario.id_usuario,
            'nombre': f'{usuario.nombre} {usuario.apellido}',
            'rol': usuario.id_rol,
        }),
        200,
    )

  return jsonify({'error': 'Credenciales incorrectas'}), 401


@vendedor_bp.route('/subir', methods=['POST'])
def subir_documento():
  """Endpoint principal para recibir la foto desde Postman y procesarla."""
  # 1. Validaciones de entrada
  if 'imagen' not in request.files:
    return jsonify({'error': 'No se ha enviado imagen'}), 400

  id_usuario = request.form.get('id_usuario')
  if not id_usuario:
    return jsonify({'error': 'Falta id_usuario'}), 400

  archivo = request.files['imagen']
  if archivo.filename == '':
    return jsonify({'error': 'Archivo vacío'}), 400

  # 2. Asegurar directorios
  os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
  os.makedirs(current_app.config['FIRMAS_FOLDER'], exist_ok=True)
  os.makedirs(current_app.config['PDFS_FOLDER'], exist_ok=True)

  # 3. Guardar imagen subida (ej: test2.jpg)
  filename = secure_filename(archivo.filename)
  ruta_imagen = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
  archivo.save(ruta_imagen)

  try:
    # 4. Crear el registro preliminar del Documento en la BD
    estado_pendiente = EstadoDocumento.query.filter_by(
        nombre_estado='PENDIENTE'
    ).first()

    nuevo_doc = Documento(
        id_plantilla=1,  # ID de la encuesta 2026 calibrada
        id_vendedor=id_usuario,
        id_estado=estado_pendiente.id_estado if estado_pendiente else 1,
        ruta_imagen=ruta_imagen,
    )
    db.session.add(nuevo_doc)
    db.session.commit()

    # 5. Ejecutar la canalización de procesamiento dinámico (OpenCV + Paddle + SQLite)
    # Procesa recortes según lo grabado en CAMPO_PLANTILLA y llena DATO_EXTRAIDO
    import numpy as np
    # Esquinas por defecto (imagen completa sin corrección de perspectiva)
    esquinas_detectadas = np.array([
        [0, 0],
        [1000, 0],
        [1000, 1400],
        [0, 1400]
    ], dtype=np.float32)
    
    db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    procesar_documento_completo(
        id_documento=nuevo_doc.id_documento,
        esquinas_detectadas=esquinas_detectadas,
        db_path=db_path
    )

    # 6. Generación opcional de PDF compilado tomando los datos guardados en BD
    nombre_pdf = f'final_{nuevo_doc.id_documento}_{int(time.time())}.pdf'
    ruta_pdf_generado = os.path.join(
        current_app.config['PDFS_FOLDER'], nombre_pdf
    )

    plantilla_pdf = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'storage',
        'plantilla',
        'maestra.pdf',
    )

    if os.path.exists(plantilla_pdf):
      # Recuperar datos extraídos desde la BD para armar el PDF
      # Usar SQL raw para hacer JOIN entre DATO_EXTRAIDO y CAMPO_PLANTILLA
      query = """
        SELECT cp.nombre_campo, COALESCE(de.valor_extraido, '') as valor_extraido
        FROM DATO_EXTRAIDO de
        JOIN CAMPO_PLANTILLA cp ON de.id_campo = cp.id_campo
        WHERE de.id_documento = :id_documento
      """
      try:
        conn_raw = db.engine.connect()
        result = conn_raw.execute(db.text(query), {'id_documento': nuevo_doc.id_documento})
        datos_dict = {row[0]: row[1] for row in result if row[1]}
        conn_raw.close()
      except Exception as query_error:
        print(f'Error ejecutando consulta de datos: {query_error}')
        datos_dict = {}

      PDFService.generar_pdf_final(
          id_documento=nuevo_doc.id_documento,
          id_plantilla=nuevo_doc.id_plantilla,
          db_path=db_path,
          ruta_plantilla=plantilla_pdf,
          ruta_salida=ruta_pdf_generado,
          ruta_firma=None,
      )
      nuevo_doc.ruta_pdf_final = ruta_pdf_generado
      db.session.commit()

    return (
        jsonify({
            'status': 'success',
            'id_documento': nuevo_doc.id_documento,
            'mensaje': 'Documento procesado correctamente',
            'ruta_pdf': nuevo_doc.ruta_pdf_final,
        }),
        201,
    )

  except Exception as e:
    db.session.rollback()
    return jsonify({'status': 'error', 'mensaje': str(e)}), 500