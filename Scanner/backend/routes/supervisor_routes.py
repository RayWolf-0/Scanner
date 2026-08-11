import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

supervisor_bp = APIRouter(prefix="/api/supervisor", tags=["Supervisor"])


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "scanner.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"timeout": 30.0}, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

class EstadoSchema(BaseModel):
    estado: str

@supervisor_bp.get("/documentos")
def listar_documentos():
    """Lista todos los documentos escaneados para revisión del supervisor."""
    db = SessionLocal()
    try:
        query = """
            SELECT d.id_documento, d.fecha_creacion, d.ruta_pdf_final, 
                   e.nombre_estado, u.nombre, u.apellido
            FROM DOCUMENTO d
            JOIN ESTADO_DOCUMENTO e ON d.id_estado = e.id_estado
            JOIN USUARIO u ON d.id_vendedor = u.id_usuario
            ORDER BY d.fecha_creacion DESC
        """
        resultado = db.execute(text(query)).fetchall()
        documentos = []
        for row in resultado:
            documentos.append({
                "id_documento": row[0],
                "fecha_creacion": str(row[1]),
                "ruta_pdf": row[2],
                "estado": row[3],
                "vendedor": f"{row[4]} {row[5]}"
            })
        return {"status": "success", "documentos": documentos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@supervisor_bp.put("/documentos/{id_documento}/estado")
def cambiar_estado_documento(id_documento: int, payload: EstadoSchema):
    """Permite al supervisor aprobar, rechazar o cambiar el estado de un documento."""
    nuevo_estado_nombre = payload.estado
    if not nuevo_estado_nombre:
        raise HTTPException(status_code=400, detail="Debe especificar el nuevo estado")

    db = SessionLocal()
    try:
        estado_obj = db.execute(
            text("SELECT id_estado FROM ESTADO_DOCUMENTO WHERE UPPER(nombre_estado) = :nombre"),
            {"nombre": nuevo_estado_nombre.upper()}
        ).fetchone()
        
        if not estado_obj:
            raise HTTPException(status_code=400, detail="El estado especificado no es válido")

        doc = db.execute(
            text("SELECT id_documento FROM DOCUMENTO WHERE id_documento = :id"),
            {"id": id_documento}
        ).fetchone()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        db.execute(
            text("UPDATE DOCUMENTO SET id_estado = :id_est WHERE id_documento = :id_doc"),
            {"id_est": estado_obj[0], "id_doc": id_documento}
        )
        db.commit()

        return {
            "status": "success",
            "mensaje": f"Documento {id_documento} actualizado a {nuevo_estado_nombre.upper()}"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@supervisor_bp.get("/documentos/{id_documento}/pdf")
def descargar_pdf_final(id_documento: int):
    """Permite descargar el PDF generado y procesado."""
    db = SessionLocal()
    try:
        doc = db.execute(
            text("SELECT ruta_pdf_final FROM DOCUMENTO WHERE id_documento = :id"),
            {"id": id_documento}
        ).fetchone()

        if not doc or not doc[0] or not os.path.exists(doc[0]):
            raise HTTPException(status_code=404, detail="PDF no encontrado para este documento")

        return FileResponse(doc[0], filename=os.path.basename(doc[0]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@supervisor_bp.get("/usuarios")
def listar_usuarios():
    """Permite al supervisor ver la lista de todos los usuarios registrados."""
    db = SessionLocal()
    try:
        query = """
            SELECT u.id_usuario, u.nombre, u.apellido, u.mail, u.run, u.user, u.id_rol, r.nombre_rol
            FROM USUARIO u
            JOIN ROL_USUARIO r ON u.id_rol = r.id_rol
        """
        resultado = db.execute(text(query)).fetchall()
        usuarios = []
        for u in resultado:
            usuarios.append({
                "id_usuario": u[0],
                "nombre": u[1],
                "apellido": u[2],
                "mail": u[3],
                "run": u[4],
                "user": u[5],
                "id_rol": u[6],
                "rol": u[7]
            })
        return {"status": "success", "usuarios": usuarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class UsuarioCreateSchema(BaseModel):
    nombre: str
    apellido: str
    mail: str
    run: str
    user: str
    contrasena: str
    id_rol: int

@supervisor_bp.post("/usuarios/crear")
def crear_usuario(payload: UsuarioCreateSchema):
    """Permite al supervisor crear un nuevo vendedor o supervisor."""
    db = SessionLocal()
    try:
        # Verificar duplicados
        existente = db.execute(
            text("SELECT id_usuario FROM USUARIO WHERE mail = :mail OR user = :user OR run = :run"),
            {"mail": payload.mail, "user": payload.user, "run": payload.run}
        ).fetchone()

        if existente:
            raise HTTPException(status_code=400, detail="El correo, nombre de usuario (user) o RUN ya están registrados")

        hashed_password = generate_password_hash(payload.contrasena)

        db.execute(
            text("""
                INSERT INTO USUARIO (nombre, apellido, mail, run, user, contrasena, id_rol)
                VALUES (:nombre, :apellido, :mail, :run, :user, :contrasena, :id_rol)
            """),
            {
                "nombre": payload.nombre,
                "apellido": payload.apellido,
                "mail": payload.mail,
                "run": payload.run,
                "user": payload.user,
                "contrasena": hashed_password,
                "id_rol": payload.id_rol
            }
        )
        db.commit()

        return {
            "status": "success",
            "mensaje": f"Usuario {payload.nombre} {payload.apellido} creado exitosamente"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        
class UsuarioUpdateSchema(BaseModel):
    nombre: str
    apellido: str
    mail: str
    run: str
    user: str
    contrasena: Optional[str] = None  # Opcional: solo se cambia si se escribe una nueva
    id_rol: int

@supervisor_bp.put("/usuarios/actualizar/{id_usuario}")
def actualizar_usuario(id_usuario: int, payload: UsuarioUpdateSchema):
    """Permite al supervisor actualizar los datos de un usuario existente."""
    db = SessionLocal()
    try:
        # Verificar que el usuario exista
        user_exist = db.execute(
            text("SELECT id_usuario FROM USUARIO WHERE id_usuario = :id"),
            {"id": id_usuario}
        ).fetchone()

        if not user_exist:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar duplicados de mail, user o run en OTROS usuarios
        duplicado = db.execute(
            text("SELECT id_usuario FROM USUARIO WHERE (mail = :mail OR user = :user OR run = :run) AND id_usuario != :id"),
            {"mail": payload.mail, "user": payload.user, "run": payload.run, "id": id_usuario}
        ).fetchone()

        if duplicado:
            raise HTTPException(status_code=400, detail="El correo, nombre de usuario o RUN ya pertenecen a otro usuario")

        # Si mandó contraseña nueva, la encriptamos; si no, mantenemos la anterior
        if payload.contrasena and payload.contrasena.strip() != "":
            hashed_password = generate_password_hash(payload.contrasena)
            db.execute(
                text("""
                    UPDATE USUARIO 
                    SET nombre = :nombre, apellido = :apellido, mail = :mail, 
                        run = :run, user = :user, contrasena = :contrasena, id_rol = :id_rol
                    WHERE id_usuario = :id
                """),
                {
                    "nombre": payload.nombre,
                    "apellido": payload.apellido,
                    "mail": payload.mail,
                    "run": payload.run,
                    "user": payload.user,
                    "contrasena": hashed_password,
                    "id_rol": payload.id_rol,
                    "id": id_usuario
                }
            )
        else:
            db.execute(
                text("""
                    UPDATE USUARIO 
                    SET nombre = :nombre, apellido = :apellido, mail = :mail, 
                        run = :run, user = :user, id_rol = :id_rol
                    WHERE id_usuario = :id
                """),
                {
                    "nombre": payload.nombre,
                    "apellido": payload.apellido,
                    "mail": payload.mail,
                    "run": payload.run,
                    "user": payload.user,
                    "id_rol": payload.id_rol,
                    "id": id_usuario
                }
            )

        db.commit()
        return {
            "status": "success",
            "mensaje": f"Usuario {payload.nombre} {payload.apellido} actualizado correctamente"
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
        
@supervisor_bp.delete("/usuarios/eliminar/{id_usuario}")
def eliminar_usuario(id_usuario: int):
    """Permite al supervisor eliminar un usuario del sistema."""
    db = SessionLocal()
    try:
        # Verificar que el usuario exista
        user = db.execute(
            text("SELECT id_usuario FROM USUARIO WHERE id_usuario = :id"),
            {"id": id_usuario}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # OJO no se va a borrar si tiene documentos asociados
        db.execute(
            text("DELETE FROM USUARIO WHERE id_usuario = :id"),
            {"id": id_usuario}
        )
        db.commit()

        return {
            "status": "success",
            "mensaje": f"Usuario con ID {id_usuario} eliminado correctamente"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar este usuario porque tiene documentos o registros asociados en el sistema."
        )
    finally:
        db.close()