from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from werkzeug.security import check_password_hash
from sqlalchemy import text

from database import SessionLocal

vendedor_router = APIRouter(prefix="/api/vendedor", tags=["Vendedor"])

# Esquema para recibir los datos de login
class LoginRequest(BaseModel):
    user: str
    contrasena: str

@vendedor_router.post("/login")
def login(payload: LoginRequest):
    db = SessionLocal()
    try:
        # Buscar usuario por email o por nombre de usuario
        query = text("""
            SELECT id_usuario, nombre, apellido, id_rol, contrasena 
            FROM USUARIO 
            WHERE mail = :user OR user = :user
        """)
        usuario = db.execute(query, {"user": payload.user}).mappings().fetchone()

        # Validar si existe y si la contraseña coincide con el hash
        if usuario and check_password_hash(usuario["contrasena"], payload.contrasena):
            return {
                "status": "success",
                "id_usuario": usuario["id_usuario"],
                "nombre": f"{usuario['nombre']} {usuario['apellido']}",
                "rol": usuario["id_rol"]
            }
        
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()