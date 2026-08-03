import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

def generar_pdf_con_cuadricula(ruta_entrada, ruta_salida):
    reader = PdfReader(ruta_entrada)
    writer = PdfWriter()
    pagina = reader.pages[0]
    
    # Tamaño estándar Letter (612 x 792)
    ancho_pag = float(pagina.mediabox.width)
    alto_pag = float(pagina.mediabox.height)
    
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(ancho_pag, alto_pag))
    
    # Configurar color rojo con transparencia
    rojo_transparente = Color(1, 0, 0, alpha=0.4)
    c.setStrokeColor(rojo_transparente)
    c.setFillColor(rojo_transparente)
    c.setFont("Helvetica", 7)
    
    # Dibujar líneas horizontales (Eje Y) cada 20 puntos
    for y in range(0, int(alto_pag), 20):
        c.line(0, y, ancho_pag, y)
        c.drawString(5, y + 2, f"Y={y}")
        c.drawString(ancho_pag - 30, y + 2, f"{y}") # Referencia al otro lado
        
    # Dibujar líneas verticales (Eje X) cada 20 puntos
    for x in range(0, int(ancho_pag), 20):
        c.line(x, 0, x, alto_pag)
        c.drawString(x + 2, alto_pag - 15, f"X={x}")
        c.drawString(x + 2, 5, f"{x}") # Referencia abajo

    c.save()
    packet.seek(0)
    
    # Fusionar la cuadrícula con tu plantilla maestra
    overlay = PdfReader(packet).pages[0]
    pagina.merge_page(overlay)
    writer.add_page(pagina)
    
    with open(ruta_salida, "wb") as f:
        writer.write(f)
    
    print(f"¡Cuadrícula generada en {ruta_salida}!")

# Asegúrate de poner la ruta correcta hacia tu plantilla maestra
ruta_maestra = "storage/plantilla/maestra.pdf" 
ruta_salida = "storage/plantilla/maestra_calibrada.pdf"

generar_pdf_con_cuadricula(ruta_maestra, ruta_salida)