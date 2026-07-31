#procesador PDF
import io
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DictionaryObject,
    IndirectObject,
    NameObject,
    NumberObject,
    RectangleObject,
    TextStringObject,
)
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image

class PDFService:
    @staticmethod
    #Relleno de la plantilla PDF
    def generar_pdf_final(ruta_plantilla, ruta_salida, datos_texto, datos_firma=None, ruta_imagen=None, campos_posiciones=None, imagen_tamano=(1000, 1400)):
        if not os.path.exists(ruta_plantilla):
            raise FileNotFoundError(f"no se ecnontró la plantilla en {ruta_plantilla}")
        #leer pdf
        reader = PdfReader(ruta_plantilla)
        writer = PdfWriter()
        #copiar las paginas al escritor
        for page in reader.pages:
            writer.add_page(page)
        #relleno de campos de texto
        if datos_texto:
            fields = reader.get_fields()
            if not fields:
                return PDFService.generar_pdf_con_campos_sobre_plantilla(
                    ruta_plantilla,
                    ruta_salida,
                    datos_texto,
                    datos_firma,
                    campos_posiciones,
                    imagen_tamano
                )
            try:
                writer.update_page_form_field_values(writer.pages[0], datos_texto)
            except Exception:
                # el PDF de plantilla no tiene campos de formulario válidos, crear un PDF editable sobre la plantilla
                return PDFService.generar_pdf_con_campos_sobre_plantilla(
                    ruta_plantilla,
                    ruta_salida,
                    datos_texto,
                    datos_firma,
                    campos_posiciones,
                    imagen_tamano
                )
                pass
        #estampar firma si es que existe
        if datos_firma and os.path.exists(datos_firma[ 'ruta']):
            #se obtienen las dimensiones de la página
            ancho_pag = float(writer.pages[0].mediabox.width)
            alto_pag = float(writer.pages[0].mediabox.height)
            #coordenadas (reportlab) y superior izquierda opencv, invertir en y
            y_invertida = alto_pag - datos_firma['y'] - datos_firma['h']
            #pdf temporal solo con la firma
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(ancho_pag, alto_pag))
            #mask para respetar la transparencia de la firma
            can.drawImage(
                datos_firma['ruta'],
                datos_firma['x'],
                y_invertida,
                width=datos_firma['w'],
                mask='auto'
            )
            can.save()
            packet.seek(0)
            #leer firma
            overLay_pdf = PdfReader(packet)
            capa_firma = overLay_pdf.pages[0]
            #fusion capa firma y pagina rellenada
            writer.pages[0].merge_page(capa_firma)
        #guardar pdf 
        with open(ruta_salida, 'wb') as archivo_salida:
            writer.write(archivo_salida)
        return ruta_salida

    @staticmethod
    def generar_pdf_con_campos_sobre_plantilla(ruta_plantilla, ruta_salida, datos_texto, datos_firma=None, campos_posiciones=None, imagen_tamano=(1000, 1400)):
        if not os.path.exists(ruta_plantilla):
            raise FileNotFoundError(f"No se encontró la plantilla: {ruta_plantilla}")

        reader = PdfReader(ruta_plantilla)
        if len(reader.pages) == 0:
            raise ValueError("La plantilla PDF no contiene páginas")

        pagina = reader.pages[0]
        ancho_pag = float(pagina.mediabox.width)
        alto_pag = float(pagina.mediabox.height)
        img_w, img_h = imagen_tamano
        scale_x = ancho_pag / img_w
        scale_y = alto_pag / img_h

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(ancho_pag, alto_pag))
        form = c.acroForm

        if campos_posiciones:
            for field_name, campo in campos_posiciones.items():
                x = campo['x'] * scale_x
                y = (img_h - campo['y'] - campo['height']) * scale_y
                width = campo['width'] * scale_x
                height = campo['height'] * scale_y
                if field_name == 'chk_siempre':
                    form.checkbox(
                        name=field_name,
                        tooltip='Siempre',
                        x=x,
                        y=y,
                        size=min(width, height),
                        borderColor=colors.black,
                        fillColor=None,
                        textColor=colors.black,
                        checked=datos_texto.get('chk_siempre', '').lower() in ['/yes', 'yes', '/on', 'on', 'true'],
                        buttonStyle='check',
                        forceBorder=True
                    )
                else:
                    form.textfield(
                        name=field_name,
                        tooltip=field_name,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        borderColor=colors.black,
                        textColor=colors.black,
                        value=datos_texto.get(field_name, ''),
                        forceBorder=True
                    )
        else:
            rut_value = datos_texto.get('rut_empresa', '')
            form.textfield(
                name='rut_empresa',
                tooltip='RUT Empresa',
                x=200,
                y=alto_pag-260,
                width=300,
                height=25,
                borderColor=colors.black,
                textColor=colors.black,
                value=rut_value,
                forceBorder=True
            )
            checkbox_value = datos_texto.get('chk_siempre', '').lower() in ['/yes', 'yes', '/on', 'on', 'true']
            form.checkbox(
                name='chk_siempre',
                tooltip='Siempre',
                x=200,
                y=alto_pag-320,
                size=20,
                borderColor=colors.black,
                fillColor=None,
                textColor=colors.black,
                checked=checkbox_value,
                buttonStyle='check',
                forceBorder=True
            )

        c.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        target_page = writer.pages[0]

        cloned_overlay_page = overlay.pages[0].clone(writer)
        if '/Annots' in cloned_overlay_page:
            cloned_annots = cloned_overlay_page['/Annots']
            target_page[NameObject('/Annots')] = cloned_annots
            for annot_ref in cloned_annots:
                annot = annot_ref.get_object()
                annot[NameObject('/P')] = target_page.indirect_reference

        if overlay.trailer['/Root'].get('/AcroForm'):
            cloned_acroform = overlay.trailer['/Root']['/AcroForm'].clone(writer)
            cloned_acroform[NameObject('/NeedAppearances')] = BooleanObject(True)
            writer._root_object[NameObject('/AcroForm')] = cloned_acroform

        writer.update_page_form_field_values(target_page, datos_texto)

        if datos_firma and os.path.exists(datos_firma['ruta']):
            packet_firma = io.BytesIO()
            can_firma = canvas.Canvas(packet_firma, pagesize=(ancho_pag, alto_pag))
            x_firma = datos_firma['x'] * scale_x
            y_firma = (img_h - datos_firma['y'] - datos_firma['h']) * scale_y
            can_firma.drawImage(datos_firma['ruta'], x_firma, y_firma, width=datos_firma['w'] * scale_x, height=datos_firma['h'] * scale_y, mask='auto')
            can_firma.save()
            packet_firma.seek(0)
            overlay_firma = PdfReader(packet_firma)
            target_page.merge_page(overlay_firma.pages[0])

        with open(ruta_salida, 'wb') as archivo_salida:
            writer.write(archivo_salida)

        return ruta_salida

    @staticmethod
    def generar_pdf_desde_imagen(ruta_imagen, ruta_salida):
        if not os.path.exists(ruta_imagen):
            raise FileNotFoundError(f"No se encontró la imagen: {ruta_imagen}")

        original_max_pixels = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None
        try:
            with Image.open(ruta_imagen) as pil_image:
                pil_image.load()
                iw, ih = pil_image.size
                max_pixels = 30_000_000
                if iw * ih > max_pixels:
                    scale = (max_pixels / float(iw * ih)) ** 0.5
                    new_width = int(iw * scale)
                    new_height = int(ih * scale)
                    pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
                    iw, ih = pil_image.size
                image_reader = ImageReader(pil_image)
                c = canvas.Canvas(ruta_salida, pagesize=(iw, ih))
                c.drawImage(image_reader, 0, 0, width=iw, height=ih)
                c.showPage()
                c.save()
        finally:
            Image.MAX_IMAGE_PIXELS = original_max_pixels

        return ruta_salida