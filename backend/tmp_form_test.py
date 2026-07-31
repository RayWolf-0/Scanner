import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

# create overlay form
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=letter)
c.acroForm.textfield(name='field1', tooltip='Field1', x=100, y=600, width=200, height=20,
                    borderColor=colors.black, textColor=colors.black, value='abc', forceBorder=True)
c.save()
packet.seek(0)
overlay = PdfReader(packet)

# create template page
packet2 = io.BytesIO()
c2 = canvas.Canvas(packet2, pagesize=letter)
c2.drawString(100, 700, 'Template Background')
c2.save()
packet2.seek(0)
template = PdfReader(packet2)

writer = PdfWriter()
writer.add_page(template.pages[0])
target = writer.pages[0]

# clone overlay page objects into writer
cloned_overlay_page = overlay.pages[0].clone(writer)
print('cloned page keys', list(cloned_overlay_page.keys()))
if '/Annots' in cloned_overlay_page:
    cloned_annots = cloned_overlay_page['/Annots']
    print('cloned_annots', cloned_annots)
    target[NameObject('/Annots')] = cloned_annots
    for annot_ref in cloned_annots:
        annot = annot_ref.get_object()
        print('annot T', annot.get('/T'), 'P before', annot.get('/P'))
        annot[NameObject('/P')] = target.indirect_reference
        print('annot P after', annot.get('/P'))

if overlay.trailer['/Root'].get('/AcroForm'):
    cloned_acroform = overlay.trailer['/Root']['/AcroForm'].clone(writer)
    cloned_acroform[NameObject('/NeedAppearances')] = BooleanObject(True)
    writer._root_object[NameObject('/AcroForm')] = cloned_acroform

out = io.BytesIO()
writer.write(out)
out.seek(0)
r = PdfReader(out)
print('result root keys', list(r.trailer['/Root'].keys()))
print('result AcroForm', r.trailer['/Root'].get('/AcroForm'))
print('result fields', r.get_fields())
page = r.pages[0]
print('page annots', page.get('/Annots'))
if page.get('/Annots'):
    for i, a in enumerate(page.get('/Annots')):
        o = a.get_object()
        print('annot', i, {k: str(o.get(k)) for k in ['/T', '/FT', '/Subtype', '/Rect', '/V', '/AP']})
