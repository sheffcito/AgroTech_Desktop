# Plan de Pruebas Unitarias RF-05

Suite implementada con `unittest` en [tests/test_database.py](tests/test_database.py).
Cada caso utiliza una base SQLite temporal independiente para evitar dependencia de datos previos.

| ID Prueba | Módulo / Entidad | Caso de prueba | Datos de entrada | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|---|
| TU-01 | Parcelas | Registro válido | `Invernadero Norte`, `1250.5 m²` | Inserción sin errores | Parcela almacenada y recuperada | Aprobado / Pass |
| TU-02 | Parcelas | Superficie no positiva | `0` y `-50.0` | Lanza `ValueError` | Excepción capturada | Aprobado / Pass |
| TU-03 | Parcelas | Campos vacíos | Nombre y ubicación con espacios | Lanza `ValueError` por campos obligatorios | Excepción capturada | Aprobado / Pass |
| TU-04 | Parcelas / Cultivos | Actualización y registro válido | Siembra `2026-10-01`, cosecha `2026-12-15` | Actualización e inserción exitosas | Datos actualizados y cultivo asociado | Aprobado / Pass |
| TU-05 | Cultivos | Cosecha anterior a siembra | Siembra `2026-11-01`, cosecha `2026-10-01` | Lanza `ValueError` | Excepción capturada | Aprobado / Pass |
| TU-06 | Cultivos | Fecha inválida | `01-10-2026` | Lanza `ValueError` con formato `AAAA-MM-DD` | Excepción capturada | Aprobado / Pass |
| TU-07 | Usuarios | Contraseña menor a 6 caracteres | `12345` | Lanza `ValueError` | Excepción capturada | Aprobado / Pass |
| TU-08 | Usuarios | Correo inválido | `correo_invalido_sin_dominio` | Lanza `ValueError` | Excepción capturada | Aprobado / Pass |
| TU-09 | Seguridad | SHA-256 y autenticación | `claveSegura2026` | Digest de 64 caracteres; login válido e inválido | Hash verificado; autenticación correcta y fallida | Aprobado / Pass |
| TU-10 | Usuarios | Actualización con contraseña corta | `12345` (< 6 caracteres) | Lanza `ValueError` | Excepción capturada | Aprobado / Pass |
| TU-11 | Cultivos / Integridad | Eliminación en cascada | Parcela con cultivo asociado | Elimina parcela y cultivos dependientes | Ambas tablas quedan sin registros | Aprobado / Pass |
| TU-12 | Seguridad / Auditoría | Conservación del historial | Usuario con operaciones auditadas | Impide borrar al usuario y conserva la auditoría | `IntegrityError` capturado | Aprobado / Pass |
| TU-13 | Usuarios / Cultivos | Trabajador asigna cultivo | Usuario rol 3 y parcela existente | Inserta cultivo asociado sin permitir gestión de parcelas | Cultivo almacenado correctamente | Aprobado / Pass |

## Ejecución

Comando utilizado:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado obtenido:

```text
Ran 13 tests in 0.426s

OK
```
