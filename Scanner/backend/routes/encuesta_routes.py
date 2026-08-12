from flask import Blueprint, request, jsonify, send_file
import pandas as pd
from io import BytesIO
from sqlalchemy import text
from models import db

# Librerías para generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

encuesta_bp = Blueprint('encuesta_bp', __name__)

# listar encuestas
@encuesta_bp.route('/api/encuesta/listar', methods=['GET'])
def listar_encuestas():
    try:
        with db.engine.connect() as conn:
            query = text("""
                SELECT 
                    e.*, 
                    u.user AS username,
                    u.nombre,
                    u.apellido,
                    d.*
                FROM encuesta e 
                LEFT JOIN USUARIO u ON e.id_usuario = u.id_usuario
                LEFT JOIN dato_extraido d ON e.id_encuesta = d.id
                ORDER BY e.id_encuesta DESC
            """)
            result = conn.execute(query).mappings().fetchall()
            encuestas = [dict(row) for row in result]
            return jsonify(encuestas), 200
    except Exception as e:
        print("Error en listar_encuestas:", str(e))
        return jsonify({'error': str(e)}), 500

# guardar encuesta
@encuesta_bp.route('/api/encuesta/guardar', methods=['POST'])
def guardar_encuesta():
    datos = request.get_json() or {}
    try:
        with db.engine.connect() as conn:
            query = text("""
                INSERT INTO encuesta (id_usuario, empresa, rut, encuestado, cargo, fecha, telefono, correo)
                VALUES (:id_usuario, :empresa, :rut, :encuestado, :cargo, :fecha, :telefono, :correo)
            """)
            result = conn.execute(query, {
                "id_usuario": datos.get('id_usuario'),
                "empresa": datos.get('empresa'),
                "rut": datos.get('rut'),
                "encuestado": datos.get('encuestado'),
                "cargo": datos.get('cargo'),
                "fecha": datos.get('fecha'),
                "telefono": datos.get('telefono'),
                "correo": datos.get('correo')
            })
            conn.commit()
            id_creado = result.lastrowid

        return jsonify({
            'status': 'success',
            'mensaje': 'Encuesta guardada con éxito',
            'id_encuesta': id_creado
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error en guardar_encuesta:", str(e))
        return jsonify({'error': str(e)}), 500


# editar encuesta
@encuesta_bp.route('/api/encuesta/actualizar/<int:id_encuesta>', methods=['PUT'])
def actualizar_encuesta(id_encuesta):
    datos = request.get_json() or {}
    try:
        with db.engine.connect() as conn:
            query = text("""
                UPDATE encuesta 
                SET empresa = :empresa, rut = :rut, encuestado = :encuestado, 
                    cargo = :cargo, fecha = :fecha, telefono = :telefono, correo = :correo
                WHERE id_encuesta = :id
            """)
            conn.execute(query, {
                "empresa": datos.get('empresa'),
                "rut": datos.get('rut'),
                "encuestado": datos.get('encuestado'),
                "cargo": datos.get('cargo'),
                "fecha": datos.get('fecha'),
                "telefono": datos.get('telefono'),
                "correo": datos.get('correo'),
                "id": id_encuesta
            })
            conn.commit()
            return jsonify({'status': 'success', 'mensaje': 'Encuesta actualizada con éxito'}), 200
    except Exception as e:
        db.session.rollback()
        print("Error en actualizar_encuesta:", str(e))
        return jsonify({'error': str(e)}), 500


# eliminar encuesta
@encuesta_bp.route('/api/encuesta/eliminar/<int:id_encuesta>', methods=['DELETE'])
def eliminar_encuesta(id_encuesta):
    try:
        with db.engine.connect() as conn:
            query = text("DELETE FROM encuesta WHERE id_encuesta = :id")
            conn.execute(query, {"id": id_encuesta})
            conn.commit()
            return jsonify({'status': 'success', 'mensaje': 'Encuesta eliminada correctamente'}), 200
    except Exception as e:
        db.session.rollback()
        print("Error en eliminar_encuesta:", str(e))
        return jsonify({'error': str(e)}), 500


# exportar a excel
@encuesta_bp.route('/api/encuesta/exportar/excel/<int:id_encuesta>', methods=['GET'])
def exportar_excel(id_encuesta):
    try:
        with db.engine.connect() as conn:
            query = text("SELECT * FROM encuesta WHERE id_encuesta = :id")
            result = conn.execute(query, {"id": id_encuesta}).mappings().fetchone()

            if not result:
                return jsonify({'error': 'Encuesta no encontrada'}), 404

            datos = {
                'Campo': ['ID Encuesta', 'Empresa', 'RUT', 'Encuestado', 'Cargo', 'Fecha', 'Teléfono', 'Correo'],
                'Valor': [
                    result['id_encuesta'], result['empresa'], result['rut'], 
                    result['encuestado'], result['cargo'], result['fecha'], 
                    result['telefono'], result['correo']
                ]
            }
            df = pd.DataFrame(datos)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Plantilla Maestra', startrow=2)
            workbook  = writer.book
            worksheet = writer.sheets['Plantilla Maestra']

            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'font_color': '#1A202C'
            })
            worksheet.write('A1', 'PLANTILLA MAESTRA DE ENCUESTA', title_format)
            worksheet.set_column('A:A', 22)
            worksheet.set_column('B:B', 35)

        output.seek(0)

        return send_file(
            output,
            download_name=f'Encuesta_Maestra_{id_encuesta}.xlsx',
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print("Error en exportar_excel:", str(e))
        return jsonify({'error': str(e)}), 500


# exportar a pdf
@encuesta_bp.route('/api/encuesta/exportar/pdf/<int:id_encuesta>', methods=['GET'])
def exportar_pdf(id_encuesta):
    try:
        with db.engine.connect() as conn:
            query = text("SELECT * FROM encuesta WHERE id_encuesta = :id")
            result = conn.execute(query, {"id": id_encuesta}).mappings().fetchone()

            if not result:
                return jsonify({'error': 'Encuesta no encontrada'}), 404

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E242D'),
            alignment=1, # Centrado
            spaceAfter=20
        )

        # Título del documento
        elements.append(Paragraph("<b>PLANTILLA MAESTRA DE ENCUESTA</b>", title_style))
        elements.append(Spacer(1, 10))

        # Formato de la Tabla
        table_data = [
            [Paragraph('<b>Campo</b>', styles['Normal']), Paragraph('<b>Detalle Registrado</b>', styles['Normal'])],
            ['ID Encuesta:', str(result['id_encuesta'])],
            ['Empresa:', str(result['empresa'] or '')],
            ['RUT:', str(result['rut'] or '')],
            ['Encuestado:', str(result['encuestado'] or '')],
            ['Cargo:', str(result['cargo'] or '')],
            ['Fecha de Registro:', str(result['fecha'] or '')],
            ['Teléfono:', str(result['telefono'] or '')],
            ['Correo Electrónico:', str(result['correo'] or '')],
        ]

        t = Table(table_data, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#2B323C')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(t)
        doc.build(elements)

        buffer.seek(0)
        return send_file(
            buffer,
            download_name=f'Encuesta_Maestra_{id_encuesta}.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )

    except Exception as e:
        print("Error en exportar_pdf:", str(e))
        return jsonify({'error': str(e)}), 500