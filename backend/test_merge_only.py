import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

# create template PDF
packet1=io.BytesIO()
can1=canvas.Canvas(packet1,pagesize=letter)
can1.drawString(100,750,'TEMPLATE BACKGROUND')
can1.save()
packet1.seek(0)
template=PdfReader(packet1)

# create overlay with form
packet2=io.BytesIO()
can2=canvas.Canvas(packet2,pagesize=letter)
can2.drawString(100,700,'Test Field Overlay')
can2.acroForm.textfield(name='testfield', tooltip='Test Field', x=100, y=650, width=200, height=20, borderStyle='underlined', forceBorder=True, value='hello')
can2.save()
packet2.seek(0)
overlay=PdfReader(packet2)

# merge page and copy AcroForm only
writer=PdfWriter()
writer.add_page(template.pages[0])
page=writer.pages[0]
page.merge_page(overlay.pages[0])
if overlay.trailer['/Root'].get('/AcroForm'):
    writer._root_object.update({NameObject('/AcroForm'): overlay.trailer['/Root']['/AcroForm']})
with open('test_merge_only.pdf','wb') as f:
    writer.write(f)

# inspect
r=PdfReader('test_merge_only.pdf')
print('root', list(r.trailer['/Root'].keys()))
print('acroform', r.trailer['/Root'].get('/AcroForm'))
print('fields', r.get_fields())
print('page annots', r.pages[0].get('/Annots'))
