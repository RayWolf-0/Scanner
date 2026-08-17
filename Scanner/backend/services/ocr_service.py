from paddleocr import PaddleOCR
import re

class OCRService:
    #Iniciar PAddleOCR
    _ocr_engine = None
    @classmethod
    def _get_ocr_engine(cls):
        if cls._ocr_engine is None:
            cls._ocr_engine = PaddleOCR(lang="es", enable_mkldnn=False)
        return cls._ocr_engine
    @classmethod
    def _buscar_patron(cls, patron, texto, multilinea=False):
        flags = (re.IGNORECASE | re.DOTALL) if multilinea else re.IGNORECASE
        match = re.search(patron, texto, flags)
        return match.group(1).strip() if match else ""
    
    @classmethod 
    def procesar_encuesta_completa(cls, img):
        if img is None:
            return {}
        ocr = cls._get_ocr_engine()
        
        try:
            resultado = ocr.ocr(img)
        except Exception as e:
            print(f"[Error OCR] {e}")
            return {}
        
        if not resultado:
            return {}
        
        textos_leidos = []
        
        for res in resultado:
            if isinstance(res, dict):
                if 'rec_texts' in res:
                    textos_leidos.extend(res['rec_texts'])
            elif isinstance(res, list):
                for item in res:
                    if isinstance(item, (list, tuple)) and len(item) > 1:
                        sub = item[1]
                        if isinstance(sub, (list, tuple)) and len(sub) > 0:
                            textos_leidos.append(str(sub[0]))
                        elif isinstance(sub, str):
                            textos_leidos.append(sub)
                    elif isinstance(item, str) and not item.startswith("input_path"):
                        textos_leidos.append(item)
                            
        texto_completo = "\n".join(textos_leidos)
        print(f"[OCR TEXTO CAPTURADO EXITOSAMENTE]")

        datos_extraidos = {
            "nombre_empresa": cls._buscar_patron(r"(?:Nombre\s*Empresa|Empresa)[:\s]*([^\n\r]+)", texto_completo),
            "rut_empresa": cls._buscar_patron(r"(?:RUT\s*Empresa|RUT|RUN)[:\s]*([0-9Kk\-\.]+)", texto_completo),
            "nombre_encuestado": cls._buscar_patron(r"Encuestado\(a\)[\s\n]*([A-Za-zÁÉÍÓÚáéíóú]+)", texto_completo),
            "cargo": cls._buscar_patron(r"Cargo[:\s]*([^\n\r]+)", texto_completo),
            "correo": cls._buscar_patron(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", texto_completo),
            "telefono": cls._buscar_patron(r"Tel[eé]fono[:\s]*([0-9\+]+)", texto_completo),
            "fecha": cls._buscar_patron(r"Fecha[:\s]*([0-9\-\/]+)", texto_completo),
            "observaciones": cls._buscar_patron(r"(?:Observaciones y Recomendaciones|Observaciones)[:\s]*(.*)", texto_completo)
        }
        return datos_extraidos