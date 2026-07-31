import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader

packet=io.BytesIO()
can=canvas.Canvas(packet,pagesize=letter)
can.drawString(100,700,'Test Field Overlay')
can.acroForm.textfield(name='testfield',tooltip='Test Field',x=100,y=650,width=200,height=20,borderStyle='underlined',forceBorder=True,value='hello')
can.save()
packet.seek(0)
overlay=PdfReader(packet)
print('overlay root keys', list(overlay.trailer['/Root'].keys()))
print('overlay fields', overlay.get_fields())
page=overlay.pages[0]
print('page keys', list(page.keys()))
ann=page.get('/Annots')
print('annots', ann)
for i,a in enumerate(ann):
    o=a.get_object()
    print('annot',i, {k:str(v) for k,v in o.items() if k in ['/T','/FT','/Subtype','/Rect','/V','/AP','/F','/DV','/TU']})
print('resources', page.get('/Resources'))
