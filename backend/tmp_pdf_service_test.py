import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from services.pdf_service import PDFService
from pypdf import PdfReader

# create temporary template file
with open('tmp_template.pdf', 'wb') as f:
    c = canvas.Canvas(f, pagesize=letter)
    c.drawString(100, 700, 'Template Background')
    c.save()

ruta_plantilla = 'tmp_template.pdf'
ruta_salida = 'tmp_generated.pdf'
datos_texto = {'rut_empresa': '12345678-9', 'chk_siempre': '/Yes'}
campos_posiciones = {
    'rut_empresa': {'x': 100, 'y': 600, 'width': 200, 'height': 20},
    'chk_siempre': {'x': 100, 'y': 550, 'width': 20, 'height': 20}
}
PDFService.generar_pdf_con_campos_sobre_plantilla(ruta_plantilla, ruta_salida, datos_texto, datos_firma=None, campos_posiciones=campos_posiciones, imagen_tamano=(612, 792))

r = PdfReader(ruta_salida)
print('fields:', r.get_fields())
print('acroform keys:', list(r.trailer['/Root']['/AcroForm'].keys()) if r.trailer['/Root'].get('/AcroForm') else None)
print('page annots:', r.pages[0].get('/Annots'))
