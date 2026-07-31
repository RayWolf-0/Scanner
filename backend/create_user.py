import argparse
from werkzeug.security import generate_password_hash
from app import app
from models import db, Usuario

"""
Utility to create a new Usuario with a hashed password.
Usage example (run from backend/):
  python create_user.py --user jperez --mail jperez@example.com --password 1234 --nombre Juan --apellido Perez --run 12345678-9 --id_rol 1
"""

def main():
    parser = argparse.ArgumentParser(description='Create a new Usuario with a hashed password')
    parser.add_argument('--user', required=True, help='username (user field)')
    parser.add_argument('--mail', required=True, help='email')
    parser.add_argument('--password', required=True, help='plain-text password')
    parser.add_argument('--nombre', required=True, help='first name')
    parser.add_argument('--apellido', required=True, help='last name')
    parser.add_argument('--run', required=True, help='run/dni')
    parser.add_argument('--id_rol', type=int, default=1, help='id_rol (default 1)')

    args = parser.parse_args()

    with app.app_context():
        if Usuario.query.filter((Usuario.user==args.user) | (Usuario.mail==args.mail)).first():
            print('Error: ya existe un usuario con ese user o mail')
            return

        hashed = generate_password_hash(args.password)
        nuevo = Usuario(
            id_rol=args.id_rol,
            nombre=args.nombre,
            apellido=args.apellido,
            mail=args.mail,
            run=args.run,
            user=args.user,
            contrasena=hashed
        )
        db.session.add(nuevo)
        db.session.commit()
        print('Usuario creado con id:', nuevo.id_usuario)

if __name__ == '__main__':
    main()
