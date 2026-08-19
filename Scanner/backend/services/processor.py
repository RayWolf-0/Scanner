import os
import cv2
import sqlite3
import numpy as np
from PIL import Image, ImageOps

# Desactivar límite de pixeles
Image.MAX_IMAGE_PIXELS = None

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PLANTILLA_IMG = os.path.join(BASE_DIR, 'storage', 'plantilla', 'maestra_referencia.png')
DEBUG_DIR = os.path.join(BASE_DIR, 'storage')


def _obtener_dimensiones_plantilla():
    """Lee las dimensiones reales de la imagen de referencia."""
    if os.path.exists(RUTA_PLANTILLA_IMG):
        img = cv2.imread(RUTA_PLANTILLA_IMG)
        if img is not None:
            h, w = img.shape[:2]
            return w, h
    return 2551, 3301  # fallback a las dimensiones de la BD


def _asegurar_portrait(img):
    """Si la imagen viene en landscape (más ancha que alta), rotarla a portrait."""
    h, w = img.shape[:2]
    if w > h:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def corregir_orientacion_desde_bytes(raw_bytes):
    """
    Intenta corregir la orientación EXIF desde los bytes crudos de la imagen.
    Retorna el array numpy BGR ya corregido.
    """
    try:
        from io import BytesIO
        pil_img = Image.open(BytesIO(raw_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"[ORIENTACION] No se pudo leer EXIF desde bytes: {e}")
        nparr = np.frombuffer(raw_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    return _asegurar_portrait(img)


def auto_orientar_y_cargar(ruta_imagen):
    """Carga una imagen desde ruta corrigiendo EXIF. Compatibilidad con código existente."""
    try:
        pil_img = Image.open(ruta_imagen)
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Advertencia al leer EXIF: {e}")
        img = cv2.imread(ruta_imagen)

    if img is None:
        return None

    return _asegurar_portrait(img)


# ──────────────────────────────────────────────
# ALINEACIÓN — Estrategia por capas
# ──────────────────────────────────────────────

def _alinear_por_feature_matching(img_original, guardar_debug=False):
    """
    ETAPA 1: Feature matching con ORB contra la plantilla de referencia.
    Es el método más robusto: funciona con fondos blancos, sombras, perspectiva.
    Usa keypoints + homografía RANSAC.
    """
    if not os.path.exists(RUTA_PLANTILLA_IMG):
        print("[ALINEACION] No se encontró la plantilla de referencia para feature matching.")
        return None

    img_plantilla = cv2.imread(RUTA_PLANTILLA_IMG, cv2.IMREAD_GRAYSCALE)
    if img_plantilla is None:
        return None

    h_dest, w_dest = img_plantilla.shape[:2]

    # Convertir la foto a escala de grises
    gray_foto = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)

    # Trabajar a resolución reducida para ORB (más rápido, pero conservando suficientes features)
    # Escalar ambas al mismo tamaño proporcional para que ORB funcione bien
    SCALE_H = 1200  # Altura de trabajo para feature matching (consume poca RAM)
    
    ratio_plantilla = SCALE_H / float(h_dest)
    plantilla_small = cv2.resize(img_plantilla, None, fx=ratio_plantilla, fy=ratio_plantilla)
    
    ratio_foto = SCALE_H / float(gray_foto.shape[0])
    foto_small = cv2.resize(gray_foto, None, fx=ratio_foto, fy=ratio_foto)

    # Crear detector ORB
    orb = cv2.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=8,
                         edgeThreshold=15, patchSize=31)

    kp1, des1 = orb.detectAndCompute(foto_small, None)
    kp2, des2 = orb.detectAndCompute(plantilla_small, None)

    if des1 is None or des2 is None:
        print("[ALINEACION] No se detectaron suficientes features.")
        return None

    if len(kp1) < 10 or len(kp2) < 10:
        print(f"[ALINEACION] Features insuficientes: foto={len(kp1)}, plantilla={len(kp2)}")
        return None

    # Matching con BFMatcher + ratio test de Lowe
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches_raw = bf.knnMatch(des1, des2, k=2)

    # Aplicar ratio test
    buenas = []
    for pair in matches_raw:
        if len(pair) == 2:
            m, n = pair
            if m.distance < 0.75 * n.distance:
                buenas.append(m)

    print(f"[ALINEACION] Feature matching: {len(buenas)} matches buenos de {len(matches_raw)} totales")

    MIN_MATCHES = 15
    if len(buenas) < MIN_MATCHES:
        print(f"[ALINEACION] Insuficientes matches ({len(buenas)} < {MIN_MATCHES}), feature matching descartado.")
        return None

    # Extraer puntos — convertir de coordenadas small → coordenadas originales
    pts_foto = np.float32([kp1[m.queryIdx].pt for m in buenas]).reshape(-1, 1, 2)
    pts_plantilla = np.float32([kp2[m.trainIdx].pt for m in buenas]).reshape(-1, 1, 2)

    # Escalar puntos de vuelta a coordenadas originales
    pts_foto /= ratio_foto
    pts_plantilla /= ratio_plantilla

    # Calcular homografía con RANSAC
    H, mask = cv2.findHomography(pts_foto, pts_plantilla, cv2.RANSAC, 5.0)

    if H is None:
        print("[ALINEACION] No se pudo calcular la homografía.")
        return None

    inliers = int(mask.sum()) if mask is not None else 0
    print(f"[ALINEACION] Homografía calculada: {inliers} inliers de {len(buenas)} matches")

    if inliers < 10:
        print(f"[ALINEACION] Pocos inliers ({inliers}), homografía poco confiable.")
        return None

    # Pre-escalar la imagen si es muy grande para evitar problemas de RAM
    # en servidores con poca memoria (ej. CentOS 8 con RAM limitada)
    h_orig, w_orig = img_original.shape[:2]
    MAX_WARP_DIM = 4000  # Dimensión máxima antes del warp
    if max(h_orig, w_orig) > MAX_WARP_DIM:
        scale_down = MAX_WARP_DIM / float(max(h_orig, w_orig))
        img_to_warp = cv2.resize(img_original, None, fx=scale_down, fy=scale_down)
        # Ajustar la homografía para las nuevas dimensiones
        S = np.array([[scale_down, 0, 0], [0, scale_down, 0], [0, 0, 1]], dtype=np.float64)
        H_adjusted = H @ np.linalg.inv(S)
        warped = cv2.warpPerspective(img_to_warp, H_adjusted, (w_dest, h_dest))
        print(f"[ALINEACION] Imagen pre-escalada de {w_orig}x{h_orig} a {img_to_warp.shape[1]}x{img_to_warp.shape[0]} antes del warp")
    else:
        warped = cv2.warpPerspective(img_original, H, (w_dest, h_dest))

    if guardar_debug:
        try:
            debug_path = os.path.join(DEBUG_DIR, 'debug_feature_matches.jpg')
            # Dibujar matches para depuración
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


