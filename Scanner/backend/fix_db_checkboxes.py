import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'scanner.db')
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Mover Redes Sociales Row 1 (C37-C42 -> C41-C46)
for i in range(42, 36, -1):
    new_num = i + 4
    c.execute(f"UPDATE CAMPO_PLANTILLA SET nombre_campo = 'Casilla {new_num}' WHERE nombre_campo = 'Casilla {i}' AND tipo_dato = 'CHECKBOX'")

# 2. Mover Redes Sociales Row 2 (C43-C49 -> C47-C52)
# C43->47, C44->48, C45->49, C47->50, C48->51, C49->52
mapping_row2 = {43: 47, 44: 48, 45: 49, 47: 50, 48: 51, 49: 52}
for old, new in sorted(mapping_row2.items(), reverse=True):
    c.execute(f"UPDATE CAMPO_PLANTILLA SET nombre_campo = 'Casilla {new}' WHERE nombre_campo = 'Casilla {old}' AND tipo_dato = 'CHECKBOX'")

# 3. Mover y corregir Correo Informativo (C50-C51 -> C53-C54)
c.execute("UPDATE CAMPO_PLANTILLA SET nombre_campo = 'Casilla 53', pos_x=1190, pos_y=2415, ancho=290, alto=80 WHERE nombre_campo = 'Casilla 50' AND tipo_dato = 'CHECKBOX'")
c.execute("UPDATE CAMPO_PLANTILLA SET nombre_campo = 'Casilla 54', pos_x=1485, pos_y=2415, ancho=280, alto=80 WHERE nombre_campo = 'Casilla 51' AND tipo_dato = 'CHECKBOX'")

# 4. Insertar las 4 casillas faltantes (Q3 de Personal: C37-C40)
# Estimadas basadas en C33-C36
nuevas_casillas = [
    ('Casilla 37', 1460, 1935, 198, 46),
    ('Casilla 38', 1662, 1935, 170, 46),
    ('Casilla 39', 1840, 1935, 160, 46),
    ('Casilla 40', 2000, 1935, 225, 46)
]

for nombre, x, y, w, h in nuevas_casillas:
    c.execute("""
        INSERT INTO CAMPO_PLANTILLA (id_plantilla, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto)
        VALUES (1, ?, 'CHECKBOX', ?, ?, ?, ?)
    """, (nombre, x, y, w, h))

conn.commit()
conn.close()
print("Base de datos corregida.")
