import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, ArrayObject

# Generate overlay with form field
packet = io.BytesIO()
can = canvas.Canvas(packet, pagesize=letter)
can.drawString(100, 700, 'Test Field Overlay')
can.acroForm.textfield(name='testfield', tooltip='Test Field', x=100, y=650, width=200, height=20, borderStyle='underlined', forceBorder=True, value='hello')
can.save()
packet.seek(0)
overlay = PdfReader(packet)

template = PdfWriter()
template.add_blank_page(width=letter[0], height=letter[1])
page = template.pages[0]
page.merge_page(overlay.pages[0])
# copy annotations and AcroForm
if '/Annots' in overlay.pages[0]:
    page[NameObject('/Annots')] = overlay.pages[0]['/Annots']
if overlay.trailer['/Root'].get('/AcroForm'):
    template._root_object.update({NameObject('/AcroForm'): overlay.trailer['/Root']['/AcroForm']})
with open('merge_manual.pdf','wb') as f:
    template.write(f)

r = PdfReader('merge_manual.pdf')
print('Root keys', list(r.trailer['/Root'].keys()))
print('AcroForm', r.trailer['/Root'].get('/AcroForm'))
print('Fields', r.get_fields())
print('Annots', r.pages[0].get('/Annots'))
