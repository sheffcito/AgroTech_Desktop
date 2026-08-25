import tkinter as tk
from tkinter import ttk, messagebox
import database as db

class AgroTechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AgroTech SmartFields - Sistema de Escritorio")
        self.root.geometry("900x620")
        self.root.configure(bg="#f0f2f5")

        # Inicializar base de datos
        db.inicializar_bd()

        # Contenedor de pestañas
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Inicializar vistas
        self.crear_tab_parcelas()
        self.crear_tab_cultivos()
        self.crear_tab_usuarios()

        # Cargar datos en tablas
        self.recargar_todo()

    # ==================== PESTAÑA 1: PARCELAS ====================
    def crear_tab_parcelas(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="🌿 Parcelas e Invernaderos")

        frame_form = ttk.LabelFrame(tab, text="Registrar Parcela (RF-01)", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.p_nombre = ttk.Entry(frame_form, width=28)
        self.p_nombre.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Ubicación:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.p_ubicacion = ttk.Entry(frame_form, width=28)
        self.p_ubicacion.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Tamaño (m²):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.p_tamano = ttk.Entry(frame_form, width=28)
        self.p_tamano.grid(row=1, column=1, padx=5, pady=5)

        btn_guardar = ttk.Button(frame_form, text="Guardar Parcela", command=self.guardar_parcela)
        btn_guardar.grid(row=1, column=3, pady=5, sticky="e")

        self.tabla_parcelas = ttk.Treeview(tab, columns=("ID", "Nombre", "Ubicación", "Tamaño"), show="headings")
        for col in ("ID", "Nombre", "Ubicación", "Tamaño"):
            self.tabla_parcelas.heading(col, text=col)
            self.tabla_parcelas.column(col, anchor="center")
        self.tabla_parcelas.pack(fill="both", expand=True, padx=10, pady=5)

    def guardar_parcela(self):
        try:
            nombre = self.p_nombre.get().strip()
            ubicacion = self.p_ubicacion.get().strip()
            tamano_str = self.p_tamano.get().strip()

            if not nombre or not ubicacion or not tamano_str:
                raise ValueError("Todos los campos son obligatorios.")

            tamano = float(tamano_str)
            db.registrar_parcela(nombre, ubicacion, tamano)
            messagebox.showinfo("Éxito", "Parcela registrada correctamente.")
            self.p_nombre.delete(0, tk.END)
            self.p_ubicacion.delete(0, tk.END)
            self.p_tamano.delete(0, tk.END)
            self.recargar_todo()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ==================== PESTAÑA 2: CULTIVOS ====================
    def crear_tab_cultivos(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="🌾 Gestión de Cultivos")

        frame_form = ttk.LabelFrame(tab, text="Registrar Cultivo (RF-01)", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Parcela:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.c_parcela_combo = ttk.Combobox(frame_form, width=25, state="readonly")
        self.c_parcela_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Tipo Cultivo:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.c_tipo = ttk.Entry(frame_form, width=28)
        self.c_tipo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Siembra (AAAA-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.c_siembra = ttk.Entry(frame_form, width=28)
        self.c_siembra.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Cosecha (AAAA-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.c_cosecha = ttk.Entry(frame_form, width=28)
        self.c_cosecha.grid(row=1, column=3, padx=5, pady=5)

        btn_guardar = ttk.Button(frame_form, text="Registrar Cultivo", command=self.guardar_cultivo)
        btn_guardar.grid(row=2, column=3, pady=5, sticky="e")

        self.tabla_cultivos = ttk.Treeview(tab, columns=("ID", "Parcela ID", "Tipo", "Siembra", "Cosecha", "Estado"), show="headings")
        for col in ("ID", "Parcela ID", "Tipo", "Siembra", "Cosecha", "Estado"):
            self.tabla_cultivos.heading(col, text=col)
            self.tabla_cultivos.column(col, anchor="center")
        self.tabla_cultivos.pack(fill="both", expand=True, padx=10, pady=5)

    def guardar_cultivo(self):
        try:
            sel = self.c_parcela_combo.get()
            if not sel:
                raise ValueError("Debe seleccionar una parcela.")
            parcela_id = int(sel.split(" - ")[0])
            tipo = self.c_tipo.get().strip()
            siembra = self.c_siembra.get().strip()
            cosecha = self.c_cosecha.get().strip()

            if not tipo or not siembra or not cosecha:
                raise ValueError("Todos los campos son obligatorios.")

            db.registrar_cultivo(parcela_id, tipo, siembra, cosecha)
            messagebox.showinfo("Éxito", "Cultivo registrado correctamente.")
            self.c_tipo.delete(0, tk.END)
            self.c_siembra.delete(0, tk.END)
            self.c_cosecha.delete(0, tk.END)
            self.recargar_todo()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ==================== PESTAÑA 3: USUARIOS ====================
    def crear_tab_usuarios(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="👤 Usuarios y Accesos")

        frame_form = ttk.LabelFrame(tab, text="Registrar Usuario (RF-02)", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.u_user = ttk.Entry(frame_form, width=28)
        self.u_user.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Email:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.u_email = ttk.Entry(frame_form, width=28)
        self.u_email.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.u_pass = ttk.Entry(frame_form, width=28, show="*")
        self.u_pass.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Rol:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.u_rol = ttk.Combobox(frame_form, values=["1 - Administrador", "2 - Encargado de Producción", "3 - Trabajador"], state="readonly", width=25)
        self.u_rol.current(0)
        self.u_rol.grid(row=1, column=3, padx=5, pady=5)

        btn_guardar = ttk.Button(frame_form, text="Registrar Usuario", command=self.guardar_usuario)
        btn_guardar.grid(row=2, column=3, pady=5, sticky="e")

        self.tabla_usuarios = ttk.Treeview(tab, columns=("ID", "Usuario", "Email", "Rol ID", "Activo"), show="headings")
        for col in ("ID", "Usuario", "Email", "Rol ID", "Activo"):
            self.tabla_usuarios.heading(col, text=col)
            self.tabla_usuarios.column(col, anchor="center")
        self.tabla_usuarios.pack(fill="both", expand=True, padx=10, pady=5)

    def guardar_usuario(self):
        try:
            user = self.u_user.get().strip()
            email = self.u_email.get().strip()
            pwd = self.u_pass.get().strip()
            rol_id = int(self.u_rol.get().split(" - ")[0])

            if not user or not email or not pwd:
                raise ValueError("Todos los campos son obligatorios.")

            db.registrar_usuario(user, email, pwd, rol_id)
            messagebox.showinfo("Éxito", "Usuario creado con clave cifrada.")
            self.u_user.delete(0, tk.END)
            self.u_email.delete(0, tk.END)
            self.u_pass.delete(0, tk.END)
            self.recargar_todo()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # ==================== RECARGAR TABLAS ====================
    def recargar_todo(self):
        # Limpiar y poblar Parcelas
        for item in self.tabla_parcelas.get_children():
            self.tabla_parcelas.delete(item)
        parcelas = db.obtener_datos("parcelas")
        combo_vals = []
        for p in parcelas:
            self.tabla_parcelas.insert("", "end", values=(p["id"], p["nombre"], p["ubicacion"], f"{p['tamano_m2']} m²"))
            combo_vals.append(f"{p['id']} - {p['nombre']}")
        self.c_parcela_combo["values"] = combo_vals

        # Limpiar y poblar Cultivos
        for item in self.tabla_cultivos.get_children():
            self.tabla_cultivos.delete(item)
        for c in db.obtener_datos("cultivos"):
            self.tabla_cultivos.insert("", "end", values=(c["id"], c["parcela_id"], c["tipo_cultivo"], c["fecha_siembra"], c["fecha_cosecha_estimada"], c["estado"]))

        # Limpiar y poblar Usuarios
        for item in self.tabla_usuarios.get_children():
            self.tabla_usuarios.delete(item)
        for u in db.obtener_datos("usuarios"):
            self.tabla_usuarios.insert("", "end", values=(u["id"], u["username"], u["email"], u["rol_id"], "Sí" if u["activo"] else "No"))

# ==================== EJECUCIÓN PRINCIPAL ====================
if __name__ == "__main__":
    ventana = tk.Tk()
    aplicacion = AgroTechApp(ventana)
    ventana.mainloop()