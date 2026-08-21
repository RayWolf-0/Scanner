import difflib
from spellchecker import SpellChecker

class MotorCorreccion:
    def __init__(self):
        self.spell = SpellChecker(language='es')
        palabras_seguras = [
            'SODIMAC', 'SPA', '@GMAIL', '@HOTMAIL',
            '@OUTLOOK', 'LTDA', 'EASY', 'TECBOLT',
            'KOVACS', 'S.A', '@MAMUT'
        ]
        
        self.spell.word_frequency.load_words(palabras_seguras)
        
        self.cargos_conocidos = [
            'GERENTE', 'VENTAS', 'ANALISTA', 'REPONEDOR',
            'SUPERVISOR', 'RECURSOS HUMANOS', 'COMERCIO',
            'SISTEMAS'
        ]
        
    def _corregir_con_difflib(self, texto, opciones_validas, similitud=0.72):
        if not texto:
            return ""
        texto = str(texto).upper().strip()
        coincidencias = difflib.get_close_matches(texto, opciones_validas, n=1, cutoff=similitud)
        return coincidencias[0] if coincidencias else texto

    def _corregir_con_spellchecker(self, texto):
        if not texto:
            return ""
        
        palabras = texto.split()
        corregidas = []
        
        for p in palabras:
            p_limpia = ''.join(e for e in p if e.isalnum()).lower()
            
            if len(p_limpia) > 3: 
                correccion = self.spell.correction(p_limpia)
                if correccion:
                    corregidas.append(correccion.upper())
                else:
                    corregidas.append(p.upper())
            else:
                corregidas.append(p.upper())
                
        return " ".join(corregidas)

    def limpiar_y_predecir(self, datos_ocr):
        campos_excluidos = ['rut', 'telefono', 'fecha', 'correo']
        
        for clave, valor in datos_ocr.items():
            if not isinstance(valor, str) or not valor:
                continue
                
            if any(excluido in clave.lower() for excluido in campos_excluidos):
                continue
                
            if 'cargo' in clave.lower():
                datos_ocr[clave] = self._corregir_con_difflib(valor, self.cargos_conocidos)
            else:
                datos_ocr[clave] = self._corregir_con_spellchecker(valor)
                
        return datos_ocr