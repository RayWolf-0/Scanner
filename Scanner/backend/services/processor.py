import os
import cv2
import sqlite3
import numpy as np
import re
from PIL import Image, ImageOps
from services.ocr_service import OCRService
import traceback

Image.MAX_IMAGE_PIXELS = None
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PLANTILLA_IMG = os.path.join(BASE_DIR, 'storage', 'plantilla', 'maestra_referencia.png')
DEBUG_DIR = os.path.join(BASE_DIR, 'storage')

#busca la planilla y obtiene sus dimensiones para ajustar la imagen recibida a ella
def _obtener_dimensiones_plantilla():
    if os.path.exists(RUTA_PLANTILLA_IMG):
        img = cv2.imread(RUTA_PLANTILLA_IMG)
        if img is not None:
            h, w = img.shape[:2]
            return w, h
    return 2551, 3301

def _asegurar_portrait(img):
    h, w = img.shape[:2]
    if w > h:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img

def corregir_orientacion_desde_bytes(raw_bytes):
    try:
        from io import BytesIO
        pil_img = Image.open(BytesIO(raw_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_BAYER_BG2BGR)
    except Exception as e:
        print(f"[ORIENTACIÓN] no se pudo leer desde bytes: {e}")
        nparr = np.frombuffer(raw_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
    if img is None:
        return None
    
    return _asegurar_portrait(img)

def auto_orientar_y_cargar(ruta_imagen):
    try:
        pil_img = Image.open(ruta_imagen)
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"advertencia al leer exif: {e}")
        img = cv2.imread(ruta_imagen)
        
    if img is None:
        return None
    
    return _asegurar_portrait(img)

#busca coincidencias por secciones (capas) antes de alinearla
def _alinear_por_capas(img_original, guardar_debug=False):
    if not os.path.exists(RUTA_PLANTILLA_IMG):
        print("[ALINEACION] no se encontró la planilla de referencia")
        return None
    
    img_plantilla = cv2.imread(RUTA_PLANTILLA_IMG, cv2.IMREAD_GRAYSCALE)
    if img_plantilla is None:
        return None
    
    h_dest, w_dest = img_plantilla.shape[:2]
    gray_foto = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray_foto = clahe.apply(gray_foto)
    
    SCALE_H = 1200 
    ratio_plantilla = SCALE_H / float(h_dest)
    plantilla_small = cv2.resize(img_plantilla, None, fx=ratio_plantilla, fy=ratio_plantilla)
    
    ratio_foto = SCALE_H / float(gray_foto.shape[0])
    foto_small = cv2.resize(gray_foto, None, fx=ratio_foto, fy=ratio_foto)
    
    orb = cv2.ORB_create(nfeatures=5000, scaleFactor=1.2, nlevels=8,
                         edgeThreshold=15, patchSize=31)
    
    kp1, des1 = orb.detectAndCompute(foto_small, None)
    kp2, des2 = orb.detectAndCompute(plantilla_small, None)
    
    if des1 is None or des2 is None:
        print("[ALINEACION] no se detectaron suficientes features")
        return None
    
    if len(kp1) < 10 or len(kp2) < 110:
        print(f"[ALINEACION] features insuficientes: foto={len(kp1)}, plantilla={len(kp2)}")
        return None
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches_raw = bf.knnMatch(des1, des2, k=2)
    
    buenas = []
    for pair in matches_raw:
        if len(pair) == 2:
            m, n = pair
            if m.distance < 0.75 * n.distance:
                buenas.append(m)
                
    print(f"[ALINEACION] feature matching: {len(buenas)} matches buenos de {len(matches_raw)} totales")
    
    MIN_MATCHES = 15
    if len(buenas) < MIN_MATCHES:
        print(f"[ALINEACION]: insuficientes matches ({len(buenas)} < {MIN_MATCHES}), features matching descartado")
        return None
    
    pts_foto = np.float32([kp1[m.queryIdx].pt for m in buenas]).reshape(-1, 1, 2)
    pts_plantilla = np.float32([kp2[m.trainIdx].pt for m in buenas]).reshape(-1, 1, 2)

    pts_foto /= ratio_foto
    pts_plantilla /= ratio_plantilla

    H, mask = cv2.findHomography(pts_foto, pts_plantilla, cv2.RANSAC, 5.0)

    if H is None:
        print("[ALINEACION] No se pudo calcular la homografía.")
        return None

    inliers = int(mask.sum()) if mask is not None else 0
    print(f"[ALINEACION] Homografía calculada: {inliers} inliers de {len(buenas)} matches")

    if inliers < 10:
        print(f"[ALINEACION] Pocos inliers ({inliers}), homografía poco confiable.")
        return None
    
    h_orig, w_orig = img_original.shape[:2]
    MAX_WARP_DIM = 4000
    if max(h_orig, w_orig) > MAX_WARP_DIM:
        scale_down = MAX_WARP_DIM / float(max(h_orig, w_orig))
        img_to_warp = cv2.resize(img_original, None, fx=scale_down, fy=scale_down)
        S = np.array([[scale_down, 0, 0], [0, scale_down, 0], [0, 0, 1]], dtype=np.float64)
        H_adjusted = H @ np.linalg.inv(S)
        warped = cv2.warpPerspective(img_to_warp, H_adjusted, (w_dest, h_dest))
        print(f"[ALINEACION] Imagen pre-escalada de {w_orig}x{h_orig} a {img_to_warp.shape[1]}x{img_to_warp.shape[0]} antes del warp")
    else:
        warped = cv2.warpPerspective(img_original, H, (w_dest, h_dest))

    if guardar_debug:
        try:
            debug_path = os.path.join(DEBUG_DIR, 'debug_feature_matches.jpg')
            foto_small_bgr = cv2.cvtColor(foto_small, cv2.COLOR_GRAY2BGR)
            plantilla_small_bgr = cv2.cvtColor(plantilla_small, cv2.COLOR_GRAY2BGR)
            
            if mask is not None:
                matches_mask = mask.ravel().tolist()
            else:
                matches_mask = None
                
            img_matches = cv2.drawMatches(
                foto_small_bgr, kp1, plantilla_small_bgr, kp2,
                buenas, None,
                matchColor=(0, 255, 0),
                singlePointColor=(255, 0, 0),
                matchesMask=matches_mask,
                flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
            )
            cv2.imwrite(debug_path, img_matches)
            print(f"[DEBUG] Feature matches guardados en {debug_path}")
        except Exception as e:
            print(f"[DEBUG] Error guardando debug de matches: {e}")

    return warped

#antes de procesar la alineacion, toma la fotografía y busca los contornos del papel
def _alinear_por_contorno(img_original, guardar_debug=False):
    w_dest, h_dest = _obtener_dimensiones_plantilla()

    #devuelto a 800 para estabilizar la deteccion de bordes en papeles blancos
    RESOLUTION_BASE = 800.0
    ratio = img_original.shape[0] / RESOLUTION_BASE
    orig = img_original.copy()
    image_resized = cv2.resize(img_original, (int(img_original.shape[1] / ratio), int(RESOLUTION_BASE)))
    area_total = image_resized.shape[0] * image_resized.shape[1]

    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 30, 150)
    
    kernel = np.ones((5, 5), np.uint8)
    edged = cv2.dilate(edged, kernel, iterations=2)
    edged = cv2.erode(edged, kernel, iterations=1)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    screenCnt = None
    if cnts:
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        for c in cnts:
            area = cv2.contourArea(c)
            if area < area_total * 0.2:
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if len(approx) == 4:
                rect = cv2.boundingRect(approx)
                aspect_ratio = rect[3] / float(rect[2]) 
                if aspect_ratio > 0.8: 
                    screenCnt = approx.reshape(4, 2).astype("float32")
                    print(f"[ALINEACION] Contorno cuadrilátero detectado: area={area:.0f}, aspect={aspect_ratio:.2f}")
                    break

        if screenCnt is None and cnts:
            c = cnts[0]
            area = cv2.contourArea(c)
            if area > area_total * 0.2:
                rect_min = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect_min)
                screenCnt = box.astype("float32")
                print(f"[ALINEACION] Usando minAreaRect como fallback, area={area:.0f}")

    if screenCnt is None:
        print("[ALINEACION] No se detectaron bordes confiables del documento.")
        return None

    pts = screenCnt * ratio
    rect = _order_points(pts)

    widthA = np.linalg.norm(rect[2] - rect[3])
    widthB = np.linalg.norm(rect[1] - rect[0])
    heightA = np.linalg.norm(rect[1] - rect[2])
    heightB = np.linalg.norm(rect[0] - rect[3])
    
    avg_width = (widthA + widthB) / 2
    avg_height = (heightA + heightB) / 2
    
    if avg_height < avg_width:
        print("[ALINEACION] Contorno parece landscape, no portrait. Descartando.")
        return None

    dst = np.array([
        [0, 0],
        [w_dest - 1, 0],
        [w_dest - 1, h_dest - 1],
        [0, h_dest - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (w_dest, h_dest))

    if guardar_debug:
        try:
            debug_img = image_resized.copy()
            cv2.drawContours(debug_img, [screenCnt.astype(int)], -1, (0, 255, 0), 3)
            cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_contorno.jpg'), debug_img)
        except Exception:
            pass

    return warped

def _alinear_simple_resize(img_original):
    w_dest, h_dest = _obtener_dimensiones_plantilla()
    print("[ALINEACION] Usando resize directo como último recurso.")
    return cv2.resize(img_original, (w_dest, h_dest), interpolation=cv2.INTER_AREA)

def _order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def alinear_imagen(img_original, guardar_debug=True):
    print("[ALINEACION] Intentando alineación por detección de contorno...")
    resultado = _alinear_por_contorno(img_original, guardar_debug=guardar_debug)
    if resultado is not None:
        print("[ALINEACION] [OK] Deteccion de contorno exitosa.")
        if guardar_debug:
            try:
                cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_alineada.jpg'), resultado)
            except Exception:
                pass
        return resultado

    print("[ALINEACION] Intentando alineación por feature matching (ORB/SIFT)...")
    resultado = _alinear_por_capas(img_original, guardar_debug=guardar_debug)
    if resultado is not None:
        print("[ALINEACION] [OK] Feature matching exitoso.")
        if guardar_debug:
            try:
                cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_alineada.jpg'), resultado)
            except Exception:
                pass
        return resultado

    resultado = _alinear_simple_resize(img_original)
    if guardar_debug:
        try:
            cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_alineada.jpg'), resultado)
        except Exception:
            pass
    return resultado

#recorta la foto en 4 secciones para un mejor analizis de cada uno
def recortar_y_guardar_roi(warped_img, y1_pct, y2_pct, x1_pct, x2_pct, nombre_archivo):
    directorio_destino = os.path.join(DEBUG_DIR, 'rois')
    os.makedirs(directorio_destino, exist_ok=True)
    
    h, w = warped_img.shape[:2]
    y1 = int(h * y1_pct)
    y2 = int(h * y2_pct)
    x1 = int(w * x1_pct)
    x2 = int(w * x2_pct)
    
    roi = warped_img[y1:y2, x1:x2]
    
    ruta_completa = os.path.join(directorio_destino, f"{nombre_archivo}.jpg")
    cv2.imwrite(ruta_completa, roi)
    
    print(f"[ROI] Recorte {nombre_archivo} guardado en {ruta_completa}")
    return roi

#crea un lienzo blanco y pega solo las zonas de texto para aislar el OCR
def _crear_lienzo_texto(img_alineada):
    lienzo = img_alineada.copy()
    lienzo[:] = 255
    
    h, w = img_alineada.shape[:2]
    
    # cabezal (0% a 25%)
    y2_cab = int(h * 0.25)
    lienzo[0:y2_cab, 0:w] = img_alineada[0:y2_cab, 0:w]
    
    # observaciones (77% a 100%)
    y1_obs = int(h * 0.77)
    lienzo[y1_obs:h, 0:w] = img_alineada[y1_obs:h, 0:w]
    
    return lienzo

#elimina la basura visual de los textos
def limpiar_datos_texto(datos_texto):
    datos_limpios = {}
    for key, value in datos_texto.items():
        if value is None:
            datos_limpios[key] = ""
            continue
            
        texto_str = str(value).strip()
        
        if key == 'fecha':
            texto_limpio = re.sub(r'[lI|/\\_.]', '-', texto_str).replace(' ', '')
            match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', texto_limpio)
            if match:
                dia, mes, anio = match.groups()
                if len(anio) == 2:
                    anio = f"20{anio}"
                datos_limpios[key] = f"{anio}-{mes.zfill(2)}-{dia.zfill(2)}"
            else:
                datos_limpios[key] = ""
        else:
            datos_limpios[key] = texto_str.upper()
            
    return datos_limpios

#evalúa cada checkbox para dibujar un mapa acorde a la cantidad de tinta 
def evaluar_checkbox_preciso(roi):
    if roi is None or roi.size == 0:
        return False

    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape

    m_h, m_w = int(h * 0.25), int(w * 0.35)
    centro = gris[m_h: h - m_h, m_w: w - m_w]

    if centro.size == 0:
        return False

    blur = cv2.GaussianBlur(centro, (5, 5), 0)

    block_size = max(15, (min(blur.shape) // 2) * 2 + 1)
    thresh = cv2.adaptiveThreshold(
        blur, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        block_size, 
        20
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh_limpio = cv2.erode(thresh, kernel, iterations=1)

    pixeles_tinta = cv2.countNonZero(thresh_limpio)
    porcentaje = (pixeles_tinta / float(centro.size)) * 100.0

    if 1.5 < porcentaje < 50.0:
        return True

    return False

#procesa la imagen usando PaddleOCR y OpenCv (extracción de texto y análisis de imagen)
def procesar_encuesta_hibrida(img_original, id_plantilla, raw_bytes=None):
    from services.predictor_service import MotorCorreccion
    
    try:
        if raw_bytes is not None:
            img_corregida = corregir_orientacion_desde_bytes(raw_bytes)
            if img_corregida is not None:
                img_original = img_corregida
        else:
            img_original = _asegurar_portrait(img_original)

        print("[SCANNER] Alineando imagen...")
        img_alineada = alinear_imagen(img_original, guardar_debug=True)
        
        datos_texto = {}
        datos_checkboxes = {}

        if img_alineada is None:
            print("[SCANNER ERROR] No se pudo alinear la imagen. Abortando recortes.")
            datos_texto["alineacion_fallida"] = True
        else:
            print("[SCANNER] Generando recortes por secciones (ROIs) en storage...")
            recortar_y_guardar_roi(img_alineada, 0.03, 0.25, 0.0, 1.0, "01_cabezal")
            recortar_y_guardar_roi(img_alineada, 0.25, 0.62, 0.0, 1.0, "02_evaluaciones")
            recortar_y_guardar_roi(img_alineada, 0.62, 0.77, 0.0, 1.0, "03_redes_sociales")
            recortar_y_guardar_roi(img_alineada, 0.77, 0.98, 0.0, 1.0, "04_observaciones")

            print("[SCANNER] Aislando zonas de texto en lienzo para forzar precision de PaddleOCR...")
            lienzo_ocr = _crear_lienzo_texto(img_alineada)
            
            try:
                cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_lienzo_ocr.jpg'), lienzo_ocr)
            except Exception:
                pass

            print("[SCANNER] Iniciando extracción de texto sobre lienzo limpio...")
            datos_texto_bruto = OCRService.procesar_encuesta_completa(lienzo_ocr)
            
            #limpia el texto extraido
            datos_texto_limpios = limpiar_datos_texto(datos_texto_bruto)
            
            #aplica el predictor y corrector al texto limpio
            motor = MotorCorreccion()
            datos_texto = motor.limpiar_y_predecir(datos_texto_limpios)

            print("[SCANNER] Buscando Checkboxes en imagen alineada...")
            try:
                db_path = os.path.join(BASE_DIR, 'instance', 'scanner.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT nombre_campo, pos_x, pos_y, ancho, alto
                    FROM CAMPO_PLANTILLA
                    WHERE id_plantilla = ? AND tipo_dato = 'CHECKBOX'
                      AND ancho > 0 AND alto > 0
                """, (id_plantilla,))

                campos = cursor.fetchall()
                debug_overlay = img_alineada.copy()

                for nombre_campo, x, y, w, h in campos:
                    x, y, w, h = int(x), int(y), int(w), int(h)
                    
                    img_h, img_w = img_alineada.shape[:2]
                    if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
                        print(f"[CHECKBOX] {nombre_campo} fuera de límites: ({x},{y},{w},{h}) imagen=({img_w},{img_h})")
                        continue

                    roi = img_alineada[y: y + h, x: x + w]
                    marcado = evaluar_checkbox_preciso(roi)
                    datos_checkboxes[nombre_campo] = marcado

                    color = (0, 255, 0) if marcado else (0, 0, 255)
                    cv2.rectangle(debug_overlay, (x, y), (x + w, y + h), color, 3)
                    etiqueta = nombre_campo.replace("Casilla ", "C")
                    cv2.putText(debug_overlay, f"{etiqueta}:{'SI' if marcado else 'NO'}",
                               (x, max(0, y - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                               0.6, color, 2, cv2.LINE_AA)

                try:
                    debug_path = os.path.join(DEBUG_DIR, 'debug_mapa_marcas.jpg')
                    cv2.imwrite(debug_path, debug_overlay)
                    print(f"[DEBUG] Mapa de marcas guardado en {debug_path}")
                except Exception:
                    pass

                conn.close()

            except Exception as e:
                print(f"[SCANNER ERROR] Falló la extracción checkbox: {e}")
                traceback.print_exc()

        resultado_final = {**datos_texto, **datos_checkboxes}
        print(f"[ANALISIS EXITOSO] Datos correctamente extraidos: {list(resultado_final.keys())}")
        return resultado_final
        
    except Exception as e:
        print("\n" + "="*60)
        print("[ERROR CRÍTICO] El servidor backend colapsó durante el escaneo:")
        traceback.print_exc()
        print("="*60 + "\n")
        raise e