#Servicio para procesar la imagen con OpenCV, renderiza la hoja, cuenta pixeles y procesa la firma
import cv2
import numpy as np

class ImageService:
    @staticmethod
    def alinear_documento(ruta_imagen, ancho_std=1000, alto_std=1400):
        img = cv2.imread(ruta_imagen)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta_imagen}")
        return cv2.resize(img, (ancho_std, alto_std))

    @staticmethod
    def procesar_firma(img_alineada, ruta_destino_png):
        """
        Recorta únicamente el recuadro 'Firma' en la foto estandarizada (1000x1400 px)
        y elimina el fondo de papel dejándolo 100% transparente.
        """
        # Recorte exacto de la casilla Firma (abajo a la derecha del encabezado)
        x_start, y_start = 610, 260
        ancho, alto = 250, 45

        crop = img_alineada[y_start:y_start+alto, x_start:x_start+ancho]

        # Convertir a escala de grises
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Umbralización para conservar SOLO trazos oscuros (tinta) y transparentar el resto
        _, alpha = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY_INV)

        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, alpha])

        cv2.imwrite(ruta_destino_png, rgba)
        return ruta_destino_png

    @staticmethod
    def evaluar_checbox(roi_casilla):
        #recorte casilla
        if roi_casilla is None or roi_casilla.size == 0:
            return False
        gris = cv2.cvtColor(roi_casilla, cv2.COLOR_BGR2GRAY)
        h, w = gris.shape
        m_h, m_w = int(h*0.15), int(w*0.15)
        centro = gris[m_h:h-m_h, m_w:w-m_w]
        
        if centro.size==0:
            return False
        
        _, thresh = cv2.threshold(
            centro, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        
        pixeles_negros = cv2.countNonZero(thresh)
        total_pixeles = centro.shape[0] * centro.shape[1]
        porcentaje = (pixeles_negros/float(total_pixeles)) * 100
        return porcentaje > 5.0
