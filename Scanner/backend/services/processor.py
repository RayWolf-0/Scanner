import os
import cv2
import sqlite3
import numpy as np
from PIL import Image, ImageOps
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


def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def alinear_por_caracteristicas(img_original, guardar_debug=False):

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_plantilla_img = os.path.join(base_dir, 'storage', 'plantilla', 'maestra_referencia.png')

    h_dest, w_dest = 3508, 2479
    if os.path.exists(ruta_plantilla_img):
        img_plantilla = cv2.imread(ruta_plantilla_img)
        if img_plantilla is not None:
            h_dest, w_dest = img_plantilla.shape[:2]

    ratio = img_original.shape[0] / 500.0
    orig = img_original.copy()
    image_resized = cv2.resize(img_original, (int(img_original.shape[1] / ratio), 500))
    area_total = image_resized.shape[0] * image_resized.shape[1]

    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    screenCnt = None
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > area_total * 0.3:

            rect_min = cv2.minAreaRect(c)
            screenCnt = cv2.boxPoints(rect_min)

    if screenCnt is None:
        print("[ALINEACION] No se detectaron bordes confiables del documento en la foto.")
        if guardar_debug:
            try:
                cv2.imwrite("/tmp/debug_mask_fallo.png", mask)
            except Exception:
                pass
        return None

    pts = screenCnt * ratio
    rect = order_points(pts)

    # medidas de la plantilla
    dst = np.array([
        [0, 0],
        [w_dest - 1, 0],
        [w_dest - 1, h_dest - 1],
        [0, h_dest - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (w_dest, h_dest))

    if guardar_debug:
        try:
            cv2.imwrite("/tmp/debug_warped.png", warped)
        except Exception:
            pass

    return warped


def evaluar_checkbox_preciso(roi):
    #este apartado se encarga de evaluar los checkboxes
    if roi is None or roi.size == 0:
        return False

    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape

    m_h, m_w = int(h * 0.15), int(w * 0.15)
    centro = gris[m_h: h - m_h, m_w: w - m_w]

    if centro.size == 0:
        return False

    std_dev = cv2.meanStdDev(centro)[1][0][0]
    if std_dev < 8.0:
        return False

    _, thresh = cv2.threshold(centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pixeles_tinta = cv2.countNonZero(thresh)
    porcentaje = (pixeles_tinta / float(centro.size)) * 100.0

    if 3.0 < porcentaje < 40.0:
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

    if img_alineada is None:

        print("[SCANNER ERROR] No se pudo alinear la imagen; se omite la lectura de checkboxes.")
        datos_texto["alineacion_fallida"] = True
    else:
        # Consulta SQL por los checkboxes
        try:
            #Buscamos la ruta
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
                roi = img_alineada[y: y + h, x: x + w]
                marcado = evaluar_checkbox_preciso(roi)
                datos_checkboxes[nombre_campo] = marcado

            conn.close()

        except Exception as e:
            print(f"[SCANNER ERROR] falló la extracción checkbox: {e}")

    resultado_final = {**datos_texto, **datos_checkboxes}
    print(f"[ANALISIS EXITOSO] Datos correctamente extraidos: {resultado_final}")
    return resultado_final