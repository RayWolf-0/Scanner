import fitz
import os

class PDFService:
    @staticmethod
    def generar_pdf_final(ruta_plantilla, ruta_salida, datos_texto, datos_casillas, ruta_firma=None):
        if not os.path.exists(ruta_plantilla):
            raise FileNotFoundError(f"No se encontró la plantilla PDF: {ruta_plantilla}")
        
        doc = fitz.open(ruta_plantilla)
        pagina = doc[0] # Primera página
        
        color_texto = (0.102, 0.169, 0.298) # Azul corporativo
        color_x = (0, 0, 0)                # Negro
        
        # 1. Encabezado
        posiciones_texto = {
            'nombre_empresa':    (180, 685),
            'rut_empresa':       (205, 147),
            'nombre_encuestado': (205, 167),
            'cargo':             (205, 187),
            'correo':            (205, 187),
            'telefono':          (425, 207),
            'fecha':             (205, 227)
        }
        
        for clave, pos in posiciones_texto.items():
            valor = datos_texto.get(clave, '')
            if valor:
                pagina.insert_text(pos, str(valor), fontname="hebo", fontsize=9, color=color_texto)
            
        # 2. Observaciones (Caja multilínea)
        obs = datos_texto.get('observaciones', '')
        if obs:
            rect_obs = fitz.Rect(85, 642, 550, 752)
            pagina.insert_textbox(rect_obs, str(obs), fontname="hebo", fontsize=9, color=color_texto)

        # 3. Casillas ("X") - Paréntesis Corregidos
        for clave, marcado in datos_casillas.items():
            if marcado and clave in COORDENADAS_CASILLAS:
                pos = COORDENADAS_CASILLAS[clave]
                pagina.insert_text(pos, "X", fontname="hebo", fontsize=9, color=color_x)
                
        # 4. Firma
        if ruta_firma and os.path.exists(ruta_firma):
            rect_firma = fitz.Rect(425, 192, 555, 210)
            pagina.insert_image(rect_firma, filename=ruta_firma)
            
        # 5. Guardar
        doc.save(ruta_salida)
        doc.close()
        
        return ruta_salida


COORDENADAS_CASILLAS = {
# 1. Evaluación de Servicios (Centros X: 388, 440, 490, 540)
    'serv_1_siempre': (340, 560), 'serv_1_general': (440, 560), 'serv_1_rara': (490, 560), 'serv_1_nunca': (540, 560),
    'serv_2_siempre': (340, 545), 'serv_2_general': (440, 545), 'serv_2_rara': (490, 545), 'serv_2_nunca': (540, 545),
    'serv_3_siempre': (340, 525), 'serv_3_general': (440, 525), 'serv_3_rara': (490, 525), 'serv_3_nunca': (540, 525),

    # 2. Evaluación de Productos
    'prod_1_siempre': (388, 344), 'prod_1_general': (440, 344), 'prod_1_rara': (490, 344), 'prod_1_nunca': (540, 344),
    'prod_2_siempre': (388, 364), 'prod_2_general': (440, 364), 'prod_2_rara': (490, 364), 'prod_2_nunca': (540, 364),
    'prod_3_siempre': (388, 384), 'prod_3_general': (440, 384), 'prod_3_rara': (490, 384), 'prod_3_nunca': (540, 384),

    # 3. Evaluación del Personal
    'pers_1_siempre': (388, 444), 'pers_1_general': (440, 444), 'pers_1_rara': (490, 444), 'pers_1_nunca': (540, 444),
    'pers_2_siempre': (388, 464), 'pers_2_general': (440, 464), 'pers_2_rara': (490, 464), 'pers_2_nunca': (540, 464),
    'pers_3_siempre': (388, 484), 'pers_3_general': (440, 484), 'pers_3_rara': (490, 484), 'pers_3_nunca': (540, 484),

    # 4. Redes Sociales (Centros X: 285, 335, 385, 435, 485, 535)
    'rs_usa_ig': (285, 522), 'rs_usa_tt': (335, 522), 'rs_usa_fb': (385, 522), 'rs_usa_li': (435, 522), 'rs_usa_pi': (485, 522), 'rs_usa_nin': (535, 522),
    'rs_sigue_ig': (285, 562), 'rs_sigue_tt': (335, 562), 'rs_sigue_fb': (385, 562), 'rs_sigue_li': (435, 562), 'rs_sigue_pi': (485, 562), 'rs_sigue_nin': (535, 562),
    
    # Correo Informativo SI/NO
    'rs_correo_si': (342, 602), 'rs_correo_no': (392, 602),
}