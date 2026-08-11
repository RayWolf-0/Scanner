import os
import sqlite3
import cv2

# Definir rutas relativas al directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'scanner.db')
IMAGEN_PLANTILLA = os.path.join(BASE_DIR, 'storage', 'plantilla', 'maestra_referencia.png')

NOMBRE_PLANTILLA = 'Encuesta Satisfaccion 2026'
VERSION = 1

ref_point = []
drawing = False
img_display = None
scale_factor = 1.0


def obtener_o_crear_plantilla(cursor, conn, ancho, alto):
  cursor.execute(
      """
        SELECT id_plantilla FROM PLANTILLA 
        WHERE nombre = ? AND version = ?
    """,
      (NOMBRE_PLANTILLA, VERSION),
  )

  res = cursor.fetchone()
  if res:
    print(
        f"Plantilla '{NOMBRE_PLANTILLA}' v{VERSION} encontrada (ID: {res[0]})."
    )
    return res[0]

  cursor.execute(
      """
        INSERT INTO PLANTILLA (nombre, version, ancho_pagina, alto_pagina)
        VALUES (?, ?, ?, ?)
    """,
      (NOMBRE_PLANTILLA, VERSION, ancho, alto),
  )

  conn.commit()
  id_p = cursor.lastrowid
  print(f"Nueva plantilla creada con ID: {id_p}")
  return id_p


def shape_selection(event, x, y, flags, param):
  global ref_point, drawing, img_display

  if event == cv2.EVENT_LBUTTONDOWN:
    drawing = True
    ref_point = [(x, y)]

  elif event == cv2.EVENT_MOUSEMOVE and drawing:
    img_temp = img_display.copy()
    # Punto 1 y Punto 2 especificados correctamente
    cv2.rectangle(img_temp, ref_point[0], (x, y), (0, 255, 0), 2)
    cv2.imshow('Etiquetador de Plantillas', img_temp)

  elif event == cv2.EVENT_LBUTTONUP:
    drawing = False
    ref_point.append((x, y))
    cv2.rectangle(img_display, ref_point[0], ref_point[1], (0, 255, 0), 2)
    cv2.imshow('Etiquetador de Plantillas', img_display)


def ejecutar_etiquetador(ruta_imagen):
  global img_display, scale_factor, ref_point

  if not os.path.exists(ruta_imagen):
    print(f"Error: La imagen '{ruta_imagen}' no existe.")
    return

  img_original = cv2.imread(ruta_imagen)
  if img_original is None:
    print('Error: No se pudo cargar la imagen.')
    return

  alto_real, ancho_real = img_original.shape[:2]

  # Ajustar a un alto máximo de 800px para que quepa en cualquier pantalla
  max_alto_pantalla = 850.0
  if alto_real > max_alto_pantalla:
    scale_factor = max_alto_pantalla / float(alto_real)
  else:
    scale_factor = 1.0

  ancho_vis = int(ancho_real * scale_factor)
  alto_vis = int(alto_real * scale_factor)

  img_resized = cv2.resize(
      img_original, (ancho_vis, alto_vis), interpolation=cv2.INTER_AREA
  )
  img_display = img_resized.copy()

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  id_plantilla = obtener_o_crear_plantilla(cursor, conn, ancho_real, alto_real)

  cv2.namedWindow('Etiquetador de Plantillas')
  cv2.setMouseCallback('Etiquetador de Plantillas', shape_selection)

  print('\n=== INSTRUCCIONES ===')
  print('1. Arrastra el mouse (clic izquierdo) para seleccionar un campo.')
  print('2. Presiona [T] para guardar como TEXTO.')
  print('3. Presiona [C] para guardar como CASILLA/CHECKBOX.')
  print('4. Presiona [R] para reiniciar vista.')
  print('5. Presiona [ESC] o [Q] para Salir.\n')

  while True:
    cv2.imshow('Etiquetador de Plantillas', img_display)
    key = cv2.waitKey(1) & 0xFF

    if key in (27, ord('q')):
      break

    elif key == ord('r'):
      img_display = img_resized.copy()
      ref_point.clear()
      print('Vista reiniciada.')

    elif key in (ord('t'), ord('c')):
      if len(ref_point) == 2:
        x1_vis, y1_vis = ref_point[0]
        x2_vis, y2_vis = ref_point[1]

        # Convertir de coordenadas visuales a coordenadas REALES
        pos_x = int(min(x1_vis, x2_vis) / scale_factor)
        pos_y = int(min(y1_vis, y2_vis) / scale_factor)
        ancho = int(abs(x1_vis - x2_vis) / scale_factor)
        alto = int(abs(y1_vis - y2_vis) / scale_factor)

        tipo_dato = 'TEXT' if key == ord('t') else 'CHECKBOX'

        print(
            f'\nSelección Real: ({pos_x}, {pos_y}, {ancho}, {alto}) ->'
            f' {tipo_dato}'
        )
        nombre_campo = input('Nombre del campo: ').strip()

        if nombre_campo:
          cursor.execute(
              """
                        INSERT INTO CAMPO_PLANTILLA (id_plantilla, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  id_plantilla,
                  nombre_campo,
                  tipo_dato,
                  pos_x,
                  pos_y,
                  ancho,
                  alto,
              ),
          )
          conn.commit()
          print(f"Campo '{nombre_campo}' guardado con éxito en la BD.")

          # Dibujar en pantalla la selección confirmada
          x1_box, y1_box = ref_point[0]
          x2_box, y2_box = ref_point[1]
          cv2.rectangle(
              img_display,
              (min(x1_box, x2_box), min(y1_box, y2_box)),
              (max(x1_box, x2_box), max(y1_box, y2_box)),
              (255, 0, 0),
              2,
          )
        else:
          print('Cancelado: Sin nombre de campo.')

        ref_point.clear()
      else:
        print('Selecciona un recuadro primero.')

  conn.close()
  cv2.destroyAllWindows()


if __name__ == '__main__':
  ejecutar_etiquetador(IMAGEN_PLANTILLA)