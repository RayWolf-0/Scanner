import os
import time
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from models import db, Usuario, EstadoDocumento
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
        return jsonify({
            'status': 'success',
            'id_usuario': usuario.id_usuario,
            'nombre': f'{usuario.nombre} {usuario.apellido}',
            'rol': usuario.id_rol,
        }), 200

    return jsonify({'error': 'Credenciales incorrectas'}), 401


@vendedor_bp.route('/subir', methods=['POST'])
def subir_documento():
    """Endpoint principal para recibir la foto desde Postman y procesarla."""
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se ha enviado imagen'}), 400

    id_usuario = request.form.get('id_usuario')
    if not id_usuario:
        return jsonify({'error': 'Falta id_usuario'}), 400

    archivo = request.files['imagen']
    if archivo.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    # Asegurar directorios
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(current_app.config['FIRMAS_FOLDER'], exist_ok=True)
    os.makedirs(current_app.config['PDFS_FOLDER'], exist_ok=True)

    filename = secure_filename(archivo.filename)
    ruta_imagen = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    archivo.save(ruta_imagen)

    try:
        # Definición explícitamente declarada para evitar el NameError
        id_plantilla = 1

        estado_pendiente = EstadoDocumento.query.filter_by(
            nombre_estado='PENDIENTE'
        ).first()
        id_estado_val = estado_pendiente.id_estado if estado_pendiente else 1

        # Inserción segura con motor directo y liberación inmediata
        with db.engine.begin() as conn:
            resultado = conn.execute(
                db.text("""
                    INSERT INTO DOCUMENTO (id_plantilla, id_vendedor, id_estado, ruta_imagen, fecha_creacion)
                    VALUES (:id_plantilla, :id_vendedor, :id_estado, :ruta_imagen, CURRENT_TIMESTAMP)
                """),
                {
                    "id_plantilla": id_plantilla,
                    "id_vendedor": id_usuario,
                    "id_estado": id_estado_val,
                    "ruta_imagen": ruta_imagen
                }
            )
            doc_id = resultado.lastrowid

        # Ejecutar procesamiento con OpenCV + PaddleOCR
        procesar_documento_completo(id_documento=doc_id)

        # Generación del PDF compilado final
        nombre_pdf = f'final_{doc_id}_{int(time.time())}.pdf'
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
            db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
            
            PDFService.generar_pdf_final(
                id_documento=doc_id,
                id_plantilla=id_plantilla,
                db_path=db_path,
                ruta_plantilla=plantilla_pdf,
                ruta_salida=ruta_pdf_generado,
            )
            
            # Actualizar la ruta del PDF final mediante conexión segura
            with db.engine.begin() as conn:
                conn.execute(
                    db.text("UPDATE DOCUMENTO SET ruta_pdf_final = :ruta WHERE id_documento = :id"),
                    {"ruta": ruta_pdf_generado, "id": doc_id}
                )

        return jsonify({
            'status': 'success',
            'id_documento': doc_id,
            'mensaje': 'Documento procesado correctamente',
            'ruta_pdf': ruta_pdf_generado,
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500