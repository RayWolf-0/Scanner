import os
import sqlite3


def inspeccionar_base_datos():
  # Ruta al archivo scanner.db en la misma carpeta backend
  db_path = os.path.join(os.path.dirname(__file__),"instance", "scanner.db")

  print("=" * 60)
  print(f"🔍 INSPECCIONANDO TABLAS CLAVE EN: {os.path.abspath(db_path)}")
  print("=" * 60)

  if not os.path.exists(db_path):
    print("❌ Error: El archivo 'scanner.db' no existe en esta ruta.")
    return

  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()

  # Tablas específicas que estructuran tu aplicación
  tablas_objetivo = ["encuesta", "dato_extraido", "CAMPO_PLANTILLA", "DOCUMENTO"]

  for nombre_tabla in tablas_objetivo:
    print(f"\n📦 TABLA: [{nombre_tabla}]")
    print("-" * 60)

    # Verificar si la tabla existe realmente en la BD
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (nombre_tabla,),
    )
    existe = cursor.fetchone()

    if not existe:
      print(f"⚠️ La tabla '{nombre_tabla}' NO EXISTE en esta base de datos.")
      print("-" * 60)
      continue

    print(f"{'Columna':<25} | {'Tipo':<15} | {'PK':<5}")
    print("-" * 60)

    # Obtener estructura de columnas
    cursor.execute(f"PRAGMA table_info('{nombre_tabla}');")
    columnas = cursor.fetchall()
    for col in columnas:
      # col[1] = nombre, col[2] = tipo, col[5] = es primary key
      print(f"{col[1]:<25} | {col[2]:<15} | {str(col[5]):<5}")

    # Contar registros
    cursor.execute(f"SELECT COUNT(*) FROM '{nombre_tabla}';")
    total = cursor.fetchone()[0]
    print(f"📊 Registros totales: {total}")
    print("-" * 60)

  conn.close()
  print("\nInspección detallada finalizada.")
  print("=" * 60)


if __name__ == "__main__":
  inspeccionar_base_datos()