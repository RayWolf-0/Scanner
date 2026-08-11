import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from sqlalchemy import text
from models import db
from services.ocr_service import OCRService

# Desactivar límite de pixeles (Decompression Bomb)
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
    """
    Alineación industrial mediante ORB Feature Matching. 
    Busca los textos y líneas impresas de la encuesta en la foto y los empareja 
    contra la plantilla maestra, ignorando por completo el fondo de la madera.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Ruta de tu plantilla maestra en imagen (asegúrate de tener una copia limpia guardada aquí)
    ruta_plantilla_img = os.path.join(base_dir, 'storage', 'plantilla', 'maestra_referencia.jpg')
    
    # Si no existe una imagen de referencia, generamos un respaldo del tamaño estándar 2479x3508
    h_dest, w_dest = 3508, 2479
    
    if not os.path.exists(ruta_plantilla_img):
        # Fallback de emergencia si no hay imagen de referencia creada aún
        h_orig, w_orig = img_original.shape[:2]
        return cv2.resize(img_original, (w_dest, h_dest))

    img_plantilla = cv2.imread(ruta_plantilla_img)
    h_dest, w_dest = img_plantilla.shape[:2]

    # Convertir a escala de grises
    gray1 = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img_plantilla, cv2.COLOR_BGR2GRAY)

    # Inicializar detector ORB
    orb = cv2.ORB_create(nfeatures=3000)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(kp1) < 15 or len(kp2) < 15:
        return cv2.resize(img_original, (w_dest, h_dest))

    # Emparejar puntos clave con fuerza bruta (Hamming)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    # Tomar el top 30% de mejores coincidencias
    good_matches = matches[:int(len(matches) * 0.30)]

    if len(good_matches) < 8:
        return cv2.resize(img_original, (w_dest, h_dest))

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # Calcular matriz de transformación perspectiva (Homografía) con RANSAC
    matrix, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if matrix is None:
        return cv2.resize(img_original, (w_dest, h_dest))

    # Enderezar y recortar exactamente a las medidas de la plantilla maestra
    img_alineada = cv2.warpPerspective(img_original, matrix, (w_dest, h_dest))
    return img_alineada


def evaluar_checkbox_preciso(roi):
    if roi is None or roi.size == 0:
        return False
        
    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gris.shape
    
    m_h, m_w = int(h * 0.15), int(w * 0.15)
    centro = gris[m_h: h - m_h, m_w: w - m_w]
    
    if centro.size == 0:
        return False
        
    std_dev = cv2.meanStdDev(centro)[1][0][0]
    if std_dev < 10.0:
        return False
        
    _, thresh = cv2.threshold(centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    pixeles_tinta = cv2.countNonZero(thresh)
    porcentaje = (pixeles_tinta / float(centro.size)) * 100.0
    
    return porcentaje > 3.0


def procesar_documento_completo(id_documento, db_path=None):
    with db.engine.begin() as conn:
        res = conn.execute(
            text("SELECT ruta_imagen, id_plantilla FROM DOCUMENTO WHERE id_documento = :id_doc"),
            {"id_doc": id_documento}
        ).fetchone()
        
        if not res:
            raise FileNotFoundError(f"No se encontró documento ID {id_documento}")
            
        ruta_imagen, id_plantilla = res
        if not os.path.isabs(ruta_imagen):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_imagen = os.path.join(base_dir, ruta_imagen)
            
        img_original = auto_orientar_y_cargar(ruta_imagen)
        if img_original is None:
            raise ValueError("No se pudo cargar la imagen")
            
        # Alineación inteligente por características (Inmune a fondos de escritorio)
        img_alineada = alinear_por_caracteristicas(img_original)
        
        dir_debug = os.path.dirname(ruta_imagen)
        ruta_debug = os.path.join(dir_debug, f"debug_alineada_{id_documento}.png")
        cv2.imwrite(ruta_debug, img_alineada)
        
        campos = conn.execute(
            text("SELECT id_campo, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto FROM CAMPO_PLANTILLA WHERE id_plantilla = :id_pl"),
            {"id_pl": id_plantilla}
        ).fetchall()
        
        conn.execute(text("DELETE FROM DATO_EXTRAIDO WHERE id_documento = :id_doc"), {"id_doc": id_documento})
        
        dir_firmas = os.path.join(os.path.dirname(dir_debug), 'firmas')
        os.makedirs(dir_firmas, exist_ok=True)
        
        for id_campo, nombre, tipo, x, y, w, h in campos:
            x, y, w, h = int(x), int(y), int(w), int(h)
            roi = img_alineada[y: y + h, x: x + w]
            valor = ''
            
            if roi.size > 0:
                if tipo in ['FIRMA', 'SIGNATURE'] or 'FIRMA' in nombre.upper():
                    ruta_firma = os.path.join(dir_firmas, f"firma_doc_{id_documento}_{id_campo}.png")
                    cv2.imwrite(ruta_firma, roi)
                    valor = ruta_firma
                elif tipo == 'CHECKBOX':
                    marcado = evaluar_checkbox_preciso(roi)
                    valor = 'MARCADO' if marcado else 'NO_MARCADO'
                else:
                    texto_extraido = OCRService._extraer_texto_de_roi(roi)
                    valor = texto_extraido if texto_extraido else ''
            
            valor_final = str(valor).strip() if valor else ''
            
            conn.execute(
                text("INSERT INTO DATO_EXTRAIDO (id_documento, id_campo, valor_extraido) VALUES (:id_doc, :id_camp, :val)"),
                {"id_doc": id_documento, "id_camp": id_campo, "val": valor_final}
            )