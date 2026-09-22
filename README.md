# AgroTech SmartFields

Prototipo de escritorio para gestionar parcelas, cultivos y usuarios agrícolas. La aplicación está construida con Python estándar, Tkinter/ttk y SQLite, sin dependencias externas.

## Requisitos

- Python 3.10 o superior.
- Windows, macOS o Linux con Tkinter disponible.

## Instalación y ejecución

1. Abrir una terminal en la carpeta del proyecto.
2. Ejecutar:

```powershell
python app.py
```

La base `agrotech.db` se crea automáticamente junto al código. En el primer inicio se puede crear el administrador inicial.

## Flujo lógico

```text
Inicio
  -> inicializar_bd()
  -> LoginWindow
  -> autenticar_usuario()
  -> cargar AgroTechApp con usuario y rol
  -> mostrar pestañas según permisos
  -> validar datos en la frontera
  -> ejecutar INSERT / UPDATE / DELETE parametrizados
  -> registrar auditoria
  -> actualizar Treeview y mostrar messagebox
```

Las lecturas se realizan mediante `SELECT`. Las operaciones de parcelas requieren un usuario activo con rol Administrador o Encargado de Producción. El Trabajador puede asignar y actualizar cultivos, pero no modificar parcelas ni eliminar cultivos. La administración de usuarios está reservada al Administrador.

## Arquitectura

- `app.py`: presentación y eventos Tkinter. Contiene login, control visual por rol, formularios, tablas y notificaciones.
- `database.py`: capa de persistencia desacoplada. Contiene esquema SQLite, validaciones, autenticación, autorización, CRUD y auditoría.
- `tests/test_database.py`: pruebas unitarias aisladas con `unittest` y bases temporales.
- `PLAN_PRUEBAS_UNITARIAS.md`: matriz institucional de casos y evidencia de ejecución.
- `agrotech.db`: base local generada en ejecución.

La conexión SQLite utiliza un context manager propio que activa `PRAGMA foreign_keys`, confirma transacciones exitosas, revierte errores y cierra siempre la conexión. Las consultas usan parámetros para evitar inyección SQL.

## Reglas de negocio y seguridad

- Superficie de parcela estrictamente mayor que cero.
- Campos de texto obligatorios.
- Fecha de cosecha estrictamente posterior a la fecha de siembra.
- Fechas en formato `AAAA-MM-DD`.
- Correo validado mediante `EMAIL_REGEX`.
- Contraseñas con mínimo 6 caracteres y almacenamiento SHA-256.
- Roles: `1` Administrador, `2` Encargado de Producción, `3` Trabajador (asignación y actualización de cultivos).
- Acciones agrícolas registradas en `auditoria` con usuario, acción, entidad y fecha.
- Los usuarios con historial no se eliminan físicamente, para conservar la trazabilidad; la aplicación muestra el error de integridad correspondiente.
- Cultivos eliminados automáticamente al eliminar su parcela (`ON DELETE CASCADE`).

## Manejo de errores

La capa de datos usa `ValueError` para entradas inválidas, `PermissionError` para roles no autorizados y `sqlite3.IntegrityError` para restricciones de base de datos. La interfaz captura esos errores y los presenta mediante `messagebox`.

## Pruebas

Ejecutar desde la raíz del proyecto:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado esperado:

```text
Ran 13 tests

OK
```

Las pruebas cubren parcelas, cultivos, fechas, superficie finita y positiva, campos obligatorios, correo, contraseña mínima en creación y actualización, SHA-256, autenticación y eliminación en cascada.
