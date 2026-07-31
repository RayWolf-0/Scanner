#servicio para las llamadas del motor tesseract, validar encuestas y extraer textos específicos
import pytesseract
import cv2

class OCRService:
    @staticmethod
    def validar_documento(img, pos_x=None, pos_y=None, ancho=None, alto=None, texto_esperado="ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026"):
        # tomar la zona superior de la hoja carta para detectar el título
        h, w = img.shape[:2]
        if pos_x is None or pos_y is None or ancho is None or alto is None:
            pos_x = 0
            pos_y = 0
            ancho = int(w * 0.95)
            alto = int(h * 0.18)

        roi = img[int(pos_y):int(pos_y + alto), int(pos_x):int(pos_x + ancho)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        texto_detectado = pytesseract.image_to_string(gray, lang='spa', config='--psm 3')

        texto = texto_detectado.lower()
        keywords = ['encuesta', 'satisfacción', 'clientes', '2026']
        matches = sum(1 for kw in keywords if kw in texto)
        if matches >= 2:
            return True

        # fallback: tomar la parte superior completa de la hoja carta
        h, w = img.shape[:2]
        pos_x = 0
        pos_y = 0
        ancho = int(w * 0.95)
        alto = int(h * 0.18)
        roi = img[int(pos_y):int(pos_y + alto), int(pos_x):int(pos_x + ancho)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        texto_detectado = pytesseract.image_to_string(gray, lang='spa', config='--psm 3')
        texto = texto_detectado.lower()
        matches = sum(1 for kw in keywords if kw in texto)
        return matches >= 2
    
    @staticmethod
    def leer_texto_campo(img, pos_x, pos_y, ancho, alto):
        #busca una zona específica
        roi = img[int(pos_y):int(pos_y + alto), int(pos_x):int(pos_x + ancho)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        #filtro nitidez
        gray = cv2.medianBlur(gray, 3)
        texto_extraido = pytesseract.image_to_string(gray, lang='spa', config='--psm 6')
        return texto_extraido.strip()

    @staticmethod
    def leer_rut(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        data = pytesseract.image_to_data(gray, lang='spa', config='--psm 6', output_type=pytesseract.Output.DICT)

        for i, palabra in enumerate(data['text']):
            if palabra and ('rut' in palabra.lower() or 'run' in palabra.lower()):
                x = int(data['left'][i])
                y = int(data['top'][i])
                w = int(data['width'][i])
                h = int(data['height'][i])
                x0 = max(0, x)
                y0 = max(0, y - 10)
                x1 = min(img.shape[1], x + w + 320)
                y1 = min(img.shape[0], y + h + 60)
                roi = img[y0:y1, x0:x1]
                texto = OCRService.leer_texto_campo(roi, 0, 0, roi.shape[1], roi.shape[0])
                import re
                texto = texto.replace(' ', '').replace('\n', ' ').replace('\r', ' ')
                patrones = [r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9Kk]\b', r'\b\d{7,8}-[0-9Kk]\b']
                for patron in patrones:
                    encontrado = re.search(patron, texto)
                    if encontrado:
                        return encontrado.group(0)
                return texto.strip()

        texto_extraido = pytesseract.image_to_string(gray, lang='spa', config='--psm 6')
        texto_extraido = texto_extraido.replace(' ', '').replace('\n', ' ').replace('\r', ' ')
        import re
        patrones = [r'\b\d{1,2}\.\d{3}\.\d{3}-[0-9Kk]\b', r'\b\d{7,8}-[0-9Kk]\b']
        for patron in patrones:
            encontrado = re.search(patron, texto_extraido)
            if encontrado:
                return encontrado.group(0)
        return ''
    
    