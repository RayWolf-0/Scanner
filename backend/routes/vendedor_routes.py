#Route del vendedor con Blueprints para el login
from fileinput import filename
import os
from flask import Blueprint, jsonify, request, json, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import time

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
    
    # Crear carpetas si no existen
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(current_app.config['FIRMAS_FOLDER'], exist_ok=True)
    os.makedirs(current_app.config['PDFS_FOLDER'], exist_ok=True)
    
    #guardar imagen original
    filename = secure_filename(archivo.filename)
    ruta_imagen = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    archivo.save(ruta_imagen)
    try:
        #procesamiento opencv
        img_alineada = ImageService.alinear_documento(ruta_imagen)
        #validacion paddle
        if not OCRService.validar_documento(img_alineada):
            os.remove(ruta_imagen)  # Eliminar la imagen original si no es válida
            return jsonify({'error': 'Documento no válido'}), 400
        
        # Extracción de campos de texto según la estructura de la foto (1000x1400 px)
        datos_texto = {
            'nombre_empresa':    OCRService.leer_texto_campo(img_alineada, pos_x=310, pos_y=120, ancho=500, alto=25),
            'rut_empresa':       OCRService.leer_rut(img_alineada),
            'nombre_encuestado': OCRService.leer_texto_campo(img_alineada, pos_x=310, pos_y=170, ancho=500, alto=25),
            'cargo':             OCRService.leer_texto_campo(img_alineada, pos_x=310, pos_y=195, ancho=500, alto=25),
            'correo':            OCRService.leer_texto_campo(img_alineada, pos_x=310, pos_y=220, ancho=300, alto=25),
            'telefono':          OCRService.leer_texto_campo(img_alineada, pos_x=670, pos_y=220, ancho=200, alto=25),
            'fecha':             OCRService.leer_texto_campo(img_alineada, pos_x=310, pos_y=245, ancho=300, alto=25),
            'observaciones':     OCRService.leer_texto_campo(img_alineada, pos_x=120, pos_y=1120, ancho=750, alto=130)
        }
        #extraccion de casillas
        datos_casillas = {
            'serv_1_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=380),
            'serv_2_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=410),
            'serv_3_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=440),
            'prod_1_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=520),
            'prod_2_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=550),
            'prod_3_siempre': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=580),
            'rs_usa_fb': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=750),
            'rs_usa_li': ImageService.evaluar_checbox(img_alineada, pos_x=650, pos_y=750),
            'rs_sigue_fb': ImageService.evaluar_checbox(img_alineada, pos_x=570, pos_y=790),
            'rs_sigue_li': ImageService.evaluar_checbox(img_alineada, pos_x=650, pos_y=790),
        }
        
        #extraccion firma
        nombre_firma = f"firma_{id_usuario}_{int(time.time())}.png"
        ruta_firma = os.path.join(current_app.config['FIRMAS_FOLDER'], nombre_firma)
        ImageService.procesar_firma(img_alineada, ruta_destino_png=ruta_firma)
        
        #generacion pdf
        plantilla_pdf = os.path.join(current_app.config['STORAGE_FOLDER'], 'plantilla', 'maestra.pdf')
        nombre_pdf = f"final_{int(time.time())}_{filename}.pdf"
        ruta_pdf_generado = os.path.join(current_app.config['PDFS_FOLDER'], nombre_pdf)

        PDFService.generar_pdf_final(
            ruta_plantilla=plantilla_pdf,
            ruta_salida=ruta_pdf_generado,
            datos_texto=datos_texto,
            datos_casillas=datos_casillas,
            ruta_firma=ruta_firma
        )
        
        #guardar en base de datos
        estado = EstadoDocumento.query.filter_by(nombre_estado='PENDIENTE').first()
        nuevo_doc = Documento(
            id_plantilla=1,
            id_vendedor=id_usuario,
            id_estado=estado.id_estado if estado else 1,
            ruta_imagen=ruta_imagen,
            ruta_pdf_final=ruta_pdf_generado
        )
        db.session.add(nuevo_doc)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'id_documento': nuevo_doc.id_documento,
            'mensaje': 'Documento procesado correctamente',
            'ruta_pdf': ruta_pdf_generado
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'mensaje': str(e)}), 500
        