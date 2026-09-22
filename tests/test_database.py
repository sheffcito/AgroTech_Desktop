import hashlib
import tempfile
import unittest
from pathlib import Path

import database as db


class DatabaseUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "test_agrotech.db"
        db.inicializar_bd()
        db.registrar_usuario("admin", "admin@example.com", "claveSegura2026", 1)
        self.admin = db.autenticar_usuario("admin", "claveSegura2026")
        self.usuario_id = self.admin["id"]

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_tu_01_registro_valido_de_parcela(self):
        db.registrar_parcela("Invernadero Norte", "Sector Norte", 1250.5, self.usuario_id)
        parcelas = db.obtener_datos("parcelas")
        self.assertEqual(len(parcelas), 1)
        self.assertEqual(parcelas[0]["nombre"], "Invernadero Norte")
        self.assertEqual(parcelas[0]["tamano_m2"], 1250.5)

    def test_tu_02_rechaza_superficie_no_positiva(self):
        for superficie in (0, -50.0, float("nan"), float("inf")):
            with self.subTest(superficie=superficie):
                with self.assertRaisesRegex(ValueError, "estrictamente positiva"):
                    db.registrar_parcela("Parcela inválida", "Sector Norte", superficie, self.usuario_id)

    def test_tu_03_rechaza_campos_de_parcela_vacios(self):
        with self.assertRaisesRegex(ValueError, "obligatorio"):
            db.registrar_parcela("   ", "   ", 100, self.usuario_id)

    def test_tu_04_actualiza_parcela_y_registra_cultivo_valido(self):
        db.registrar_parcela("Parcela Norte", "Norte", 100, self.usuario_id)
        db.actualizar_parcela(1, "Invernadero Norte", "Sector Norte", 1250.5, self.usuario_id)
        db.registrar_cultivo(1, "Tomate", "2026-10-01", "2026-12-15", "Sembrado", self.usuario_id)
        parcela = db.obtener_datos("parcelas")[0]
        cultivo = db.obtener_datos("cultivos")[0]
        self.assertEqual(parcela["nombre"], "Invernadero Norte")
        self.assertEqual(cultivo["fecha_cosecha_estimada"], "2026-12-15")

    def test_tu_05_rechaza_cosecha_no_posterior(self):
        db.registrar_parcela("Parcela Norte", "Norte", 100, self.usuario_id)
        with self.assertRaisesRegex(ValueError, "posterior"):
            db.registrar_cultivo(1, "Tomate", "2026-11-01", "2026-10-01", "Sembrado", self.usuario_id)

    def test_tu_06_rechaza_formato_de_fecha_invalido(self):
        db.registrar_parcela("Parcela Norte", "Norte", 100, self.usuario_id)
        with self.assertRaisesRegex(ValueError, "AAAA-MM-DD"):
            db.registrar_cultivo(1, "Tomate", "01-10-2026", "2026-12-15", "Sembrado", self.usuario_id)

    def test_tu_07_rechaza_contrasena_menor_a_seis(self):
        with self.assertRaisesRegex(ValueError, "mínimo de 6"):
            db.registrar_usuario("corto", "corto@example.com", "12345", 3, self.usuario_id)

    def test_tu_08_rechaza_correo_invalido(self):
        with self.assertRaisesRegex(ValueError, "formato válido"):
            db.registrar_usuario("usuario", "correo_invalido_sin_dominio", "claveSegura", 3, self.usuario_id)

    def test_tu_09_hash_sha256_y_autenticacion(self):
        db.registrar_usuario("seguro", "seguro@example.com", "claveSegura2026", 3, self.usuario_id)
        usuario = db.obtener_datos("usuarios")[1]
        esperado = hashlib.sha256("claveSegura2026".encode("utf-8")).hexdigest()
        self.assertEqual(usuario["password_hash"], esperado)
        self.assertEqual(len(usuario["password_hash"]), 64)
        self.assertIsNotNone(db.autenticar_usuario("seguro", "claveSegura2026"))
        self.assertIsNone(db.autenticar_usuario("seguro", "incorrecta"))

    def test_tu_10_actualizacion_rechaza_contrasena_corta(self):
        with self.assertRaisesRegex(ValueError, "mínimo de 6"):
            db.actualizar_usuario(
                self.usuario_id,
                "admin",
                "admin@example.com",
                "12345",
                1,
                1,
                self.usuario_id,
            )

    def test_tu_11_eliminacion_de_parcela_elimina_cultivos_asociados(self):
        db.registrar_parcela("Parcela Norte", "Norte", 100, self.usuario_id)
        db.registrar_cultivo(1, "Tomate", "2026-10-01", "2026-12-15", "Sembrado", self.usuario_id)
        db.eliminar_parcela(1, self.usuario_id)
        self.assertEqual(db.obtener_datos("parcelas"), [])
        self.assertEqual(db.obtener_datos("cultivos"), [])

    def test_tu_12_preserva_auditoria_al_intentar_eliminar_usuario_activo(self):
        db.registrar_parcela("Parcela auditada", "Norte", 100, self.usuario_id)
        db.registrar_usuario("admin2", "admin2@example.com", "claveSegura", 1, self.usuario_id)
        admin2 = db.autenticar_usuario("admin2", "claveSegura")
        with self.assertRaises(db.sqlite3.IntegrityError):
            db.eliminar_usuario(self.usuario_id, admin2["id"])

    def test_tu_13_trabajador_puede_asignar_cultivo(self):
        db.registrar_parcela("Parcela de producción", "Norte", 100, self.usuario_id)
        db.registrar_usuario("trabajador", "trabajador@example.com", "claveSegura", 3, self.usuario_id)
        trabajador = db.autenticar_usuario("trabajador", "claveSegura")
        db.registrar_cultivo(
            1,
            "Lechuga",
            "2026-10-01",
            "2026-11-15",
            "Sembrado",
            trabajador["id"],
        )
        self.assertEqual(len(db.obtener_datos("cultivos")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
