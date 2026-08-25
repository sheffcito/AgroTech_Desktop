import sqlite3
import hashlib
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "agrotech_smartfields.db")

def obtener_conexion():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT
            );
        """)
        
        cursor.executemany("""
            INSERT OR IGNORE INTO roles (id, nombre, descripcion) VALUES (?, ?, ?);
        """, [
            (1, 'Administrador', 'Control total y accesos'),
            (2, 'Encargado de Producción', 'Control de parcelas y cultivos'),
            (3, 'Trabajador', 'Operaciones y consultas')
        ])

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol_id INTEGER NOT NULL,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (rol_id) REFERENCES roles (id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ubicacion TEXT NOT NULL,
                tamano_m2 REAL NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cultivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcela_id INTEGER NOT NULL,
                tipo_cultivo TEXT NOT NULL,
                fecha_siembra TEXT NOT NULL,
                fecha_cosecha_estimada TEXT NOT NULL,
                estado TEXT DEFAULT 'Sembrado',
                FOREIGN KEY (parcela_id) REFERENCES parcelas (id)
            );
        """)
        conn.commit()

def registrar_usuario(username, email, password, rol_id):
    if len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (username, email, password_hash, rol_id) VALUES (?, ?, ?, ?)",
                (username, email, pwd_hash, rol_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("El usuario o correo ya se encuentra registrado.")

def registrar_parcela(nombre, ubicacion, tamano_m2):
    if tamano_m2 <= 0:
        raise ValueError("El tamaño en m² debe ser un número positivo mayor a 0.")
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO parcelas (nombre, ubicacion, tamano_m2) VALUES (?, ?, ?)",
            (nombre, ubicacion, tamano_m2)
        )
        conn.commit()

def registrar_cultivo(parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha):
    f_siembra = datetime.strptime(fecha_siembra, "%Y-%m-%d")
    f_cosecha = datetime.strptime(fecha_cosecha, "%Y-%m-%d")
    if f_cosecha <= f_siembra:
        raise ValueError("La fecha estimada de cosecha debe ser posterior a la fecha de siembra.")
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cultivos (parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha_estimada) VALUES (?, ?, ?, ?)",
            (parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha)
        )
        conn.commit()

def obtener_datos(tabla):
    with obtener_conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {tabla}")
        return cursor.fetchall()