def _alinear_por_contorno(img_original, guardar_debug=False):
    """
    ETAPA 2 (FALLBACK): Detección de bordes del documento con Canny + contorno.
    Mejorado respecto al original: usa Canny en vez de Otsu, busca cuadrilátero
    con approxPolyDP, y filtra por relación de aspecto vertical.
    """
    w_dest, h_dest = _obtener_dimensiones_plantilla()

    ratio = img_original.shape[0] / 800.0
    orig = img_original.copy()
    image_resized = cv2.resize(img_original, (int(img_original.shape[1] / ratio), 800))
    area_total = image_resized.shape[0] * image_resized.shape[1]

    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Usar Canny edge detection (más robusto que Otsu para bordes)
    edged = cv2.Canny(blur, 30, 150)
    
    # Dilatar los bordes para cerrar gaps
    kernel = np.ones((5, 5), np.uint8)
    edged = cv2.dilate(edged, kernel, iterations=2)
    edged = cv2.erode(edged, kernel, iterations=1)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    screenCnt = None
    if cnts:
        # Ordenar contornos por área, de mayor a menor
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        for c in cnts:
            area = cv2.contourArea(c)
            if area < area_total * 0.2:
                continue

            # Intentar aproximar a un polígono de 4 lados
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if len(approx) == 4:
                # Verificar que tenga forma de rectángulo vertical (portrait)
                rect = cv2.boundingRect(approx)
                aspect_ratio = rect[3] / float(rect[2])  # alto / ancho
                if aspect_ratio > 1.0:  # Debe ser más alto que ancho
                    screenCnt = approx.reshape(4, 2).astype("float32")
                    print(f"[ALINEACION] Contorno cuadrilátero detectado: area={area:.0f}, aspect={aspect_ratio:.2f}")
                    break

        # Si no encontramos cuadrilátero, usar minAreaRect del contorno más grande
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

    # Escalar puntos de vuelta a la resolución original
    pts = screenCnt * ratio

    # Ordenar los 4 puntos
    rect = _order_points(pts)

    # Verificar que los puntos formen un rectángulo razonable
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
    """
    ETAPA 3 (ÚLTIMO RECURSO): Si nada funciona, simplemente redimensionar
    la imagen al tamaño de la plantilla. Menos preciso pero mejor que nada.
    """
    w_dest, h_dest = _obtener_dimensiones_plantilla()
    print("[ALINEACION] Usando resize directo como último recurso.")
    return cv2.resize(img_original, (w_dest, h_dest), interpolation=cv2.INTER_AREA)


