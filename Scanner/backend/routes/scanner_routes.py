import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from services.processor import procesar_encuesta_hibrida

scanner_router = APIRouter(prefix="/api/scanner", tags=["Scanner"])
@scanner_router.post("/analizar")
async def analizar_imagen_encuesta(
    imagen: UploadFile = File(...),
    id_plantilla: int = Form(1)
):
    try:
        if not imagen.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo no es una imagen.")

        contents = await imagen.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_original is None:
            raise HTTPException(status_code=400, detail="La imagen está corrupta.")

        print("[API SCANNER] Procesando fotografía con FastAPI...")
        datos_extraidos = procesar_encuesta_hibrida(img_original, id_plantilla)

        return JSONResponse(content={
            "status": "success",
            "data": datos_extraidos
        })

    except Exception as e:
        print(f"Error en API Scanner: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))