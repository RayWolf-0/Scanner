from flask import Blueprint, jsonify, request, send_file
from models import db, Documento, EstadoDocumento, Usuario
from sqlalchemy import text
import os

supervisor_bp = Blueprint('supervisor', __name__, url_prefix='/api/supervisor')


@supervisor_bp.route('/documentos', methods=['GET'])
def listar_documentos():
    """Lista todos los documentos escaneados para revisión del supervisor."""
    try:
        query = """
            SELECT d.id_documento, d.fecha_creacion, d.ruta_pdf_final, 
                   e.nombre_estado, u.nombre, u.apellido
            FROM DOCUMENTO d
            JOIN ESTADO_DOCUMENTO e ON d.id_estado = e.id_estado
            JOIN USUARIO u ON d.id_vendedor = u.id_usuario
            ORDER BY d.fecha_creacion DESC
        """
        with db.engine.connect() as conn:
            resultado = conn.execute(text(query)).fetchall()

        documentos = []
        for row in resultado:
            documentos.append({
                "id_documento": row[0],
                "fecha_creacion": row[1],
                "ruta_pdf": row[2],
                "estado": row[3],
                "vendedor": f"{row[4]} {row[5]}"
            })

        return jsonify({"status": "success", "documentos": documentos}), 200

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@supervisor_bp.route('/documentos/<int:id_documento>/estado', methods=['PUT'])
def cambiar_estado_documento(id_documento):
    """Permite al supervisor aprobar, rechazar o cambiar el estado de un documento."""
    datos = request.json or {}
    nuevo_estado_nombre = datos.get('estado') # Ej: 'APROBADO', 'RECHAZADO'

    if not nuevo_estado_nombre:
        return jsonify({"error": "Debe especificar el nuevo estado"}), 400

    try:
        estado_obj = EstadoDocumento.query.filter_by(nombre_estado=nuevo_estado_nombre.upper()).first()
        if not estado_obj:
            return jsonify({"error": "El estado especificado no es válido"}), 400

        doc = Documento.query.get(id_documento)
        if not doc:
            return jsonify({"error": "Documento no encontrado"}), 404

        doc.id_estado = estado_obj.id_estado
        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Documento {id_documento} actualizado a {nuevo_estado_nombre.upper()}"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@supervisor_bp.route('/documentos/<int:id_documento>/pdf', methods=['GET'])
def descargar_pdf_final(id_documento):
    """Permite descargar el PDF generado y procesado."""
    try:
        doc = Documento.query.get(id_documento)
        if not doc or not doc.ruta_pdf_final or not os.path.exists(doc.ruta_pdf_final):
            return jsonify({"error": "PDF no encontrado para este documento"}), 404

        return send_file(doc.ruta_pdf_final, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500