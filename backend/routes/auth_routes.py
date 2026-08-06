from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from sqlalchemy import text
from models import db

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    datos = request.get_json() or {}
    usuario = datos.get('usuario')
    password = datos.get('password')

    if not usuario or not password:
        return jsonify({'error': 'Por favor ingresa usuario y contraseña'}), 400

    try:
        with db.engine.connect() as conn:
            # 1. Buscamos el usuario por su campo 'user'
            query = text("SELECT * FROM usuario WHERE user = :usr")
            result = conn.execute(query, {"usr": usuario}).mappings().fetchone()

            if not result:
                return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

            # 2. Verificamos si la contraseña coincide (soporta Hash y texto plano antiguo)
            password_bd = result['contrasena']
            es_valido = False

            if password_bd and (password_bd.startswith('scrypt:') or password_bd.startswith('pbkdf2:')):
                # Usuario creado correctamente con create_user.py (encriptado)
                es_valido = check_password_hash(password_bd, password)
            else:
                # Caso de prueba o registros antiguos en texto plano
                es_valido = (password_bd == password)

            if es_valido:
                return jsonify({
                    'status': 'success',
                    'usuario': {
                        'username': result['user'],
                        'nombre': result['nombre']
                    }
                }), 200
            else:
                return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    except Exception as e:
        return jsonify({'error': f'Error de servidor: {str(e)}'}), 500