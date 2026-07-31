import os
import glob
from pypdf import PdfReader

files = glob.glob('storage/pdf_generado/*.pdf')
print('files:', files)
for fname in files:
    print('---', fname)
    print('mtime', os.path.getmtime(fname))

fname = 'storage/pdf_generado/final_test2.jpg.pdf'
print('exists', os.path.exists(fname))
if not os.path.exists(fname):
    raise SystemExit('file missing')
r = PdfReader(fname)
print('Root keys', list(r.trailer['/Root'].keys()))
print('AcroForm', r.trailer['/Root'].get('/AcroForm'))
print('fields', r.get_fields())
p = r.pages[0]
print('Page Annots', p.get('/Annots'))
annots = p.get('/Annots')
if annots:
    for i, a in enumerate(annots):
        o = a.get_object()
        print('annot', i)
        for k in ['/T', '/FT', '/Subtype', '/Rect', '/V', '/DV', '/AP', '/P']:
            if k in o:
                print(' ', k, o[k])
