import traceback
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import SessionLocal
from schemas.encuesta import EncuestaSchema

encuesta_router = APIRouter(prefix="/api/encuesta", tags=["Encuestas"])

@encuesta_router.post("/guardar")
@encuesta_router.post("")
def guardar_y_generar_encuesta(payload: EncuestaSchema):
    db = SessionLocal()
    try:
        datos = payload.model_dump()
        extra_datos = payload.model_extra or {}

        def limpiar_evaluacion(val):
            if not val: return None
            v_lower = str(val).lower()
            if "siempre" in v_lower: return "Siempre"
            if "generalmente" in v_lower: return "Generalmente"
            if "rara" in v_lower: return "Rara vez"
            if "nunca" in v_lower: return "Nunca"
            return val

        datos['p1_1'] = limpiar_evaluacion(datos.get('p1_1') or extra_datos.get('pedidos_completos'))
        datos['p1_2'] = limpiar_evaluacion(datos.get('p1_2') or extra_datos.get('pedidos_rapidos'))
        datos['p1_3'] = limpiar_evaluacion(datos.get('p1_3') or extra_datos.get('respuestas_oportunas'))
        
        datos['p2_1'] = limpiar_evaluacion(datos.get('p2_1') or extra_datos.get('producto_bien_presentado'))
        datos['p2_2'] = limpiar_evaluacion(datos.get('p2_2') or extra_datos.get('producto_buena_calidad'))
        datos['p2_3'] = limpiar_evaluacion(datos.get('p2_3') or extra_datos.get('informacion_productos_nuevos'))
        
        datos['p3_1'] = limpiar_evaluacion(datos.get('p3_1') or extra_datos.get('contacto_con_ejecutivo'))
        datos['p3_2'] = limpiar_evaluacion(datos.get('p3_2') or extra_datos.get('calidad_atencion'))
        datos['p3_3'] = limpiar_evaluacion(datos.get('p3_3') or extra_datos.get('personal_domina_informacion'))

        red_usa = datos.get('red_mas_usa') or extra_datos.get('red_social_usa', "")
        red_sigue = datos.get('red_sigue') or extra_datos.get('red_social_sigue', "")
        
        if isinstance(red_usa, list): red_usa = ", ".join(red_usa)
        if isinstance(red_sigue, list): red_sigue = ", ".join(red_sigue)
        
        datos['red_mas_usa'] = red_usa
        datos['red_sigue'] = red_sigue
        datos['observaciones'] = datos.get('observaciones') or extra_datos.get('obs_recomen')

        # Detección de id_usuario
        id_usuario_real = extra_datos.get("id_usuario") or datos.get("id_usuario")
        if not id_usuario_real:
            primer_usr = db.execute(text("SELECT id_usuario FROM usuario LIMIT 1")).fetchone()
            id_usuario_real = primer_usr[0] if primer_usr else 3

        # insertar encuesta
        enc_res = db.execute(
            text(
                "INSERT INTO encuesta (id_usuario, empresa, rut, encuestado, cargo,"
                " correo, telefono, fecha) VALUES (:id_usuario, :empresa, :rut,"
                " :encuestado, :cargo, :correo, :telefono, :fecha)"
            ),
            {
                "id_usuario": id_usuario_real,
                "empresa": datos.get("nombre_empresa", ""),
                "rut": datos.get("rut_empresa", ""),
                "encuestado": datos.get("nombre_encuestado", ""),
                "cargo": datos.get("cargo", ""),
                "correo": datos.get("correo", ""),
                "telefono": datos.get("telefono", ""),
                "fecha": datos.get("fecha", ""),
            },
        )
        db.commit()
        registro_id = enc_res.lastrowid

        # insertar dato_extraido acorde al id
        db.execute(
            text("""
                INSERT INTO dato_extraido (
                    id, nombre_empresa, rut_empresa, nombre_encuestado, cargo, correo, telefono, fecha, firma,
                    p1_1, p1_2, p1_3, p2_1, p2_2, p2_3, p3_1, p3_2, p3_3, 
                    red_mas_usa, red_sigue, correo_informativo, observaciones
                ) VALUES (
                    :id, :nombre_empresa, :rut_empresa, :nombre_encuestado, :cargo, :correo, :telefono, :fecha, '',
                    :p1_1, :p1_2, :p1_3, :p2_1, :p2_2, :p2_3, :p3_1, :p3_2, :p3_3, 
                    :red_mas_usa, :red_sigue, :correo_informativo, :observaciones
                )
            """),
            {**datos, "id": registro_id},
        )
        db.commit()

        # asignar documento según id
        db.execute(
            text("INSERT INTO DOCUMENTO (id_plantilla, id_vendedor, id_estado, ruta_pdf_final) VALUES (1, :vendedor, 1, '')"),
            {"vendedor": id_usuario_real},
        )
        db.commit()

        return {
            "status": "success",
            "id_encuesta": registro_id,
            "mensaje": "encuesta guardada exitosamente"
        }
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@encuesta_router.get("/detalle/{registro_id}")
def obtener_detalle_encuesta(registro_id: int):
    db = SessionLocal()
    try:
        enc = db.execute(text("SELECT * FROM encuesta WHERE id_encuesta = :id"), {"id": registro_id}).mappings().fetchone()
        if not enc:
            raise HTTPException(status_code=404, detail="Encuesta no encontrada")
            
        det = db.execute(text("SELECT * FROM dato_extraido WHERE id = :id"), {"id": registro_id}).mappings().fetchone()
        
        if not det:
            det = db.execute(
                text("SELECT * FROM dato_extraido WHERE rut_empresa = :rut AND fecha = :fecha ORDER BY id DESC LIMIT 1"),
                {"rut": enc["rut"], "fecha": enc["fecha"]}
            ).mappings().fetchone()
            
        resultado = dict(enc)
        if det:
            det_dict = dict(det)
            resultado.update(det_dict)
            
            # traductor pdf de react
            resultado['pedidos_completos'] = det_dict.get('p1_1')
            resultado['pedidos_rapidos'] = det_dict.get('p1_2')
            resultado['respuestas_oportunas'] = det_dict.get('p1_3')
            
            resultado['producto_bien_presentado'] = det_dict.get('p2_1')
            resultado['producto_buena_calidad'] = det_dict.get('p2_2')
            resultado['informacion_productos_nuevos'] = det_dict.get('p2_3')
            
            resultado['contacto_con_ejecutivo'] = det_dict.get('p3_1')
            resultado['calidad_atencion'] = det_dict.get('p3_2')
            resultado['personal_domina_informacion'] = det_dict.get('p3_3')
            
            if det_dict.get('red_mas_usa'):
                resultado['red_social_usa'] = [r.strip() for r in str(det_dict.get('red_mas_usa')).split(',')]
            if det_dict.get('red_sigue'):
                resultado['red_social_sigue'] = [r.strip() for r in str(det_dict.get('red_sigue')).split(',')]
            
        # Obtener nombre del usuario
        resultado['usuario'] = 'Vendedor'
        try:
            if 'id_usuario' in resultado and resultado['id_usuario']:
                usr = db.execute(text("SELECT * FROM usuario WHERE id_usuario = :uid OR id = :uid"), {"uid": resultado['id_usuario']}).mappings().fetchone()
                if usr:
                    nombre = usr.get('nombre', '')
                    apellido = usr.get('apellido', '')
                    if nombre or apellido:
                        resultado['usuario'] = f"{nombre} {apellido}".strip()
                    else:
                        for key in ['username', 'usuario', 'mail', 'user']:
                            if key in usr and usr[key]:
                                resultado['usuario'] = usr[key]
                                break
        except Exception:
            pass

        return resultado
    finally:
        db.close()

