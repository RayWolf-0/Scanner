from typing import Optional

# Escalas pdf
IMG_W, IMG_H = 2551.0, 3301.0
PDF_W, PDF_H = 612.0, 792.0

# aux
def pixel_to_pdf_coords(x, y, w, h):
    return (x * (PDF_W / IMG_W)), ((IMG_H - (y + h)) * (PDF_H / IMG_H))

def obtener_id_casilla(pregunta: str, opcion: str) -> Optional[int]:
    opciones_eval = ["Siempre", "Generalmente", "Rara vez", "Nunca"]
    redes = ["Instagram", "TikTok", "Facebook", "LinkedIn", "Pinterest", "Ninguna"]
    mapeo = {
        "p1_1": range(9, 13), "p1_2": range(13, 17), "p1_3": range(17, 21),
        "p2_1": range(21, 25), "p2_2": range(25, 29), "p2_3": range(29, 33),
        "p3_1": range(33, 37), "p3_2": range(37, 41), "p3_3": range(41, 45),
    }
    if pregunta in mapeo and opcion in opciones_eval:
        return list(mapeo[pregunta])[opciones_eval.index(opcion)]
    if pregunta == "red_mas_usa" and opcion in redes:
        return [45, 47, 48, 49, 50, 51][redes.index(opcion)]
    if pregunta == "red_sigue" and opcion in redes:
        return [52, 53, 54, 56, 57, 58][redes.index(opcion)]
    if pregunta == "correo_informativo":
        return 59 if str(opcion) in ["1", "True", "true", "Sí", "si"] else 60
    return None