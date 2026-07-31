import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

def merge_resources(target, source):
    if '/Resources' not in target:
        target[NameObject('/Resources')] = source['/Resources']
        return
    tgt = target['/Resources']
    src = source['/Resources']
    for key, val in src.items():
        if key not in tgt:
            tgt[NameObject(key)] = val
        else:
            # for /Font, merge sub-objects if absent
            if key == '/Font':
                tgt_font = tgt[key]
                for fontkey, fontval in val.items():
                    if fontkey not in tgt_font:
                        tgt_font[NameObject(fontkey)] = fontval

packet1 = io.BytesIO()
can1 = canvas.Canvas(packet1, pagesize=letter)
can1.drawString(100, 750, 'TEMPLATE BACKGROUND')
can1.save()
packet1.seek(0)
template = PdfReader(packet1)

packet2 = io.BytesIO()
can2 = canvas.Canvas(packet2, pagesize=letter)
can2.drawString(100, 700, 'Test Field Overlay')
can2.acroForm.textfield(name='testfield', tooltip='Test Field', x=100, y=650, width=200, height=20, borderStyle='underlined', forceBorder=True, value='hello')
can2.save()
packet2.seek(0)
overlay = PdfReader(packet2)

writer = PdfWriter()
writer.add_page(template.pages[0])
page = writer.pages[0]

# copy overlay annots and resources
overlay_page = overlay.pages[0]
page[NameObject('/Annots')] = overlay_page['/Annots']
merge_resources(page, overlay_page)
if overlay.trailer['/Root'].get('/AcroForm'):
    writer._root_object.update({NameObject('/AcroForm'): overlay.trailer['/Root']['/AcroForm']})

with open('test_copy_annots.pdf','wb') as f:
    writer.write(f)

r = PdfReader('test_copy_annots.pdf')
print('root', list(r.trailer['/Root'].keys()))
print('acroform', r.trailer['/Root'].get('/AcroForm'))
print('fields', r.get_fields())
print('page annots', r.pages[0].get('/Annots'))
print('resources', list(r.pages[0].get('/Resources').keys()))
