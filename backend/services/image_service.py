#Servicio para procesar la imagen con OpenCV, renderiza la hoja, cuenta pixeles y procesa la firma
import cv2
import numpy as np
import pytesseract

class ImageService:
    @staticmethod
    def alinear_documento(ruta_imagen, ancho_esperado = 1000, alto_esperado = 1400):
        # obtiene la imagen y la redimensiona manteniendo la proporción
        img = cv2.imread(ruta_imagen)
        if img is None:
            raise FileNotFoundError("No se pudo cargar la imagen")

        h, w = img.shape[:2]
        escala = min(ancho_esperado / w, alto_esperado / h)
        nuevo_ancho = int(w * escala)
        nuevo_alto = int(h * escala)
        img_resized = cv2.resize(img, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_AREA)

        # centrar en la plantilla de destino con relleno blanco
        canvas = 255 * np.ones((alto_esperado, ancho_esperado, 3), dtype=np.uint8)
        x_offset = (ancho_esperado - nuevo_ancho) // 2
        y_offset = (alto_esperado - nuevo_alto) // 2
        canvas[y_offset:y_offset+nuevo_alto, x_offset:x_offset+nuevo_ancho] = img_resized
        return canvas
    
    @staticmethod
    def evaluar_checbox(img, pos_x, pos_y, ancho, alto, umbral_porcentajes = 15.0):
        #region de interés checbox
        roi = img[int(pos_y):int(pos_y + alto), int(pos_x):int(pos_x + ancho)]
        #escala de grises
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY_INV)
        #Pixeles de tinta
        pixeles_tinta = cv2.countNonZero(thresh)
        total_pixeles = ancho * alto
        porcentaje_marcado = (pixeles_tinta/total_pixeles) * 100
        return porcentaje_marcado >= umbral_porcentajes
    
    @staticmethod
    def procesar_firma(img, pos_x=None, pos_y=None, ancho=None, alto=None, ruta_destino_png=None):
        if isinstance(img, str):
            img = cv2.imread(img)
        if img is None:
            raise FileNotFoundError("No se pudo cargar la imagen de firma")
        if pos_x is None or pos_y is None or ancho is None or alto is None:
            data = pytesseract.image_to_data(img, lang='spa', config='--psm 6', output_type=pytesseract.Output.DICT)
            found = False
            for i, text in enumerate(data['text']):
                if text and 'firma' in text.lower():
                    x = int(data['left'][i])
                    y = int(data['top'][i])
                    w = int(data['width'][i])
                    h = int(data['height'][i])
                    margin_left = max(int(w * 2), 60)
                    margin_top = max(int(h * 6), 40)
                    margin_right = max(int(w * 12), 260)
                    margin_bottom = max(int(h * 12), 100)
                    pos_x = max(0, x - margin_left)
                    pos_y = max(0, y - margin_top)
                    ancho = min(img.shape[1] - pos_x, w + margin_left + margin_right)
                    alto = min(img.shape[0] - pos_y, h + margin_top + margin_bottom)
                    found = True
                    break
            if not found:
                # fallback simple region cerca de la mitad inferior derecha de la hoja
                h_img, w_img = img.shape[:2]
                pos_x = int(w_img * 0.5)
                pos_y = int(h_img * 0.45)
                ancho = int(w_img * 0.4)
                alto = int(h_img * 0.2)

        roi = img[int(pos_y):int(pos_y + alto), int(pos_x):int(pos_x + ancho)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        b, g, r = cv2.split(roi)
        rgba = cv2.merge([b, g, r, alpha])
        cv2.imwrite(ruta_destino_png, rgba)
        return ruta_destino_png
    