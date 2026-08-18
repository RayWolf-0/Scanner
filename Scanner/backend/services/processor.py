import os
import cv2
import sqlite3
import numpy as np
from PIL import Image, ImageOps
from services.ocr_service import OCRService

Image.MAX_IMAGE_PIXELS = None

def auto_orientar_y_cargar(ruta_imagen):
    try:
        pil_img = Image.open(ruta_imagen)
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        img = cv2.imread(ruta_imagen)
    
    if img is None:
        return None
        
    h, w = img.shape[:2]
    if w > h:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def get_checkbox_crop(img, rect, border_crop_factor=0.25):
    x, y, w, h = rect
    w_pad = int(w * border_crop_factor)
    h_pad = int(h * border_crop_factor)
    
    if (w - 2 * w_pad) <= 0 or (h - 2 * h_pad) <= 0:
        return img[y:y+h, x:x+w]
        
    im_crop = img[y + h_pad : y + h - h_pad, x + w_pad : x + w - w_pad]
    return im_crop

def calcular_ratio_tinta(img, rect):
    x, y, w, h = rect
    crop = get_checkbox_crop(img, (x, y, w, h), border_crop_factor=0.25)
    if crop is None or crop.size == 0:
        return 0.0
        
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    nonzero_px_count = np.count_nonzero(thresh)
    total_px = thresh.shape[0] * thresh.shape[1]
    
    if total_px == 0:
        return 0.0
        
    return nonzero_px_count / total_px

def procesar_encuesta_hibrida(img_original, id_plantilla):
    print("[SCANNER] Iniciando extracción de texto...")
    datos_texto = OCRService.procesar_encuesta_completa(img_original)
    
    print("[SCANNER] Evaluando casillas con mapeo seguro por filas espaciales independientes...")
    
    h_img, w_img = img_original.shape[:2]
    w_master, h_master = 2479, 3508
    
    scale_x = w_img / w_master
    scale_y = h_img / h_master
    
    datos_checkboxes = {}
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'scanner.db') 
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nombre_campo, pos_x, pos_y, ancho, alto
            FROM CAMPO_PLANTILLA
            WHERE id_plantilla = ? AND tipo_dato = 'CHECKBOX'
            ORDER BY pos_y ASC, pos_x ASC
        """, (id_plantilla,))
        
        campos = cursor.fetchall()
        conn.close()
        
        elementos = []
        for nombre_campo, x, y, w, h in campos:
            rx = int(x * scale_x)
            ry = int(y * scale_y)
            rw = int(w * scale_x)
            rh = int(h * scale_y)
            
            ratio = calcular_ratio_tinta(img_original, (rx, ry, rw, rh))
            elementos.append({
                'nombre': nombre_campo,
                'x': rx,
                'y': ry,
                'ratio': ratio
            })
            
        filas = []
        tolerancia_y = int(30 * scale_y) 
        
        for el in sorted(elementos, key=lambda e: e['y']):
            colocado = False
            for fila in filas:
                # Comparamos con el primer elemento de la fila
                if abs(fila[0]['y'] - el['y']) <= tolerancia_y:
                    fila.append(el)
                    colocado = True
                    break
            if not colocado:
                filas.append([el])
                
        for fila in filas:
            fila.sort(key=lambda e: e['x']) # Ordenar de izquierda a derecha
            n = len(fila)
            
            if n == 4:
                # TABLAS
                max_ratio = max(e['ratio'] for e in fila)
                UMBRAL_LIKERT = 0.03
                
                if max_ratio >= UMBRAL_LIKERT:
                    idx_max = max(range(4), key=lambda idx: fila[idx]['ratio'])
                    for idx, e in enumerate(fila):
                        marcado = (idx == idx_max)
                        datos_checkboxes[e['nombre']] = marcado
                        if marcado:
                            print(f"[LIKERT FILA] {e['nombre']} marcado ({e['ratio']:.4f})")
                else:
                    for e in fila:
                        datos_checkboxes[e['nombre']] = False
                        
            elif n >= 5:
                # REDES SOCIALES
                UMBRAL_MULTI = 0.05
                for e in fila:
                    marcado = e['ratio'] >= UMBRAL_MULTI
                    datos_checkboxes[e['nombre']] = marcado
                    if marcado:
                        print(f"[REDES SOCIALES] {e['nombre']} marcado ({e['ratio']:.4f})")
                        
            elif n == 2:
                # CORREO INFORMATIVO
                max_ratio = max(e['ratio'] for e in fila)
                UMBRAL_BINARIO = 0.03
                
                if max_ratio >= UMBRAL_BINARIO:
                    idx_max = max(range(2), key=lambda idx: fila[idx]['ratio'])
                    for idx, e in enumerate(fila):
                        marcado = (idx == idx_max)
                        datos_checkboxes[e['nombre']] = marcado
                        if marcado:
                            print(f"[BINARIO] {e['nombre']} marcado ({e['ratio']:.4f})")
                else:
                    for e in fila:
                        datos_checkboxes[e['nombre']] = False
            else:
                # Casillas individuales sueltas
                for e in fila:
                    datos_checkboxes[e['nombre']] = e['ratio'] >= 0.04
            
    except Exception as e:
        print(f"[SCANNER ERROR] falló la extracción checkbox: {e}")
        
    resultado_final = {**datos_texto, **datos_checkboxes}
    print(f"[ANALISIS EXITOSO] Extracción finalizada correctamente.")
    return resultado_final