import os
import sqlite3
import fitz  # PyMuPDF


class PDFService:

  @staticmethod
  def generar_pdf_final(
      id_documento,
      id_plantilla=1,
      db_path=None,
      ruta_plantilla=None,
      ruta_salida=None,
      ruta_firma=None,
  ):
    """Genera un PDF limpio estampando sobre la plantilla original los textos
    y 'X' extraídos de SQLite según las coordenadas reales guardadas por el
    labeler.
    """
    # Resolver rutas relativas al directorio del backend
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if db_path is None:
      db_path = os.path.join(base_dir, 'instance', 'scanner.db')
    if ruta_plantilla is None:
      ruta_plantilla = os.path.join(base_dir, 'storage', 'plantilla', 'maestra.pdf')
    if ruta_salida is None:
      ruta_salida = os.path.join(base_dir, 'storage', 'pdf_generado', f'final_doc_{id_documento}.pdf')
    
    if not os.path.exists(ruta_plantilla):
      raise FileNotFoundError(
          f'No se encontró la plantilla PDF: {ruta_plantilla}'
      )
    
    if not os.path.exists(db_path):
      raise FileNotFoundError(
          f'No se encontró la base de datos: {db_path}'
      )

    doc = fitz.open(ruta_plantilla)
    pagina = doc[0]  # Primera página

    # Obtener dimensiones reales del PDF (en puntos/points 72 DPI)
    ancho_pdf = pagina.rect.width
    alto_pdf = pagina.rect.height

    # Conectar a la BD para obtener el tamaño de calibración original y los datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Obtener dimensiones con las que se calibró la plantilla (300 DPI aprox)
    cursor.execute(
        """
            SELECT ancho_pagina, alto_pagina FROM PLANTILLA WHERE id_plantilla = ?
        """,
        (id_plantilla,),
    )
    res_p = cursor.fetchone()

    ancho_img_base = res_p[0] if res_p else 2479.0
    alto_img_base = res_p[1] if res_p else 3508.0

    # Factores de conversión: Coordenada_Imagen -> Coordenada_PDF
    scale_x = ancho_pdf / float(ancho_img_base)
    scale_y = alto_pdf / float(alto_img_base)

    # 2. Consultar los campos y sus valores extraídos para este documento
    cursor.execute(
        """
            SELECT c.nombre_campo, c.tipo_dato, c.pos_x, c.pos_y, c.ancho, c.alto, d.valor_extraido
            FROM CAMPO_PLANTILLA c
            LEFT JOIN DATO_EXTRAIDO d ON c.id_campo = d.id_campo AND d.id_documento = ?
            WHERE c.id_plantilla = ?
        """,
        (id_documento, id_plantilla),
    )

    campos = cursor.fetchall()
    conn.close()

    color_texto = (0.102, 0.169, 0.298)  # Azul corporativo
    color_x = (0, 0, 0)  # Negro

    # 3. Recorrer los campos y estamparlos en el PDF
    for (
        nombre_campo,
        tipo_dato,
        pos_x,
        pos_y,
        ancho,
        alto,
        valor_extraido,
    ) in campos:
      # Convertir coordenadas a escala del PDF
      pdf_x = pos_x * scale_x
      pdf_y = pos_y * scale_y
      pdf_w = ancho * scale_x
      pdf_h = alto * scale_y

      if tipo_dato == 'CHECKBOX':
        # Si la casilla está marcada en la BD (1, "1", "TRUE")
        if (
            valor_extraido
            and str(valor_extraido).strip().upper() in ['1', 'TRUE', 'SI']
        ):
          # Ajustar punto de inserción al centro de la casilla
          pos_insert = (pdf_x + (pdf_w * 0.2), pdf_y + (pdf_h * 0.8))
          pagina.insert_text(
              pos_insert,
              'X',
              fontname='hebo',
              fontsize=pdf_h * 0.8,
              color=color_x,
          )

      elif tipo_dato == 'TEXT':
        if valor_extraido:
          # Si el texto es una observación larga usar caja multilínea
          if 'OBSERVACION' in nombre_campo.upper():
            rect_obs = fitz.Rect(
                pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h
            )
            pagina.insert_textbox(
                rect_obs,
                str(valor_extraido),
                fontname='hebo',
                fontsize=8,
                color=color_texto,
            )
          else:
            # Texto simple de una línea
            pos_insert = (pdf_x + 2, pdf_y + (pdf_h * 0.75))
            pagina.insert_text(
                pos_insert,
                str(valor_extraido),
                fontname='hebo',
                fontsize=max(7, pdf_h * 0.6),
                color=color_texto,
            )

    # 4. Estampar la firma si existe
    if ruta_firma and os.path.exists(ruta_firma):
      # Buscar si hay un campo de firma calibrado en la base de datos o usar por defecto
      rect_firma = fitz.Rect(425, 192, 555, 210)
      pagina.insert_image(rect_firma, filename=ruta_firma)

    # 5. Guardar el PDF resultante
    if not ruta_salida:
      ruta_salida = os.path.join(base_dir, 'storage', 'pdf_generado', f'final_doc_{id_documento}.pdf')

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    doc.save(ruta_salida)
    doc.close()

    print(f'PDF generado con éxito en: {ruta_salida}')
    return ruta_salida