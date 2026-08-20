from typing import List, Optional, Union
from pydantic import BaseModel, field_validator, ConfigDict

# esquema rellenar encuestas
class EncuestaSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    nombre_empresa: str
    rut_empresa: str
    nombre_encuestado: str
    cargo: Optional[str] = ""
    correo: str
    telefono: Optional[str] = ""
    fecha: Optional[str] = None
    firma: Optional[str] = ""
    
    p1_1: Optional[str] = None
    p1_2: Optional[str] = None
    p1_3: Optional[str] = None
    p2_1: Optional[str] = None
    p2_2: Optional[str] = None
    p2_3: Optional[str] = None
    p3_1: Optional[str] = None
    p3_2: Optional[str] = None
    p3_3: Optional[str] = None

    red_mas_usa: Optional[Union[str, List[str]]] = None
    red_sigue: Optional[Union[str, List[str]]] = None

    correo_informativo: Optional[Union[int, str]] = 0
    observaciones: Optional[str] = ""

    @field_validator("correo_informativo", mode="before")
    @classmethod
    def format_correo_informativo(cls, v):
        if v is None or v == "" or v == "null":
            return 0
        if str(v).lower() in ["1", "true", "si", "sí"]:
            return 1
        return 0