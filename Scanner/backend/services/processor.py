import os
import cv2
import sqlite3
import numpy as np
from PIL import Image, ImageOps
from sqlalchemy import text
from models import db
from services.ocr_service import OCRService

# Desactivar límite de pixeles
Image.MAX_IMAGE_PIXELS = None

def auto_orientar_y_cargar(ruta_imagen):
    try:
        pil_img = Image.open(ruta_imagen)
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Advertencia al leer EXIF: {e}")
        img = cv2.imread(ruta_imagen)
    
    if img is None:
        return None
        
    h, w = img.shape[:2]
    if w > h:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


    
def alinear_por_caracteristicas(img_original):

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_plantilla_img = os.path.join(base_dir, 'storage', 'plantilla', 'maestra_referencia.png')
    
    # Dimensiones estándar
    h_dest, w_dest = 3508, 2479
    
    if os.path.exists(ruta_plantilla_img):
        img_plantilla = cv2.imread(ruta_plantilla_img)
        if img_plantilla is not None:
            h_dest, w_dest = img_plantilla.shape[:2]

    # Redimensionar foto
    img_alineada = cv2.resize(img_original, (w_dest, h_dest))
    
    return img_alineada


def evaluar_checkbox_preciso(roi):
    if roi is None or roi.size == 0:
        return False
        
    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape
    
    # Recorte interior para evitar los bordes del checkbox
    m_h, m_w = int(h * 0.40), int(w * 0.40)
    centro = gris[m_h: h - m_h, m_w: w - m_w]
    
    if centro.size == 0:
        return False
        
    std_dev = cv2.meanStdDev(centro)[1][0][0]
    
    # Si la casilla está completamente limpia o sin contraste
    if std_dev < 8.0:
        return False
        
    _, thresh = cv2.threshold(centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pixeles_tinta = cv2.countNonZero(thresh)
    porcentaje = (pixeles_tinta / float(centro.size)) * 100.0
    
    if porcentaje > 3.0 and porcentaje < 35.0:
        return True
        
    return False

def procesar_encuesta_hibrida(img_original, id_plantilla):
    # Motor hibrido, PaddleOCR y OPENCV, uno escanea la hoja y el otro recorta para retornar un JSON
    
    # Paddle y Regex comienzan
    print("[SCANNER] Iniciando extracción de texto...")
    datos_texto = OCRService.procesar_encuesta_completa(img_original)
    
    # OpenCV junto a las Coordenadas
    print("[SCANNER] Alineando imagen y buscando Checkboxes...")
    img_alineada = alinear_por_caracteristicas(img_original)
    datos_checkboxes = {}
    
    # Consulta SQL por los checkboxes usando SQLite nativo
    try:
        # 1. Buscamos la ruta absoluta de tu base de datos
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'scanner.db') 
        
        # conectar base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nombre_campo, pos_x, pos_y, ancho, alto
            FROM CAMPO_PLANTILLA
            WHERE id_plantilla = ? AND tipo_dato = 'CHECKBOX'
        """, (id_plantilla,))
        
        campos = cursor.fetchall()
        
        for nombre_campo, x, y, w, h in campos:
            x, y, w, h = int(x), int(y), int(w), int(h)
            roi = img_alineada[y: y+h, x: x+w]
            marcado = evaluar_checkbox_preciso(roi)
            datos_checkboxes[nombre_campo] = marcado
            
        conn.close()
                    
    except Exception as e:
        print(f"[SCANNER ERROR] falló la extracción checkbox: {e}")
        
    resultado_final = {**datos_texto, **datos_checkboxes}
    print(f"[ANALISIS EXITOSO] Datos correctamente extraidos: {resultado_final}")
    return resultado_final

