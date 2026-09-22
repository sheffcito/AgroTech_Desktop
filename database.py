"""Persistencia SQLite, validaciones de dominio, seguridad y auditoría."""

import hashlib
import hmac
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "agrotech.db"
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLES = {1: "Administrador", 2: "Encargado de Producción", 3: "Trabajador"}


@contextmanager
def _conexion():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar_bd():
    """Crea el esquema, activa claves foráneas y registra los roles base."""
    with _conexion() as conexion:
        conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS parcelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ubicacion TEXT NOT NULL,
                tamano_m2 REAL NOT NULL CHECK (tamano_m2 > 0)
            );
            CREATE TABLE IF NOT EXISTS cultivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcela_id INTEGER NOT NULL,
                tipo_cultivo TEXT NOT NULL,
                fecha_siembra TEXT NOT NULL,
                fecha_cosecha_estimada TEXT NOT NULL,
                estado TEXT NOT NULL,
                FOREIGN KEY (parcela_id) REFERENCES parcelas(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol_id INTEGER NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (rol_id) REFERENCES roles(id)
            );
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                accion TEXT NOT NULL,
                entidad TEXT NOT NULL,
                entidad_id INTEGER,
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
            """
        )
        _migrar_auditoria_sin_cascada(conexion)
        conexion.executemany(
            "INSERT OR IGNORE INTO roles (id, nombre) VALUES (?, ?)", ROLES.items()
        )


def _migrar_auditoria_sin_cascada(conexion):
    """Actualiza instalaciones antiguas para conservar el historial de auditoría."""
    relaciones = conexion.execute("PRAGMA foreign_key_list(auditoria)").fetchall()
    usa_cascada = any(relacion[6].upper() == "CASCADE" for relacion in relaciones)
    if not usa_cascada:
        return
    conexion.execute("ALTER TABLE auditoria RENAME TO auditoria_antigua")
    conexion.execute(
        """CREATE TABLE auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            accion TEXT NOT NULL,
            entidad TEXT NOT NULL,
            entidad_id INTEGER,
            fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )"""
    )
    conexion.execute(
        """INSERT INTO auditoria (id, usuario_id, accion, entidad, entidad_id, fecha)
           SELECT id, usuario_id, accion, entidad, entidad_id, fecha
           FROM auditoria_antigua"""
    )
    conexion.execute("DROP TABLE auditoria_antigua")


def _texto_obligatorio(valor, campo):
    """Normaliza un texto y rechaza valores vacíos."""
    valor = str(valor).strip()
    if not valor:
        raise ValueError(f"El campo {campo} es obligatorio.")
    return valor


def _fecha_valida(valor, campo):
    """Convierte una fecha ISO y entrega un error de dominio si es inválida."""
    valor = _texto_obligatorio(valor, campo)
    try:
        return date.fromisoformat(valor)
    except ValueError as error:
        raise ValueError(f"{campo} debe tener formato AAAA-MM-DD.") from error


def _usuario_autorizado(usuario_id, roles_permitidos):
    """Verifica que el usuario exista, esté activo y tenga un rol permitido."""
    with _conexion() as conexion:
        usuario = conexion.execute(
            "SELECT id, rol_id, activo FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    if usuario is None or not usuario["activo"] or usuario["rol_id"] not in roles_permitidos:
        raise PermissionError("Su rol no tiene permisos para realizar esta acción.")
    return usuario


def _registrar_auditoria(conexion, usuario_id, accion, entidad, entidad_id):
    """Guarda quién ejecutó una operación sobre una entidad."""
    conexion.execute(
        """INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id)
           VALUES (?, ?, ?, ?)""",
        (usuario_id, accion, entidad, entidad_id),
    )


def registrar_parcela(nombre, ubicacion, tamano_m2, usuario_id=None):
    """Registra una parcela validada y crea su evento de auditoría."""
    _usuario_autorizado(usuario_id, {1, 2})
    nombre = _texto_obligatorio(nombre, "nombre")
    ubicacion = _texto_obligatorio(ubicacion, "ubicación")
    tamano_m2 = float(tamano_m2)
    if not math.isfinite(tamano_m2) or tamano_m2 <= 0:
        raise ValueError("La superficie debe ser estrictamente positiva.")
    with _conexion() as conexion:
        cursor = conexion.execute(
            "INSERT INTO parcelas (nombre, ubicacion, tamano_m2) VALUES (?, ?, ?)",
            (nombre, ubicacion, tamano_m2),
        )
        _registrar_auditoria(conexion, usuario_id, "CREAR", "parcela", cursor.lastrowid)


def actualizar_parcela(parcela_id, nombre, ubicacion, tamano_m2, usuario_id=None):
    """Actualiza una parcela existente si el rol está autorizado."""
    _usuario_autorizado(usuario_id, {1, 2})
    nombre = _texto_obligatorio(nombre, "nombre")
    ubicacion = _texto_obligatorio(ubicacion, "ubicación")
    tamano_m2 = float(tamano_m2)
    if not math.isfinite(tamano_m2) or tamano_m2 <= 0:
        raise ValueError("La superficie debe ser estrictamente positiva.")
    with _conexion() as conexion:
        cursor = conexion.execute(
            "UPDATE parcelas SET nombre = ?, ubicacion = ?, tamano_m2 = ? WHERE id = ?",
            (nombre, ubicacion, tamano_m2, parcela_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("La parcela seleccionada no existe.")
        _registrar_auditoria(conexion, usuario_id, "ACTUALIZAR", "parcela", parcela_id)


def eliminar_parcela(parcela_id, usuario_id=None):
    """Elimina una parcela y sus cultivos mediante cascada SQLite."""
    _usuario_autorizado(usuario_id, {1, 2})
    with _conexion() as conexion:
        conexion.execute("DELETE FROM parcelas WHERE id = ?", (parcela_id,))
        _registrar_auditoria(conexion, usuario_id, "ELIMINAR", "parcela", parcela_id)


def registrar_cultivo(parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha, estado, usuario_id=None):
    """Registra un cultivo con fechas cronológicamente consistentes."""
    _usuario_autorizado(usuario_id, {1, 2, 3})
    tipo_cultivo = _texto_obligatorio(tipo_cultivo, "cultivo")
    siembra = _fecha_valida(fecha_siembra, "La fecha de siembra")
    cosecha = _fecha_valida(fecha_cosecha, "La fecha de cosecha")
    if cosecha <= siembra:
        raise ValueError("La cosecha debe ser posterior a la siembra.")
    estado = _texto_obligatorio(estado, "estado")
    with _conexion() as conexion:
        cursor = conexion.execute(
            """INSERT INTO cultivos
               (parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha_estimada, estado)
               VALUES (?, ?, ?, ?, ?)""",
            (parcela_id, tipo_cultivo, siembra.isoformat(), cosecha.isoformat(), estado),
        )
        _registrar_auditoria(conexion, usuario_id, "CREAR", "cultivo", cursor.lastrowid)


def actualizar_cultivo(cultivo_id, parcela_id, tipo_cultivo, fecha_siembra, fecha_cosecha, estado, usuario_id=None):
    """Actualiza un cultivo validando parcela, fechas y estado."""
    _usuario_autorizado(usuario_id, {1, 2, 3})
    tipo_cultivo = _texto_obligatorio(tipo_cultivo, "cultivo")
    siembra = _fecha_valida(fecha_siembra, "La fecha de siembra")
    cosecha = _fecha_valida(fecha_cosecha, "La fecha de cosecha")
    if cosecha <= siembra:
        raise ValueError("La cosecha debe ser posterior a la siembra.")
    estado = _texto_obligatorio(estado, "estado")
    with _conexion() as conexion:
        cursor = conexion.execute(
            """UPDATE cultivos SET parcela_id = ?, tipo_cultivo = ?, fecha_siembra = ?,
               fecha_cosecha_estimada = ?, estado = ? WHERE id = ?""",
            (parcela_id, tipo_cultivo, siembra.isoformat(), cosecha.isoformat(), estado, cultivo_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("El cultivo seleccionado no existe.")
        _registrar_auditoria(conexion, usuario_id, "ACTUALIZAR", "cultivo", cultivo_id)


def eliminar_cultivo(cultivo_id, usuario_id=None):
    """Elimina un cultivo y registra la operación."""
    _usuario_autorizado(usuario_id, {1, 2})
    with _conexion() as conexion:
        conexion.execute("DELETE FROM cultivos WHERE id = ?", (cultivo_id,))
        _registrar_auditoria(conexion, usuario_id, "ELIMINAR", "cultivo", cultivo_id)


def registrar_usuario(username, email, password, rol_id, usuario_id=None):
    """Crea un usuario con correo validado y contraseña SHA-256."""
    if usuario_id is not None:
        _usuario_autorizado(usuario_id, {1})
    username = _texto_obligatorio(username, "usuario")
    email = _texto_obligatorio(email, "correo")
    password = _texto_obligatorio(password, "contraseña")
    if len(password) < 6:
        raise ValueError("La contraseña debe tener un mínimo de 6 caracteres.")
    if not EMAIL_REGEX.fullmatch(email):
        raise ValueError("El correo electrónico no tiene un formato válido.")
    if rol_id not in ROLES:
        raise ValueError("El rol seleccionado no es válido.")
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with _conexion() as conexion:
        conexion.execute(
            """INSERT INTO usuarios (username, email, password_hash, rol_id)
               VALUES (?, ?, ?, ?)""",
            (username, email, password_hash, rol_id),
        )


def actualizar_usuario(usuario_id, username, email, password=None, rol_id=None, activo=None, actor_id=None):
    """Actualiza datos de usuario; solo un administrador puede ejecutarlo."""
    _usuario_autorizado(actor_id, {1})
    username = _texto_obligatorio(username, "usuario")
    email = _texto_obligatorio(email, "correo")
    if not EMAIL_REGEX.fullmatch(email):
        raise ValueError("El correo electrónico no tiene un formato válido.")
    if rol_id not in ROLES:
        raise ValueError("El rol seleccionado no es válido.")
    if activo not in (0, 1, False, True):
        raise ValueError("El estado del usuario no es válido.")
    campos = ["username = ?", "email = ?", "rol_id = ?", "activo = ?"]
    valores = [username, email, rol_id, int(activo)]
    if password:
        if len(password) < 6:
            raise ValueError("La contraseña debe tener un mínimo de 6 caracteres.")
        campos.append("password_hash = ?")
        valores.append(hashlib.sha256(password.encode("utf-8")).hexdigest())
    valores.append(usuario_id)
    with _conexion() as conexion:
        cursor = conexion.execute(
            f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores
        )
        if cursor.rowcount == 0:
            raise ValueError("El usuario seleccionado no existe.")
        _registrar_auditoria(conexion, actor_id, "ACTUALIZAR", "usuario", usuario_id)


def eliminar_usuario(usuario_id, actor_id=None):
    """Elimina otro usuario; impide que el administrador se elimine a sí mismo."""
    _usuario_autorizado(actor_id, {1})
    if usuario_id == actor_id:
        raise ValueError("No puede eliminar su propia cuenta durante la sesión.")
    with _conexion() as conexion:
        cursor = conexion.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        if cursor.rowcount == 0:
            raise ValueError("El usuario seleccionado no existe.")
        _registrar_auditoria(conexion, actor_id, "ELIMINAR", "usuario", usuario_id)


def contar_usuarios():
    """Devuelve la cantidad de usuarios registrados."""
    with _conexion() as conexion:
        return conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


def autenticar_usuario(username, password):
    """Autentica credenciales y devuelve el usuario activo o `None`."""
    username = _texto_obligatorio(username, "usuario")
    password = _texto_obligatorio(password, "contraseña")
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with _conexion() as conexion:
        usuario = conexion.execute(
            """SELECT id, username, email, password_hash, rol_id, activo
               FROM usuarios WHERE username = ?""",
            (username,),
        ).fetchone()
    if usuario is None or not usuario["activo"]:
        return None
    if not hmac.compare_digest(usuario["password_hash"], password_hash):
        return None
    return dict(usuario)


def obtener_datos(tabla):
    """Lee una tabla permitida y devuelve sus filas como diccionarios."""
    tablas_permitidas = {"parcelas", "cultivos", "usuarios"}
    if tabla not in tablas_permitidas:
        raise ValueError("Tabla no permitida.")
    with _conexion() as conexion:
        filas = conexion.execute(f"SELECT * FROM {tabla} ORDER BY id").fetchall()
        return [dict(fila) for fila in filas]
