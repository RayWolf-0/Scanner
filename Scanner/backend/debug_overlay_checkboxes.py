"""
Uso:
    ./venv/bin/python debug_overlay_checkboxes.py /home/ctest/Proyecto_Encuesta_Ventas/Scanner/backend/test2.jpg 1

Genera: storage/uploads/debug_overlay.png
"""
import sys
import os
import sqlite3
import cv2
import numpy as np
from PIL import Image, ImageOps

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


def main():
    if len(sys.argv) < 3:
        print("Uso: ./venv/bin/python debug_overlay_checkboxes.py <ruta_imagen> <id_plantilla>")
        return

    ruta_imagen = sys.argv[1]
    id_plantilla = sys.argv[2]

    if not os.path.exists(ruta_imagen):
        print(f"[ERROR] No se encontró la imagen en: {ruta_imagen}")
        return

    img_original = auto_orientar_y_cargar(ruta_imagen)
    if img_original is None:
        print("[ERROR] No se pudo leer la imagen.")
        return

    # Estandarizamos al tamaño maestro (2479x3508) donde se registraron las coordenadas de la BD
    w_dest, h_dest = 2479, 3508
    img_alineada = cv2.resize(img_original, (w_dest, h_dest))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'instance', 'scanner.db')
    
    if not os.path.exists(db_path):
        print(f"[ERROR] No se encontró la base de datos en: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre_campo, pos_x, pos_y, ancho, alto
        FROM CAMPO_PLANTILLA
        WHERE id_plantilla = ? AND tipo_dato = 'CHECKBOX'
    """, (id_plantilla,))
    campos = cursor.fetchall()
    conn.close()

    if not campos:
        print(f"[AVISO] No se encontraron casillas para la plantilla ID: {id_plantilla}")

    overlay = img_alineada.copy()
    for nombre_campo, x, y, w, h in campos:
        x, y, w, h = int(x), int(y), int(w), int(h)
        # Dibuja la caja roja del checkbox registrado en la BD
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 255), 3)

        # Etiqueta de texto (ej. C1, C2...)
        etiqueta = nombre_campo.replace("Casilla ", "C")
        pos_texto = (x, max(0, y - 6))
        cv2.putText(overlay, etiqueta, pos_texto, cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 1, cv2.LINE_AA)

    # Guardado directo en storage/uploads/debug_overlay.png
    carpeta_salida = os.path.join(base_dir, 'storage', 'uploads')
    os.makedirs(carpeta_salida, exist_ok=True)
    salida = os.path.join(carpeta_salida, 'debug_overlay.png')

    cv2.imwrite(salida, overlay)
    print(f"Guardado exitosamente: {salida} ({len(campos)} casillas dibujadas)")


if __name__ == "__main__":
    main()