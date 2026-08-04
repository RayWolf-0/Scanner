import os
import sys
import sqlite3
import cv2
import numpy as np

# Agregar la ruta del backend al path para poder importar services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.processor import procesar_documento_completo


def preparar_base_de_datos_prueba(db_path='instance/scanner.db'):
  """Inserta datos mínimos de prueba en scanner.db para poder probar."""
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()

  # 1. Insertar Plantilla (ejemplo: 1000x1400 px)
  cursor.execute(
      """
        INSERT INTO PLANTILLA (nombre, version, ancho_pagina, alto_pagina)
        VALUES ('Encuesta Satisfaccion 2026', 1, 1000, 1400)
    """
  )
  id_plantilla = cursor.lastrowid

  # 2. Insertar Campos de la Plantilla (x, y, ancho, alto)
  # Campo 1: Nombre Empresa (Texto)
  cursor.execute(
      """
        INSERT INTO CAMPO_PLANTILLA (id_plantilla, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto)
        VALUES (?, 'Nombre Empresa', 'TEXT', 300, 120, 600, 40)
    """,
      (id_plantilla,),
  )

  # Campo 2: Casilla Evaluación 1 (Checkbox / Marca)
  cursor.execute(
      """
        INSERT INTO CAMPO_PLANTILLA (id_plantilla, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto)
        VALUES (?, 'Eval_1_Siempre', 'CHECKBOX', 580, 280, 50, 30)
    """,
      (id_plantilla,),
  )

  # 3. Insertar Usuario y Estado requeridos
  cursor.execute(
      "INSERT INTO ROL_USUARIO (nombre_rol) VALUES ('Vendedor')"
  )
  id_rol = cursor.lastrowid

  cursor.execute(
      """
        INSERT INTO USUARIO (id_rol, nombre, apellido, user, contrasena)
        VALUES (?, 'Juan', 'Pérez', 'jperez', 1234)
    """,
      (id_rol,),
  )
  id_usuario = cursor.lastrowid

  cursor.execute(
      "INSERT INTO ESTADO_DOCUMENTO (nombre_estado) VALUES ('Pendiente')"
  )
  id_estado = cursor.lastrowid

  # 4. Crear el Documento de prueba
  ruta_imagen_demo = 'uploads/encuesta_prueba.jpg'
  cursor.execute(
      """
        INSERT INTO DOCUMENTO (id_plantilla, id_vendedor, id_estado, ruta_imagen)
        VALUES (?, ?, ?, ?)
    """,
      (id_plantilla, id_usuario, id_estado, ruta_imagen_demo),
  )
  id_documento = cursor.lastrowid

  conn.commit()
  conn.close()

  return id_documento, ruta_imagen_demo


def crear_imagen_dummy(ruta_destino):
  """Crea una imagen blanca simulada de 1000x1400 en uploads/."""
  os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
  img = np.ones((1400, 1000, 3), dtype=np.uint8) * 255

  # Dibujar un pequeño recuadro simular casilla marcada
  cv2.rectangle(img, (580, 280), (630, 310), (0, 0, 0), -1)

  cv2.imwrite(ruta_destino, img)


# =========================================================
# EJECUCIÓN DE LA PRUEBA
# =========================================================
if __name__ == '__main__':
  db_file = 'instance/scanner.db'

  print('1. Cargando datos iniciales de prueba en la BD...')
  id_doc, ruta_img = preparar_base_de_datos_prueba(db_file)
  crear_imagen_dummy(ruta_img)

  # Simular las 4 esquinas detectadas por la cámara (ejemplo de la hoja completa)
  esquinas_simuladas = np.array(
      [[10, 10], [990, 10], [990, 1390], [10, 1390]], dtype=np.float32
  )

  print(f'2. Procesando Documento ID: {id_doc}...')
  procesar_documento_completo(
      id_documento=id_doc,
      esquinas_detectadas=esquinas_simuladas,
      db_path=db_file,
  )

  print('\n3. Verificando resultados guardados en DATO_EXTRAIDO:')
  conn = sqlite3.connect(db_file)
  cursor = conn.cursor()
  cursor.execute("""
        SELECT c.nombre_campo, c.tipo_dato, d.valor_extraido
        FROM DATO_EXTRAIDO d
        JOIN CAMPO_PLANTILLA c ON d.id_campo = c.id_campo
        WHERE d.id_documento = ?
    """, (id_doc,))

  registros = cursor.fetchall()
  for campo, tipo, valor in registros:
    print(f' -> [{tipo}] {campo}: {valor}')

  conn.close()
  print('\n¡Prueba completada con éxito!')