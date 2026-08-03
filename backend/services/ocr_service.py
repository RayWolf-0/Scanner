#servicio para las llamadas del motor paddleocr, validar encuestas y extraer textos específicos
import cv2
import os
import re
import unicodedata

# Desactiva oneDNN para evitar fallos de ejecución en Windows/CPU
os.environ['FLAGS_use_onednn'] = '0'

from paddleocr import PaddleOCR


def _normalizar_texto_ocr(texto):
    """Convierte texto OCR a una cadena estable para validación."""
    if texto is None:
        return ''
    if isinstance(texto, (tuple, list)):
        if not texto:
            return ''
        texto = texto[0]
    return str(texto)


class OCRService:

  _ocr_engine = None

  @classmethod
  def get_engine(cls):
    """Inicialización para PaddleOCR v6.

    Desactiva la orientación de líneas sin chocar con la API antigua ni cargar
    UVDoc.
    """
    if cls._ocr_engine is None:
      cls._ocr_engine = PaddleOCR(
          lang='es', enable_mkldnn=False, use_textline_orientation=False
      )
    return cls._ocr_engine

  @staticmethod
  def _normalizar_texto(texto):
    """Convierte a minúsculas y elimina tildes/acentos."""
    if not texto:
      return ''
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')

  @staticmethod
  def _parsear_linea_ocr(linea):
    """Extrae de forma segura (texto, confianza) evitando desbordes de índice."""
    try:
      if not linea:
        return '', 0.0

      if isinstance(linea, dict):
        texto = _normalizar_texto_ocr(linea.get('text'))
        confianza = float(linea.get('score', 1.0)) if linea.get('score') is not None else 1.0
        return texto, confianza

      if isinstance(linea, (tuple, list)):
        if not linea:
          return '', 0.0
        if len(linea) >= 2 and isinstance(linea[1], (int, float)):
          return _normalizar_texto_ocr(linea[0]), float(linea[1])
        return _normalizar_texto_ocr(linea[0]), 1.0

      if isinstance(linea, str):
        return linea, 1.0

      if hasattr(linea, '__getitem__') and len(linea) >= 2:
        contenido = linea[1]
        if isinstance(contenido, (tuple, list)):
          texto = str(contenido[0]) if len(contenido) > 0 else ''
          confianza = float(contenido[1]) if len(contenido) > 1 else 1.0
          return texto, confianza
        return str(contenido), 1.0

      return '', 0.0
    except Exception:
      return '', 0.0

  @staticmethod
  def _extraer_textos_ocr(resultados):
    """Normaliza la salida de PaddleOCR, compatible con listas y diccionarios."""
    if not resultados:
      return []

    if isinstance(resultados, dict):
      textos = resultados.get('rec_texts') or []
      scores = resultados.get('rec_scores') or []
      resultado_items = []
      for idx, texto in enumerate(textos):
        score = scores[idx] if idx < len(scores) else 1.0
        resultado_items.append((str(texto), float(score)))
      return resultado_items

    if isinstance(resultados, list):
      if resultados and isinstance(resultados[0], dict):
        return OCRService._extraer_textos_ocr(resultados[0])
      items = []
      for linea in resultados:
        texto, confianza = OCRService._parsear_linea_ocr(linea)
        if texto:
          items.append((texto, confianza))
      return items

    return []

  @staticmethod
  def _extraer_texto_de_roi(roi):
    if roi is None or roi.size == 0:
      return ''

    engine = OCRService.get_engine()
    # En PaddleOCR v6 NO debemos pasar cls=False aquí
    resultados = engine.ocr(roi)

    textos = OCRService._extraer_textos_ocr(resultados)
    lineas_texto = []
    for texto, confianza in textos:
      texto_limpio = texto.strip()
      if texto_limpio and confianza > 0.30:
        lineas_texto.append(texto_limpio)

    return ' '.join(lineas_texto)

  @staticmethod
  def validar_documento(
      img,
      pos_x=None,
      pos_y=None,
      ancho=None,
      alto=None,
      texto_esperado='ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026',
  ):
    h, w = img.shape[:2]

    # Tomamos el 40% superior de la hoja
    roi = img[0 : int(h * 0.40), 0:w]
    texto_raw = OCRService._extraer_texto_de_roi(roi)
    texto_norm = OCRService._normalizar_texto(texto_raw)

    keywords = ['encuesta', 'satisfaccion', 'clientes', '2026']
    texto_norm = OCRService._normalizar_texto(texto_raw)
    matches = sum(1 for kw in keywords if kw in texto_norm)

    print(f"\n--- [DEBUG OCR] Texto leído en cabecera: '{texto_norm}' ---")
    print(f'--- [DEBUG OCR] Coincidencias encontradas: {matches}/4 ---\n')

    # Fallback: Si no detectó suficientes palabras en la cabecera, escaneamos la hoja completa
    if matches < 2:
      texto_raw_full = OCRService._extraer_texto_de_roi(img)
      texto_norm_full = OCRService._normalizar_texto(texto_raw_full)
      matches = sum(1 for kw in keywords if kw in texto_norm_full)
      print(f"--- [DEBUG OCR Fallback] Texto completo: '{texto_norm_full}' ---")
      print(f'--- [DEBUG OCR Fallback] Coincidencias: {matches}/4 ---\n')

    return matches >= 2

  @staticmethod
  def leer_texto_campo(img, pos_x, pos_y, ancho, alto):
    roi = img[int(pos_y) : int(pos_y + alto), int(pos_x) : int(pos_x + ancho)]
    return OCRService._extraer_texto_de_roi(roi)

  @staticmethod
  def leer_Campo_porcentual(img, pos_x_pct, pos_y_pct, ancho_pct, alto_pct, es_checkbox=False):
    h, w = img.shape[:2]
    x = int(pos_x_pct * w)
    y = int(pos_y_pct * h)
    ancho = int(ancho_pct * w)
    alto = int(alto_pct * h)

    roi = img[y : y + alto, x : x + ancho]
    if roi.size == 0:
      return '' if not es_checkbox else False

    if es_checkbox:
      gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
      _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
      pixeles_negros = cv2.countNonZero(thresh)
      total_pixeles = roi.shape[0] * roi.shape[1]
      porcentaje_marcado = (pixeles_negros / float(total_pixeles)) * 100

      # Si más del 5% del recuadro interno tiene tinta, se considera marcado
      return porcentaje_marcado > 5.0

    # Para texto manuscrito o impreso
    return OCRService._extraer_texto_de_roi(roi)

  @staticmethod
  def leer_rut(img):
    h, w = img.shape[:2]
    roi_cabecera = img[0 : int(h * 0.40), 0:w]

    engine = OCRService.get_engine()
    resultados = engine.ocr(roi_cabecera)

    patrones = [r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9Kk]\b', r'\b\d{7,8}-[0-9Kk]\b']

    textos = OCRService._extraer_textos_ocr(resultados)
    texto_completo = ''
    for texto_linea, _ in textos:
      if not texto_linea:
        continue

      texto_completo += ' ' + texto_linea
      texto_limpio = texto_linea.replace(' ', '')

      for patron in patrones:
        encontrado = re.search(patron, texto_limpio)
        if encontrado:
          return encontrado.group(0)

    texto_acumulado = texto_completo.replace(' ', '')
    for patron in patrones:
      encontrado = re.search(patron, texto_acumulado)
      if encontrado:
        return encontrado.group(0)

    return ''