@encuesta_router.get("/listar")
def listar_encuestas():
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                e.*, 
                (SELECT user FROM USUARIO WHERE id_usuario = e.id_usuario) AS username,
                (SELECT nombre FROM USUARIO WHERE id_usuario = e.id_usuario) AS nombre,
                (SELECT apellido FROM USUARIO WHERE id_usuario = e.id_usuario) AS apellido
            FROM encuesta e 
            ORDER BY e.id_encuesta DESC
        """)
        resultados = db.execute(query).mappings().fetchall()
        return [dict(row) for row in resultados]
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@encuesta_router.put("/actualizar/{registro_id}")
def actualizar_encuesta(registro_id: int, payload: dict):
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE encuesta 
                SET empresa = :empresa, rut = :rut, encuestado = :encuestado, 
                    cargo = :cargo, correo = :correo, telefono = :telefono, fecha = :fecha
                WHERE id_encuesta = :id
            """),
            {
                "id": registro_id,
                "empresa": payload.get("empresa", payload.get("nombre_empresa", "")),
                "rut": payload.get("rut", payload.get("rut_empresa", "")),
                "encuestado": payload.get("encuestado", payload.get("nombre_encuestado", "")),
                "cargo": payload.get("cargo", ""),
                "correo": payload.get("correo", ""),
                "telefono": payload.get("telefono", ""),
                "fecha": payload.get("fecha", "")
            }
        )

        def limpiar_evaluacion(val):
            if not val: return None
            v_lower = str(val).lower()
            if "siempre" in v_lower: return "Siempre"
            if "generalmente" in v_lower: return "Generalmente"
            if "rara" in v_lower: return "Rara vez"
            if "nunca" in v_lower: return "Nunca"
            return val

        red_usa = payload.get("red_mas_usa", payload.get("red_social_usa", ""))
        if isinstance(red_usa, list): red_usa = ", ".join(red_usa)
        
        red_sigue = payload.get("red_sigue", payload.get("red_social_sigue", ""))
        if isinstance(red_sigue, list): red_sigue = ", ".join(red_sigue)

        params_det = {
            "id": registro_id,
            "empresa": payload.get("empresa", payload.get("nombre_empresa", "")),
            "rut": payload.get("rut", payload.get("rut_empresa", "")),
            "encuestado": payload.get("encuestado", payload.get("nombre_encuestado", "")),
            "cargo": payload.get("cargo", ""),
            "correo": payload.get("correo", ""),
            "telefono": payload.get("telefono", ""),
            "fecha": payload.get("fecha", ""),
            "p1_1": limpiar_evaluacion(payload.get("p1_1") or payload.get("pedidos_completos")),
            "p1_2": limpiar_evaluacion(payload.get("p1_2") or payload.get("pedidos_rapidos")),
            "p1_3": limpiar_evaluacion(payload.get("p1_3") or payload.get("respuestas_oportunas")),
            "p2_1": limpiar_evaluacion(payload.get("p2_1") or payload.get("producto_bien_presentado")),
            "p2_2": limpiar_evaluacion(payload.get("p2_2") or payload.get("producto_buena_calidad")),
            "p2_3": limpiar_evaluacion(payload.get("p2_3") or payload.get("informacion_productos_nuevos")),
            "p3_1": limpiar_evaluacion(payload.get("p3_1") or payload.get("contacto_con_ejecutivo")),
            "p3_2": limpiar_evaluacion(payload.get("p3_2") or payload.get("calidad_atencion")),
            "p3_3": limpiar_evaluacion(payload.get("p3_3") or payload.get("personal_domina_informacion")),
            "red_mas_usa": red_usa,
            "red_sigue": red_sigue,
            "correo_informativo": payload.get("correo_informativo", 0),
            "observaciones": payload.get("observaciones", payload.get("obs_recomen", ""))
        }

        existe_det = db.execute(text("SELECT id FROM dato_extraido WHERE id = :id"), {"id": registro_id}).fetchone()

        if existe_det:
            db.execute(
                text("""
                    UPDATE dato_extraido 
                    SET nombre_empresa = :empresa, rut_empresa = :rut, nombre_encuestado = :encuestado,
                        cargo = :cargo, correo = :correo, telefono = :telefono, fecha = :fecha,
                        p1_1 = :p1_1, p1_2 = :p1_2, p1_3 = :p1_3,
                        p2_1 = :p2_1, p2_2 = :p2_2, p2_3 = :p2_3,
                        p3_1 = :p3_1, p3_2 = :p3_2, p3_3 = :p3_3,
                        red_mas_usa = :red_mas_usa, red_sigue = :red_sigue,
                        correo_informativo = :correo_informativo,
                        observaciones = :observaciones
                    WHERE id = :id
                """),
                params_det
            )
        else:
            db.execute(
                text("""
                    INSERT INTO dato_extraido (
                        id, nombre_empresa, rut_empresa, nombre_encuestado, cargo, correo, telefono, fecha, firma,
                        p1_1, p1_2, p1_3, p2_1, p2_2, p2_3, p3_1, p3_2, p3_3, 
                        red_mas_usa, red_sigue, correo_informativo, observaciones
                    ) VALUES (
                        :id, :empresa, :rut, :encuestado, :cargo, :correo, :telefono, :fecha, '',
                        :p1_1, :p1_2, :p1_3, :p2_1, :p2_2, :p2_3, :p3_1, :p3_2, :p3_3, 
                        :red_mas_usa, :red_sigue, :correo_informativo, :observaciones
                    )
                """),
                params_det
            )

        db.commit()
        return {"status": "success", "mensaje": "Encuesta actualizada correctamente"}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@encuesta_router.delete("/eliminar/{registro_id}")
def eliminar_encuesta(registro_id: int):
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM encuesta WHERE id_encuesta = :id"), {"id": registro_id})
        db.execute(text("DELETE FROM dato_extraido WHERE id = :id"), {"id": registro_id})
        db.commit()
        return {"status": "success", "mensaje": "Encuesta eliminada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()