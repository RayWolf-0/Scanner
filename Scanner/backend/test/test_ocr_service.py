import numpy as np

from services.ocr_service import OCRService


def test_extraer_textos_ocr_soporta_respuesta_v6():
    resultado = {
        "rec_texts": ["ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026", "Nombre Empresa"],
        "rec_scores": [0.99, 0.95],
    }

    assert OCRService._extraer_textos_ocr(resultado) == [
        ("ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026", 0.99),
        ("Nombre Empresa", 0.95),
    ]


def test_validar_documento_con_respuesta_v6(monkeypatch):
    class DummyEngine:
        def ocr(self, img):
            return {
                "rec_texts": ["ENCUESTA DE SATISFACCIÓN DE CLIENTES 2026", "Nombre Empresa"],
                "rec_scores": [0.99, 0.95],
            }

    monkeypatch.setattr(OCRService, "get_engine", lambda: DummyEngine())
    img = np.zeros((100, 100, 3), dtype=np.uint8)

    assert OCRService.validar_documento(img) is True
