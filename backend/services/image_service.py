#Servicio para procesar la imagen con OpenCV, renderiza la hoja, cuenta pixeles y procesa la firma
import cv2
import numpy as np
from PIL import Image, ImageOps

class ImageService:

    @staticmethod
    def corregir_orientacion_exif(ruta_imagen):
        """Corrige la rotación física que aplican las cámaras de los celulares."""
        try:
            image = Image.open(ruta_imagen)
            image = ImageOps.exif_transpose(image)
            # Convertir de vuelta a formato OpenCV (BGR)
            imagen_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return imagen_cv
        except Exception as e:
            print(f"No se pudo leer EXIF: {e}")
            return cv2.imread(ruta_imagen)

    @classmethod
    def obtener_imagen_alineada(cls, ruta_imagen, esquinas_detectadas=None):
        """Alinea y corrige rotación de la imagen recibida."""
        img = cls.corregir_orientacion_exif(ruta_imagen)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta_imagen}")

        # Si se detectan esquinas válidas, aplicar transformación de perspectiva
        if esquinas_detectadas is not None and len(esquinas_detectadas) == 4:
            pts1 = np.float32(esquinas_detectadas)
            # Dimensiones estándar de calibración (Plantilla A4 / 300 DPI)
            ancho_ref, alto_ref = 2479, 3508
            pts2 = np.float32([[0, 0], [ancho_ref, 0], [ancho_ref, alto_ref], [0, alto_ref]])

            matriz = cv2.getPerspectiveTransform(pts1, pts2)
            img = cv2.warpPerspective(img, matriz, (ancho_ref, alto_ref))

        return img