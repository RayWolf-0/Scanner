"""
Test de alineacion y checkboxes (sin PaddleOCR).
"""
import os
import sys
import cv2
import sqlite3
import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
Image.MAX_IMAGE_PIXELS = None

def test_imagen(ruta_test):
    if not os.path.exists(ruta_test):
        print(f"[ERROR] No se encontro {ruta_test}")
        return
    
    print(f"\n{'='*60}")
    print(f"PROCESANDO: {os.path.basename(ruta_test)}")
    print(f"{'='*60}")
    
    with open(ruta_test, 'rb') as f:
        raw_bytes = f.read()
    
    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    print(f"Dimensiones: {img.shape[1]}x{img.shape[0]} ({len(raw_bytes)/1024/1024:.1f} MB)")
    
    from services.processor import (
        corregir_orientacion_desde_bytes, alinear_imagen, evaluar_checkbox_preciso
    )
    
    # Paso 1: Corregir orientacion EXIF
    img_corregida = corregir_orientacion_desde_bytes(raw_bytes)
    if img_corregida is None:
        print("[ERROR] No se pudo corregir orientacion")
        return
    print(f"Tras EXIF: {img_corregida.shape[1]}x{img_corregida.shape[0]}")
    
    # Paso 2: Alinear
    img_alineada = alinear_imagen(img_corregida, guardar_debug=True)
    if img_alineada is None:
        print("[ERROR] Fallo la alineacion")
        return
    print(f"Alineada: {img_alineada.shape[1]}x{img_alineada.shape[0]}")
    
    # Paso 3: Leer checkboxes
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'instance', 'scanner.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT nombre_campo, pos_x, pos_y, ancho, alto
        FROM CAMPO_PLANTILLA
        WHERE id_plantilla = 1 AND tipo_dato = 'CHECKBOX'
          AND ancho > 0 AND alto > 0
        ORDER BY id_campo
    """)
    campos = cursor.fetchall()
    
    # Generar overlay de debug
    debug_overlay = img_alineada.copy()
    
    casillas_marcadas = []
    casillas_no_marcadas = []
    
    for nombre_campo, x, y, w, h in campos:
        x, y, w, h = int(x), int(y), int(w), int(h)
        
        img_h, img_w = img_alineada.shape[:2]
        if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
            print(f"  [SKIP] {nombre_campo} fuera de limites: ({x},{y},{w},{h})")
            continue
        
        roi = img_alineada[y: y + h, x: x + w]
        marcado = evaluar_checkbox_preciso(roi)
        
        if marcado:
            casillas_marcadas.append(nombre_campo)
        else:
            casillas_no_marcadas.append(nombre_campo)
        
        color = (0, 255, 0) if marcado else (0, 0, 255)
        cv2.rectangle(debug_overlay, (x, y), (x + w, y + h), color, 3)
        etiqueta = nombre_campo.replace("Casilla ", "C")
        cv2.putText(debug_overlay, f"{etiqueta}:{'SI' if marcado else 'NO'}",
                   (x, max(0, y - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, color, 2, cv2.LINE_AA)
    
    conn.close()
    
    # Guardar overlay
    out_name = f"debug_overlay_{os.path.splitext(os.path.basename(ruta_test))[0]}.jpg"
    out_path = os.path.join(base_dir, 'storage', out_name)
    cv2.imwrite(out_path, debug_overlay)
    print(f"\nOverlay guardado: {out_path}")
    
    print(f"\n--- RESULTADOS ---")
    print(f"Marcadas ({len(casillas_marcadas)}): {', '.join(casillas_marcadas)}")
    print(f"No marcadas: {len(casillas_no_marcadas)} casillas")

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    for nombre in ['test2.jpg', 'test3.jpg']:
        ruta = os.path.join(base, nombre)
        if os.path.exists(ruta):
            test_imagen(ruta)
        else:
            print(f"\n[SKIP] {nombre} no encontrado")

if __name__ == '__main__':
    main()
