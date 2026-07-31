#Route del vendedor con Blueprints para el login
import os
from flask import Blueprint, jsonify, request, json, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from models import db, Usuario, Documento, EstadoDocumento, DatoExtraido
from services.ocr_service import OCRService
from services.pdf_service import PDFService
from services.image_service import ImageService

#para crear el usuario
vendedor_bp = Blueprint('vendedor', __name__, url_prefix='/api/vendedor')

@vendedor_bp.route('/login', methods=['POST'])
def login():
    #endpoint para la autentificacion del vendedor
    datos = request.json
    #extranccion datos user y contrasena
    usuario_ingresado = datos.get('user')
    password_ingresada = datos.get('contrasena')
    #buscar usuario en la base de datos (acepta mail o user)
    usuario = Usuario.query.filter((Usuario.mail == usuario_ingresado) | (Usuario.user == usuario_ingresado)).first()
    #comparación con hash y campo de la base de datos para la contraseña
    if usuario and check_password_hash(usuario.contrasena, password_ingresada):
        return jsonify({
            'status': 'success',
            'id_usuario': usuario.id_usuario,
            'nombre': f"{usuario.nombre} {usuario.apellido}",
            'rol': usuario.id_rol
        }), 200
    return jsonify({'error': 'Credenciales incorrectas'}), 401
 
@vendedor_bp.route('/subir', methods=['POST'])
def subir_documento():
    #endpoint para recibir la foto y procesarla 
    #validar datos
    if 'imagen' not in request.files:
        return jsonify({'error': 'no se ha enviado imagen'}), 400
    
    id_usuario = request.form.get('id_usuario')
    if not id_usuario:
        return jsonify({'error': 'falta id_usuario'}), 400
    
    archivo = request.files['imagen']
    if archivo.filename == '':
        return jsonify({'error': 'archivo vacio'})
    
    #guardar imagen original
    filename = secure_filename(archivo.filename)
    ruta_imagen = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    archivo.save(ruta_imagen)
    try:
        #procesamiento opencv
        img_alineada = ImageService.alinear_documento(ruta_imagen)
        #validacion tesseract
        es_valida = OCRService.validar_documento(img_alineada)
        if not es_valida:
            os.remove(ruta_imagen)
            return jsonify({'error': 'la foto no pertenece a la encuesta oficial'}), 400
        
        #extraccion datos
        casilla_siempre = ImageService.evaluar_checbox(img_alineada, pos_x=100, pos_y=300, ancho=50, alto=50)
        rut_leido = OCRService.leer_rut(img_alineada)

        # fallback si no encuentra RUT por OCR completo
        if not rut_leido:
            rut_leido = OCRService.leer_texto_campo(img_alineada, pos_x=200, pos_y=150, ancho=300, alto=50)

        #recorte firma
        nombre_firma = f"firma_vend{id_usuario}_{filename}.png"
        ruta_firma = os.path.join(current_app.config['FIRMAS_FOLDER'], nombre_firma)
        ImageService.procesar_firma(img_alineada, ruta_destino_png=ruta_firma)
        
        #generar pdf
        plantilla_pdf = os.path.join(current_app.config['STORAGE_FOLDER'], 'plantilla', 'maestra.pdf')
        ruta_pdf_generado = os.path.join(current_app.config['PDFS_FOLDER'], f"final_{filename}.pdf")
        if os.path.exists(plantilla_pdf):
            campos_posiciones = {
                'rut_empresa': {'x': 200, 'y': 150, 'width': 300, 'height': 50},
                'chk_siempre': {'x': 100, 'y': 300, 'width': 50, 'height': 50}
            }
            datos_texto = {
                'rut_empresa': rut_leido,
                'chk_siempre': '/Yes' if casilla_siempre else '/Off'
            }
            datos_firma = {'ruta': ruta_firma, 'x':400, 'y':1000, 'w':300, 'h':150}
            PDFService.generar_pdf_final(
                plantilla_pdf,
                ruta_pdf_generado,
                datos_texto,
                datos_firma,
                ruta_imagen=ruta_imagen,
                campos_posiciones=campos_posiciones,
                imagen_tamano=(1000, 1400)
            )
        else:
            ruta_pdf_generado = None
            
        #guardar en base de datos
        estado = EstadoDocumento.query.filter_by(nombre_estado='PENDIENTE').first()
        nuevo_doc = Documento(
            id_plantilla=1,
            id_vendedor=id_usuario,
            id_estado=estado.id_estado,
            ruta_imagen=ruta_imagen,
            ruta_pdf_final=ruta_pdf_generado
        )
        db.session.add(nuevo_doc)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'id_dicumento': nuevo_doc.id_documento,
            'mensaje': 'Documento procesao correctamente',
            'datos_extraidos': {
                'rut_detectado': rut_leido,
                'casilla_siempre': casilla_siempre
            }
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e) })
        