def _order_points(pts):
    """Ordena 4 puntos: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def alinear_imagen(img_original, guardar_debug=True):
    """
    Pipeline de alineación robusto con 3 etapas de fallback:
      1. Feature matching ORB contra la plantilla → más preciso
      2. Detección de contorno con Canny → funciona si la hoja tiene borde claro
      3. Resize directo → último recurso
    """
    # Etapa 1: Feature matching
    print("[ALINEACION] Intentando alineación por feature matching (ORB)...")
    resultado = _alinear_por_feature_matching(img_original, guardar_debug=guardar_debug)
    if resultado is not None:
        print("[ALINEACION] [OK] Feature matching exitoso.")
        if guardar_debug:
            try:
                cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_alineada.jpg'), resultado)
            except Exception:
                pass
        return resultado

    # Etapa 2: Detección de contorno
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

    # Etapa 3: Resize directo
    resultado = _alinear_simple_resize(img_original)
    if guardar_debug:
        try:
            cv2.imwrite(os.path.join(DEBUG_DIR, 'debug_alineada.jpg'), resultado)
        except Exception:
            pass
    return resultado


# ──────────────────────────────────────────────
# EVALUACIÓN DE CHECKBOXES
# ──────────────────────────────────────────────

def evaluar_checkbox_preciso(roi):
    """Evalúa si un checkbox está marcado analizando la densidad de tinta en el centro."""
    if roi is None or roi.size == 0:
        return False

    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape

    # Recortar márgenes para ignorar los bordes del checkbox
    m_h, m_w = int(h * 0.15), int(w * 0.15)
    centro = gris[m_h: h - m_h, m_w: w - m_w]

    if centro.size == 0:
        return False

    # Verificar que hay suficiente variación (no es un área vacía uniforme)
    std_dev = cv2.meanStdDev(centro)[1][0][0]
    if std_dev < 8.0:
        return False

    # Binarizar y contar pixeles de tinta
    _, thresh = cv2.threshold(centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pixeles_tinta = cv2.countNonZero(thresh)
    porcentaje = (pixeles_tinta / float(centro.size)) * 100.0

    if 3.0 < porcentaje < 40.0:
        return True

    return False


# ──────────────────────────────────────────────
# PROCESADOR PRINCIPAL
# ──────────────────────────────────────────────

def procesar_encuesta_hibrida(img_original, id_plantilla, raw_bytes=None):
    """
    Motor híbrido: PaddleOCR (texto) + OpenCV (checkboxes).
    
    Args:
        img_original: Imagen como array numpy BGR
        id_plantilla: ID de la plantilla en la BD
        raw_bytes: Bytes crudos originales (opcional, para corrección EXIF)
    """
    from services.ocr_service import OCRService

    # Si tenemos bytes crudos, corregir orientación EXIF primero
    if raw_bytes is not None:
        img_corregida = corregir_orientacion_desde_bytes(raw_bytes)
        if img_corregida is not None:
            img_original = img_corregida
    else:
        # Al menos asegurar orientación portrait
        img_original = _asegurar_portrait(img_original)

    # Paso 1: PaddleOCR extrae texto
    print("[SCANNER] Iniciando extracción de texto con PaddleOCR...")
    datos_texto = OCRService.procesar_encuesta_completa(img_original)

    # Paso 2: Alinear imagen y leer checkboxes con OpenCV
    print("[SCANNER] Alineando imagen y buscando Checkboxes...")
    img_alineada = alinear_imagen(img_original, guardar_debug=True)
    datos_checkboxes = {}

    if img_alineada is None:
        print("[SCANNER ERROR] No se pudo alinear la imagen; se omite la lectura de checkboxes.")
        datos_texto["alineacion_fallida"] = True
    else:
        # Consulta SQL por los checkboxes
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

            # Debug: dibujar overlay de los checkboxes sobre la imagen alineada
            debug_overlay = img_alineada.copy()

            for nombre_campo, x, y, w, h in campos:
                x, y, w, h = int(x), int(y), int(w), int(h)
                
                # Validar que el ROI esté dentro de los límites de la imagen
                img_h, img_w = img_alineada.shape[:2]
                if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
                    print(f"[CHECKBOX] {nombre_campo} fuera de límites: ({x},{y},{w},{h}) imagen=({img_w},{img_h})")
                    continue

                roi = img_alineada[y: y + h, x: x + w]
                marcado = evaluar_checkbox_preciso(roi)
                datos_checkboxes[nombre_campo] = marcado

                # Dibujar en debug
                color = (0, 255, 0) if marcado else (0, 0, 255)
                cv2.rectangle(debug_overlay, (x, y), (x + w, y + h), color, 3)
                etiqueta = nombre_campo.replace("Casilla ", "C")
                cv2.putText(debug_overlay, f"{etiqueta}:{'SI' if marcado else 'NO'}",
                           (x, max(0, y - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                           0.6, color, 2, cv2.LINE_AA)

            # Guardar imagen de debug con overlay
            try:
                debug_path = os.path.join(DEBUG_DIR, 'debug_mapa_marcas.jpg')
                cv2.imwrite(debug_path, debug_overlay)
                print(f"[DEBUG] Mapa de marcas guardado en {debug_path}")
            except Exception:
                pass

            conn.close()

        except Exception as e:
            print(f"[SCANNER ERROR] Falló la extracción checkbox: {e}")
            import traceback
            traceback.print_exc()

    resultado_final = {**datos_texto, **datos_checkboxes}
    print(f"[ANALISIS EXITOSO] Datos correctamente extraidos: {list(resultado_final.keys())}")
    return resultado_final