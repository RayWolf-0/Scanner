from services.pdf_service import PDFService
from pypdf import PdfReader
import os
plantilla = os.path.join('storage','plantilla','maestra.pdf')
out = os.path.join('storage','pdf_generado','final_test2.jpg.pdf')
if os.path.exists(out):
    os.remove(out)
PDFService.generar_pdf_final(
    plantilla,
    out,
    {'rut_empresa':'11111111-1','chk_siempre':'/Yes'},
    {'ruta': os.path.join('storage','firmas','firma_vend1_test.png'),'x':400,'y':1000,'w':300,'h':150},
    ruta_imagen=os.path.join('storage','uploads','test2.jpg'),
    campos_posiciones={'rut_empresa': {'x':200,'y':150,'width':300,'height':50}, 'chk_siempre': {'x':100,'y':300,'width':50,'height':50}},
    imagen_tamano=(1000,1400)
)
r = PdfReader(out)
p = r.pages[0]
print('fields', r.get_fields())
print('Annots', p.get('/Annots'))
print('Resources', list(p.get('/Resources').keys()))
xobj = p.get('/Resources').get('/XObject')
print('XObject', xobj)
