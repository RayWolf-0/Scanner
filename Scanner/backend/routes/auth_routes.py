from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text
from database import SessionLocal

auth_router = APIRouter()

# Login
class LoginRequest(BaseModel):
    usuario: str
    password: str

# cambio de contraseña
class ChangePasswordRequest(BaseModel):
    id_usuario: int
    password_actual: str
    password_nueva: str


@auth_router.post('/api/auth/login')
def login(datos: LoginRequest):
    if not datos.usuario or not datos.password:
        raise HTTPException(status_code=400, detail="Por favor ingresa usuario y contraseña")

    db = SessionLocal()
    try:
        # Buscar usuario (tabla en mayúsculas: USUARIO)
        query = text("""
            SELECT u.*, r.nombre_rol 
            FROM USUARIO u 
            JOIN ROL_USUARIO r ON u.id_rol = r.id_rol 
            WHERE u.user = :usr OR u.mail = :usr
        """)
        result = db.execute(query, {"usr": datos.usuario}).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        # Verificar contraseña
        password_bd = result['contrasena']
        es_valido = False

        if password_bd and (password_bd.startswith('scrypt:') or password_bd.startswith('pbkdf2:')):
            es_valido = check_password_hash(password_bd, datos.password)
        else:
            es_valido = (password_bd == datos.password)

        if es_valido:
            # rol
            nombre_rol_db = str(result['nombre_rol']).lower().strip()
            
            return {
                'status': 'success',
                'id_usuario': result['id_usuario'],
                'nombre': f"{result['nombre']} {result['apellido']}",
                'username': result['user'],
                'id_rol': result['id_rol'],
                'rol': nombre_rol_db  # supervisor o vendedor
            }
        else:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de servidor: {str(e)}")
    finally:
        db.close()


@auth_router.put('/api/auth/cambiar-password')
def cambiar_password(datos: ChangePasswordRequest):
    db = SessionLocal()
    try:
        # Buscar al usuario por su ID (tabla en mayúsculas: USUARIO)
        query = text("SELECT * FROM USUARIO WHERE id_usuario = :id")
        result = db.execute(query, {"id": datos.id_usuario}).mappings().fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        password_bd = result['contrasena']
        es_valido = False

        # validar contraseña
        if password_bd and (password_bd.startswith('scrypt:') or password_bd.startswith('pbkdf2:')):
            es_valido = check_password_hash(password_bd, datos.password_actual)
        else:
            es_valido = (password_bd == datos.password_actual)

        if not es_valido:
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

        # hash contraseña
        nueva_hash = generate_password_hash(datos.password_nueva)

        # actualizar bd (tabla en mayúsculas: USUARIO)
        db.execute(
            text("UPDATE USUARIO SET contrasena = :nueva WHERE id_usuario = :id"),
            {"nueva": nueva_hash, "id": datos.id_usuario}
        )
        db.commit()

        return {"status": "success", "mensaje": "Contraseña actualizada exitosamente"}

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error de servidor: {str(e)}")
    finally:
        db.close()