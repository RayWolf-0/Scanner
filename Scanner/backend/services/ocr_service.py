# Servicio para las llamadas del motor PaddleOCR / PaddleX, validar encuestas y extraer textos específicos
import os
import cv2
import numpy as np
from paddleocr import PaddleOCR


class OCRService:
    # Instancia única de PaddleOCR (Lazy Initialization)
    _ocr_engine = None

    @classmethod
    def _get_ocr_engine(cls):
        if cls._ocr_engine is None:
            # Inicializa PaddleOCR en español
            cls._ocr_engine = PaddleOCR(use_angle_cls=False, lang='es', enable_mkldnn=False)
        return cls._ocr_engine

    @classmethod
    def _extraer_texto_de_roi(cls, roi):
        """Extrae texto usando reconocimiento directo (det=False), ideal para recortes (ROI) pre-delimitados."""
        if roi is None or roi.size == 0:
            return ''

        # Preprocesamiento para mejorar contraste, escala y nitidez del manuscrito
        gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        h, w = gris.shape
        if h < 50 or w < 50:
            scale = max(2.5, 90.0 / min(h, w))
            gris = cv2.resize(gris, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        roi_preprocesado = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)

        ocr = cls._get_ocr_engine()
        
        try:
            # det=False evita que el modelo busque cajas y lee directamente el contenido del recorte
            resultado = ocr.ocr(roi_preprocesado, det=False)
        except TypeError:
            # Fallback por compatibilidad de versión
            try:
                resultado = ocr.ocr(roi_preprocesado)
            except Exception:
                return ''
        except Exception as e:
            print(f"[DEBUG OCR ERROR] Error en motor: {e}")
            return ''

        textos_encontrados = []

        if not resultado:
            return ''

        try:
            # Analizar la salida estructurada de det=False (tuplas o listas con texto y confianza)
            for item in resultado:
                if isinstance(item, (list, tuple)):
                    for sub in item:
                        if isinstance(sub, (list, tuple)) and len(sub) >= 2:
                            txt = str(sub[0]).strip()
                            try:
                                score = float(sub[1])
                            except (ValueError, TypeError):
                                score = 1.0
                            if txt and score >= 0.1:
                                textos_encontrados.append(txt)
                        elif isinstance(sub, str) and sub.strip():
                            textos_encontrados.append(sub.strip())
                elif isinstance(item, str) and item.strip():
                    textos_encontrados.append(item.strip())
                elif isinstance(item, dict):
                    txt = item.get('text') or item.get('rec_text') or item.get('transcription')
                    if txt:
                        textos_encontrados.append(str(txt).strip())
                    rec_texts = item.get('rec_texts', [])
                    for t in rec_texts:
                        if t: textos_encontrados.append(str(t).strip())

        except Exception as e:
            print(f"[DEBUG OCR ERROR] Analizando resultado: {e}")

        texto_final = ' '.join(textos_encontrados)
        print(f"[DEBUG OCR] Texto extraído con éxito (det=False): '{texto_final}'")
        return texto_final