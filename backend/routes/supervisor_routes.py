#Route supervisor
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

from models import db, Usuario, Documento, EstadoDocumento, DatoExtraido
from services.image_service import ImageService
from services.ocr_service import OCRService
from services.pdf_service import PDFService

# supervisor
supervisor_bp = Blueprint('supervisor', __name__, url_prefix='/api/supervisor')

@supervisor_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticar al supervisor."""
    datos = request.json
    usuario_ingresado = datos.get('user')
    password_ingresada = datos.get('contrasena')
    
    # Buscar por mail o user para aceptar login con cualquiera de los dos
    usuario = Usuario.query.filter((Usuario.mail == usuario_ingresado) | (Usuario.user == usuario_ingresado)).first()
    
    # Valida credenciales
    if usuario and check_password_hash(usuario.contrasena, password_ingresada):
        # Aquí podrías añadir una validación extra para asegurar que usuario.id_rol sea el de SUPERVISOR
        return jsonify({
            'status': 'success', 
            'id_usuario': usuario.id_usuario,
            'nombre': f"{usuario.nombre} {usuario.apellido}",
            'rol': usuario.id_rol
        }), 200
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@supervisor_bp.route('/subir', methods=['POST'])
def subir_documento():
    """El supervisor también puede subir documentos actuando como vendedor."""
    if 'imagen' not in request.files:
        return jsonify({'error': 'No se envió ninguna imagen'}), 400
    
    id_usuario = request.form.get('id_usuario')
    if not id_usuario:
        return jsonify({'error': 'Falta el id_usuario en el formulario'}), 400

    archivo = request.files['imagen']
    if archivo.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400

    filename = secure_filename(archivo.filename)
    ruta_imagen = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    archivo.save(ruta_imagen)

    try:
        #procesamiento opencv
        img_alineada = ImageService.alinear_documento(ruta_imagen)
        
        #validacion tesseract
        es_valida = OCRService.validar_documento(img_alineada, 50, 50, 900, 100, "ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026")
        if not es_valida:
            os.remove(ruta_imagen)
            return jsonify({'error': 'La foto no parece ser la encuesta oficial'}), 400

        #extraccion datos
        casilla_siempre = ImageService.evaluar_checkbox(img_alineada, pos_x=100, pos_y=300, ancho=50, alto=50)
        rut_leido = OCRService.leer_texto_campo(img_alineada, pos_x=200, pos_y=150, ancho=300, alto=50)

        #recorte firma
        nombre_firma = f"firma_sup{id_usuario}_{filename}.png"
        ruta_firma = os.path.join(current_app.config['FIRMAS_FOLDER'], nombre_firma)
        ImageService.procesar_firma(img_alineada, pos_x=400, pos_y=1000, ancho=300, alto=150, ruta_destino_png=ruta_firma)

        #generar pdf
        plantilla_pdf = os.path.join(current_app.config['STORAGE_FOLDER'], 'plantilla', 'maestra.pdf')
        ruta_pdf_generado = os.path.join(current_app.config['PDFS_FOLDER'], f"final_{filename}.pdf")
        
        if os.path.exists(plantilla_pdf):
            datos_texto = {
                'rut_empresa': rut_leido,
                'chk_siempre': '/Yes' if casilla_siempre else '/Off'
            }
            datos_firma = {'ruta': ruta_firma, 'x': 400, 'y': 1000, 'w': 300, 'h': 150}
            PDFService.generar_pdf_final(plantilla_pdf, ruta_pdf_generado, datos_texto, datos_firma)
        else:
            ruta_pdf_generado = None

        #guardar en base de datos
        estado = EstadoDocumento.query.filter_by(nombre_estado='PENDIENTE').first()
        nuevo_doc = Documento(
            id_plantilla=1,
            id_vendedor=id_usuario, # El supervisor queda registrado como el creador
            id_estado=estado.id_estado,
            ruta_imagen=ruta_imagen,
            ruta_pdf_final=ruta_pdf_generado
        )
        db.session.add(nuevo_doc)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'id_documento': nuevo_doc.id_documento,
            'mensaje': 'Documento procesado correctamente por el supervisor',
            'datos_extraidos': {
                'rut_detectado': rut_leido,
                'casilla_siempre': casilla_siempre
            }
        }), 201

    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500

@supervisor_bp.route('/pendientes', methods=['GET'])
def obtener_pendientes():
    """Endpoint para listar todos los documentos que esperan revisión."""
    estado_pendiente = EstadoDocumento.query.filter_by(nombre_estado='PENDIENTE').first()
    
    if not estado_pendiente:
        return jsonify({'status': 'success', 'pendientes': []}), 200
        
    documentos = Documento.query.filter_by(id_estado=estado_pendiente.id_estado).all()
    
    resultado = []
    for doc in documentos:
        creador = Usuario.query.get(doc.id_vendedor)
        resultado.append({
            'id_documento': doc.id_documento,
            'creador': f"{creador.nombre} {creador.apellido}",
            'fecha': doc.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
            'ruta_pdf': doc.ruta_pdf_final
        })
        
    return jsonify({'status': 'success', 'pendientes': resultado}), 200

@supervisor_bp.route('/auditar/<int:id_documento>', methods=['PUT'])
def auditar_documento(id_documento):
    """Endpoint para aprobar o rechazar un documento y guardar correcciones."""
    datos = request.json
    nuevo_estado_nombre = datos.get('estado') # Debe enviar 'APROBADO' o 'RECHAZADO'
    id_supervisor = datos.get('id_supervisor')
    
    doc = Documento.query.get(id_documento)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404
        
    estado_nuevo = EstadoDocumento.query.filter_by(nombre_estado=nuevo_estado_nombre).first()
    if not estado_nuevo:
        return jsonify({'error': 'Estado no válido, use APROBADO o RECHAZADO'}), 400
        
    #Actualizar documento
    doc.id_estado = estado_nuevo.id_estado
    doc.id_supervisor = id_supervisor
    
    # correciones si lo requiere
    
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'mensaje': f'Documento {nuevo_estado_nombre.lower()} exitosamente'
    }), 200