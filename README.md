# 🌱 AgroTech SmartFields - Sistema de Gestión Agrícola

Sistema informático de escritorio desarrollado en **Python** para la digitalización y administración centralizada de parcelas, invernaderos, ciclos de cultivo y control de accesos por roles. Proyecto diseñado para optimizar las operaciones agrícolas en las regiones del Maule y Ñuble.

---

## 🚀 Características Principales (Etapa 1)

* **🌿 Gestión de Parcelas e Invernaderos (RF-01):** Registro y validación estricta de áreas en metros cuadrados ($m^2 > 0$), nombres y ubicaciones geográficas.
* **🌾 Control de Cultivos (RF-01):** Asignación y trazabilidad de ciclos de cultivo con validación cronológica (fechas de cosecha estimadas posteriores a la siembra).
* **👤 Gestión de Accesos y Seguridad (RF-02):**
  * Control de usuarios por perfiles (*Administrador*, *Encargado de Producción*, *Trabajador*).
  * Validación de formato RFC en correos institucionales.
  * Cifrado unidireccional de contraseñas mediante **SHA-256**.
* **🧪 Aseguramiento de Calidad (RF-03):** Suite de pruebas unitarias automatizadas con `unittest` para validación de lógica de negocio y sanitización de datos.
* **🗄️ Persistencia Relacional:** Base de datos relacional (SQLite) con claves primarias, foráneas e integridad referencial, compatible y administrable directamente desde **DBeaver**.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.x
* **Interfaz Gráfica:** Tkinter / TTK (Desktop Nativo)
* **Base de Datos:** SQLite / SQL Relacional (Administrado con DBeaver)
* **Seguridad:** Hash criptográfico SHA-256 (`hashlib`)
* **Testing:** Framework estándar `unittest`

---

## 📁 Estructura del Repositorio

```text
AgroTech_Desktop/
├── database.py           # Persistencia relacional, conexión SQLite y reglas de negocio
├── app.py                # Interfaz gráfica de escritorio (Tkinter)
├── test_suite.py         # Batería de pruebas unitarias automatizadas
├── agrotech_smartfields.db # Base de datos SQLite (generada al iniciar)
└── README.md             # Documentación del proyecto
