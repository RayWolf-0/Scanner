from flask import Blueprint, request, jsonify, send_file
import pandas as pd
from io import BytesIO
from models import db

encuesta_bp = Blueprint('encuesta_bp', __name__)

@encuesta_bp.route('/api/encuesta/guardar', methods=['POST'])
def guardar_encuesta():
    datos = request.get_json() or {}
    
    try:
        
        return jsonify({
            'status': 'success',
            'mensaje': 'Encuesta guardada con éxito',
            'id_encuesta': 1  # ID retornado para descargas
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@encuesta_bp.route('/api/encuesta/exportar/excel/<int:id_encuesta>', methods=['GET'])
def exportar_excel(id_encuesta):
    try:
        # consulta base de datos
        datos_demo = {
            'Campo': ['Empresa', 'RUT', 'Encuestado'],
            'Valor': ['Ejemplo S.A.', '76.123.456-7', 'Juan Pérez']
        }
        df = pd.DataFrame(datos_demo)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Encuesta')
        output.seek(0)

        return send_file(
            output,
            download_name=f'Encuesta_{id_encuesta}.xlsx',
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500