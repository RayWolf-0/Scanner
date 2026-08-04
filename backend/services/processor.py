import os
import sqlite3
import cv2
import numpy as np
from services.ocr_service import OCRService


def cuatro_esquinas_automaticas(imagen):
  """Encuentra las 4 esquinas de la hoja.

  Si la detección falla o detecta un área extraña, usa la foto completa para no
  destruir las coordenadas.
  """
  gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
  blur = cv2.GaussianBlur(gris, (7, 7), 0)

  # Umbralización Adaptativa (ideal para sombras y fondos de madera)
  thresh = cv2.adaptiveThreshold(
      blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
  )

  contornos, _ = cv2.findContours(
      thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
  )
  contornos = sorted(contornos, key=cv2.contourArea, reverse=True)

  h_img, w_img = imagen.shape[:2]
  area_minima = h_img * w_img * 0.45  # La hoja debe ocupar al menos el 45%

  for c in contornos:
    area = cv2.contourArea(c)
    if area > area_minima:
      peri = cv2.arcLength(c, True)
      approx = cv2.approxPolyDP(c, 0.02 * peri, True)
      if len(approx) == 4:
        return approx.reshape(4, 2)

  # FALLBACK SEGURO: Si no encuentra el papel completo, toma los bordes de la foto original
  # Esto evita que 'debug_alineada' se convierta en un zoom gigante de una esquina.
  return np.array(
      [[0, 0], [w_img - 1, 0], [w_img - 1, h_img - 1], [0, h_img - 1]],
      dtype='float32',
  )


def ordenar_puntos(pts):
  """Ordena los puntos en: [Arriba-Izquierda, Arriba-Derecha, Abajo-Derecha, Abajo-Izquierda]."""
  rect = np.zeros((4, 2), dtype='float32')
  s = pts.sum(axis=1)
  rect[0] = pts[np.argmin(s)]
  rect[2] = pts[np.argmax(s)]

  diff = np.diff(pts, axis=1)
  rect[1] = pts[np.argmin(diff)]
  rect[3] = pts[np.argmax(diff)]
  return rect


def evaluar_checkbox_preciso(roi):
  """Evalúa si una casilla está marcada ignorando los bordes impresos del recuadro."""
  if roi is None or roi.size == 0:
    return False

  gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
  h, w = gris.shape

  # Margen interno del 15% para eliminar las líneas impresas de la casilla
  m_h, m_w = int(h * 0.15), int(w * 0.15)
  centro = gris[m_h : h - m_h, m_w : w - m_w]

  if centro.size == 0:
    return False

  # Binarizar adaptativamente usando OTSU en el área interna
  _, thresh = cv2.threshold(
      centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
  )

  # Contar la tinta del centro
  pixeles_tinta = cv2.countNonZero(thresh)
  total_pixeles = centro.shape[0] * centro.shape[1]
  porcentaje = (pixeles_tinta / float(total_pixeles)) * 100.0

  # Si más del 4% del área interna tiene tinta escrita, se considera MARCADO
  return porcentaje > 4.0


def procesar_documento_completo(
    id_documento,
    esquinas_detectadas=None,
    db_path='instance/scanner.db',
):
  """Procesa un documento: alineación de perspectiva y extracción de campos.

  Args:
      id_documento: ID del documento a procesar
      esquinas_detectadas: Array NumPy con las 4 esquinas (si None, se detectan
        automáticamente)
      db_path: Ruta a la base de datos SQLite
  """
  # Normalizar ruta db_path si es relativa
  if not os.path.isabs(db_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, db_path)

  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()

  # 1. Obtener la ruta de la imagen y id_plantilla del documento
  cursor.execute(
      'SELECT ruta_imagen, id_plantilla FROM DOCUMENTO WHERE id_documento = ?',
      (id_documento,),
  )
  res = cursor.fetchone()
  if not res:
    conn.close()
    raise FileNotFoundError(
        f'No se encontró el documento con ID {id_documento}'
    )
  ruta_imagen, id_plantilla = res

  if not ruta_imagen:
    conn.close()
    raise ValueError(
        f'El documento {id_documento} no tiene ruta de imagen asociada'
    )

  # Convertir la ruta de la imagen a absoluta si es relativa
  if not os.path.isabs(ruta_imagen):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_imagen = os.path.join(base_dir, ruta_imagen)

  img_original = cv2.imread(ruta_imagen)
  if img_original is None:
    conn.close()
    raise FileNotFoundError(f'No se pudo abrir la imagen: {ruta_imagen}')

  # 2. Obtener dimensiones de calibración de la plantilla
  cursor.execute(
      'SELECT ancho_pagina, alto_pagina FROM PLANTILLA WHERE id_plantilla = ?',
      (id_plantilla,),
  )
  res_plantilla = cursor.fetchone()
  ancho_dest = res_plantilla[0] if (res_plantilla and res_plantilla[0]) else 2479
  alto_dest = res_plantilla[1] if (res_plantilla and res_plantilla[1]) else 3508

  # 3. Transformación de Perspectiva (Alinear la foto de la encuesta)
  if esquinas_detectadas is None:
    esquinas_detectadas = cuatro_esquinas_automaticas(img_original)

  pts1 = ordenar_puntos(np.array(esquinas_detectadas, dtype='float32'))
  pts2 = np.array(
      [
          [0, 0],
          [ancho_dest - 1, 0],
          [ancho_dest - 1, alto_dest - 1],
          [0, alto_dest - 1],
      ],
      dtype='float32',
  )

  M = cv2.getPerspectiveTransform(pts1, pts2)
  img_alineada = cv2.warpPerspective(img_original, M, (ancho_dest, alto_dest))

  # Guardar copia de depuración visual de la imagen alineada
  dir_debug = os.path.dirname(ruta_imagen)
  cv2.imwrite(
      os.path.join(dir_debug, f'debug_alineada_{id_documento}.png'),
      img_alineada,
  )

  # 4. Obtener todos los campos de la plantilla calibrada
  cursor.execute(
      """
        SELECT id_campo, nombre_campo, tipo_dato, pos_x, pos_y, ancho, alto 
        FROM CAMPO_PLANTILLA 
        WHERE id_plantilla = ?
    """,
      (id_plantilla,),
  )

  campos = cursor.fetchall()

  # Limpiar extracciones anteriores de este documento para evitar duplicados
  cursor.execute(
      'DELETE FROM DATO_EXTRAIDO WHERE id_documento = ?', (id_documento,)
  )

  # 5. Extraer recortes y procesar cada campo sobre la imagen alineada
  for id_campo, nombre, tipo, x, y, w, h in campos:
    # Recortar la región de interés (ROI)
    roi = img_alineada[y : y + h, x : x + w]

    if roi.size == 0:
      valor = ''
    elif tipo == 'CHECKBOX':
      marcado = evaluar_checkbox_preciso(roi)
      valor = 'MARCADO' if marcado else 'NO_MARCADO'
    elif tipo == 'TEXT':
      # Pasar el recorte por PaddleOCR
      valor = OCRService._extraer_texto_de_roi(roi)
    else:
      valor = ''

    # Insertar el valor extraído en la base de datos
    cursor.execute(
        """
            INSERT INTO DATO_EXTRAIDO (id_documento, id_campo, valor_extraido)
            VALUES (?, ?, ?)
        """,
        (id_documento, id_campo, valor),
    )

  conn.commit()
  conn.close()
  print(
      f' Documento {id_documento} procesado correctamente y guardado en BD.'
  )