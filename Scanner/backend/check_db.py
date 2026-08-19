"""
Limpia los registros problemáticos de la BD:
- Casilla 38 duplicada (id=46, ancho=0, alto=0)
- Casilla 46 duplicada (id=55, ancho=0, alto=0)
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'scanner.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Ver los registros problematicos
c.execute("SELECT id_campo, nombre_campo, pos_x, pos_y, ancho, alto FROM CAMPO_PLANTILLA WHERE ancho = 0 OR alto = 0")
problemas = c.fetchall()
print(f"Registros con dimensiones 0: {len(problemas)}")
for r in problemas:
    print(f"  Eliminando: id={r[0]} nombre={r[1]} ({r[2]},{r[3]},{r[4]},{r[5]})")
    c.execute("DELETE FROM CAMPO_PLANTILLA WHERE id_campo = ?", (r[0],))

conn.commit()

# Verificar
c.execute("SELECT COUNT(*) FROM CAMPO_PLANTILLA WHERE tipo_dato='CHECKBOX'")
total = c.fetchone()[0]
print(f"\nTotal checkboxes restantes: {total}")

# Actualizar dimensiones de la plantilla para que coincidan con la imagen de referencia
import cv2
ref_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage', 'plantilla', 'maestra_referencia.png')
if os.path.exists(ref_path):
    img = cv2.imread(ref_path)
    if img is not None:
        h, w = img.shape[:2]
        print(f"\nDimensiones reales de maestra_referencia.png: {w}x{h}")
        c.execute("SELECT ancho_pagina, alto_pagina FROM PLANTILLA WHERE id_plantilla = 1")
        current = c.fetchone()
        print(f"Dimensiones actuales en BD: {current[0]}x{current[1]}")
        
        if current[0] != w or current[1] != h:
            print(f"NOTA: Las dimensiones difieren. La BD dice {current[0]}x{current[1]}, la imagen es {w}x{h}.")
            print("Las coordenadas de checkboxes fueron calibradas con labeler.py contra esta imagen,")
            print("así que deberían ser correctas relativas a estas dimensiones.")

conn.close()
print("\n✓ Limpieza completada.")
