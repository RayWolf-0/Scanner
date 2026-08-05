import os
import fitz
from models import db
from sqlalchemy import text

class PDFService:

    @classmethod
    def generar_pdf_final(cls, id_documento, id_plantilla, db_path, ruta_plantilla, ruta_salida):
        if not os.path.exists(ruta_plantilla):
            raise FileNotFoundError(f"Plantilla no encontrada: {ruta_plantilla}")

        # Leer de BD usando SQLAlchemy para asegurar que los datos estén sincronizados
        with db.engine.connect() as conn:
            datos = conn.execute(
                text("""
                    SELECT cp.nombre_campo, cp.tipo_dato, cp.pos_x, cp.pos_y, cp.ancho, cp.alto, de.valor_extraido
                    FROM DATO_EXTRAIDO de
                    JOIN CAMPO_PLANTILLA cp ON de.id_campo = cp.id_campo
                    WHERE de.id_documento = :id_doc
                """),
                {"id_doc": id_documento}
            ).fetchall()

        doc = fitz.open(ruta_plantilla)
        pagina = doc[0]

        escala_x = pagina.rect.width / 2479.0
        escala_y = pagina.rect.height / 3508.0

        for nombre_campo, tipo_dato, x, y, w, h, valor in datos:
            val_str = str(valor).strip() if valor else ""
            
            # Si está vacío o es un checkbox NO_MARCADO, ignorarlo
            if not val_str or val_str == 'NO_MARCADO':
                continue

            # Convertir coordenadas
            pdf_x, pdf_y = int(x) * escala_x, int(y) * escala_y
            pdf_w, pdf_h = int(w) * escala_x, int(h) * escala_y
            rect_destino = fitz.Rect(pdf_x, pdf_y, pdf_x + pdf_w, pdf_y + pdf_h)

            es_tipo_firma = tipo_dato in ['FIRMA', 'SIGNATURE'] or 'FIRMA' in nombre_campo.upper()
            if es_tipo_firma and val_str.endswith('.png'):
                if os.path.exists(val_str):
                    pagina.insert_image(rect_destino, filename=val_str, keep_proportion=True)
                continue

            if tipo_dato == 'CHECKBOX':
                if val_str == 'MARCADO':
                    pagina.insert_textbox(
                        rect_destino, 
                        "X", 
                        fontsize=int(pdf_h * 0.75), 
                        fontname="hebo", 
                        align=fitz.TEXT_ALIGN_CENTER, 
                        color=(0, 0, 0)
                    )
            else:
                rect_texto = fitz.Rect(pdf_x + 2, pdf_y + 1, pdf_x + pdf_w - 2, pdf_y + pdf_h - 1)
                pagina.insert_textbox(
                    rect_texto, 
                    val_str, 
                    fontsize=max(7.0, pdf_h * 0.55), 
                    fontname="helv", 
                    align=fitz.TEXT_ALIGN_LEFT, 
                    color=(0, 0, 0)
                )

        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        doc.save(ruta_salida)
        doc.close()