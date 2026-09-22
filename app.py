import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
import database as db


class LoginWindow:
    """Ventana inicial que autentica al usuario antes de abrir el sistema."""

    def __init__(self, root):
        self.root = root
        self.root.title("AgroTech SmartFields - Acceso")
        self.root.geometry("420x300")
        self.root.resizable(False, False)
        db.inicializar_bd()

        frame = ttk.LabelFrame(root, text="Inicio de sesión", padding=20)
        frame.pack(fill="both", expand=True, padx=25, pady=25)
        ttk.Label(frame, text="Usuario:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
        self.usuario = ttk.Entry(frame, width=28)
        self.usuario.grid(row=0, column=1, padx=5, pady=8)
        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, padx=5, pady=8, sticky="e")
        self.password = ttk.Entry(frame, width=28, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=8)
        ttk.Button(frame, text="Ingresar", command=self.iniciar_sesion).grid(
            row=2, column=1, padx=5, pady=12, sticky="e"
        )
        if db.contar_usuarios() == 0:
            ttk.Button(frame, text="Crear administrador inicial", command=self.crear_administrador).grid(
                row=3, column=0, columnspan=2, pady=5
            )
        self.usuario.focus_set()
        self.root.bind("<Return>", lambda event: self.iniciar_sesion())

    def iniciar_sesion(self):
        try:
            usuario = db.autenticar_usuario(self.usuario.get(), self.password.get())
        except ValueError as error:
            messagebox.showerror("Acceso", str(error))
            return
        if usuario is None:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            self.password.delete(0, tk.END)
            return
        self.root.unbind("<Return>")
        for widget in self.root.winfo_children():
            widget.destroy()
        AgroTechApp(self.root, usuario)

    def crear_administrador(self):
        ventana = tk.Toplevel(self.root)
        ventana.title("Administrador inicial")
        ventana.resizable(False, False)
        frame = ttk.Frame(ventana, padding=15)
        frame.pack()
        campos = {}
        for fila, (etiqueta, clave, ocultar) in enumerate(
            (("Usuario:", "usuario", False), ("Correo:", "correo", False), ("Contraseña:", "password", True))
        ):
            ttk.Label(frame, text=etiqueta).grid(row=fila, column=0, padx=5, pady=5, sticky="e")
            entrada = ttk.Entry(frame, width=28, show="*" if ocultar else "")
            entrada.grid(row=fila, column=1, padx=5, pady=5)
            campos[clave] = entrada

        def guardar():
            if db.contar_usuarios() != 0:
                ventana.destroy()
                return
            try:
                db.registrar_usuario(
                    campos["usuario"].get(), campos["correo"].get(), campos["password"].get(), 1
                )
            except (ValueError, sqlite3.IntegrityError) as error:
                messagebox.showerror("Error", str(error), parent=ventana)
                return
            ventana.destroy()
            messagebox.showinfo("Administrador creado", "Ya puede iniciar sesión.", parent=self.root)

        ttk.Button(frame, text="Crear", command=guardar).grid(row=3, column=1, pady=10, sticky="e")


class AgroTechApp:
    """Interfaz principal de gestión agrícola protegida por roles."""

    def __init__(self, root, usuario):
        self.root = root
        self.usuario_actual = usuario
        self.rol_id = usuario["rol_id"]
        self.root.title(f"AgroTech SmartFields - {db.ROLES[self.rol_id]}")
        self.root.geometry("950x650")
        self.root.configure(bg="#f4f6f9")

        db.inicializar_bd()

        # Variables de seguimiento de seleccion para edicion
        self.parcela_seleccionada_id = None
        self.cultivo_seleccionado_id = None
        self.usuario_seleccionado_id = None

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(self.root, text="Cerrar sesión", command=self.cerrar_sesion).pack(
            anchor="ne", padx=10, pady=(0, 5)
        )

        self.crear_tab_parcelas()
        self.crear_tab_cultivos()
        if self.rol_id == 1:
            self.crear_tab_usuarios()

        self.recargar_todo()
        self.aplicar_permisos()

    def aplicar_permisos(self):
        if self.rol_id == 3:
            for boton in (
                self.btn_nueva_parcela,
                self.btn_actualizar_parcela,
                self.btn_eliminar_parcela,
                self.btn_eliminar_cultivo,
            ):
                boton.configure(state="disabled")

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar la sesión actual?"):
            for widget in self.root.winfo_children():
                widget.destroy()
            LoginWindow(self.root)

    # ==================== PESTAÑA PARCELAS (CRUD) ====================
    def crear_tab_parcelas(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="🌿 Parcelas e Invernaderos (CRUD)")

        frame_form = ttk.LabelFrame(tab, text="Formulario de Parcela", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.p_nombre = ttk.Entry(frame_form, width=25)
        self.p_nombre.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Ubicación:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.p_ubicacion = ttk.Entry(frame_form, width=25)
        self.p_ubicacion.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Tamaño (m²):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.p_tamano = ttk.Entry(frame_form, width=25)
        self.p_tamano.grid(row=1, column=1, padx=5, pady=5)

        # Botonera CRUD
        frame_botones = ttk.Frame(frame_form)
        frame_botones.grid(row=1, column=2, columnspan=2, pady=5, sticky="e")

        self.btn_nueva_parcela = ttk.Button(frame_botones, text="Guardar Nuevo", command=self.guardar_parcela)
        self.btn_nueva_parcela.pack(side="left", padx=2)
        self.btn_actualizar_parcela = ttk.Button(frame_botones, text="Actualizar", command=self.actualizar_parcela)
        self.btn_actualizar_parcela.pack(side="left", padx=2)
        self.btn_eliminar_parcela = ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_parcela)
        self.btn_eliminar_parcela.pack(side="left", padx=2)
        ttk.Button(frame_botones, text="Limpiar", command=self.limpiar_form_parcela).pack(side="left", padx=2)

        # Tabla
        self.tabla_parcelas = ttk.Treeview(tab, columns=("ID", "Nombre", "Ubicación", "Tamaño"), show="headings", height=12)
        anchos_parcelas = {"ID": 55, "Nombre": 220, "Ubicación": 260, "Tamaño": 110}
        for col in ("ID", "Nombre", "Ubicación", "Tamaño"):
            self.tabla_parcelas.heading(col, text=col)
            self.tabla_parcelas.column(col, width=anchos_parcelas[col], minwidth=anchos_parcelas[col], anchor="center", stretch=False)
        self.tabla_parcelas.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabla_parcelas.bind("<<TreeviewSelect>>", self.cargar_parcela_seleccionada)

    def cargar_parcela_seleccionada(self, event):
        item = self.tabla_parcelas.focus()
        if item:
            valores = self.tabla_parcelas.item(item, "values")
            self.parcela_seleccionada_id = int(valores[0])
            self.p_nombre.delete(0, tk.END)
            self.p_nombre.insert(0, valores[1])
            self.p_ubicacion.delete(0, tk.END)
            self.p_ubicacion.insert(0, valores[2])
            self.p_tamano.delete(0, tk.END)
            self.p_tamano.insert(0, valores[3].replace(" m²", ""))

    def limpiar_form_parcela(self):
        self.parcela_seleccionada_id = None
        self.p_nombre.delete(0, tk.END)
        self.p_ubicacion.delete(0, tk.END)
        self.p_tamano.delete(0, tk.END)

    def guardar_parcela(self):
        try:
            nombre = self.p_nombre.get()
            ubicacion = self.p_ubicacion.get()
            tamano = float(self.p_tamano.get())
            db.registrar_parcela(nombre, ubicacion, tamano, self.usuario_actual["id"])
            messagebox.showinfo("Éxito", "Parcela registrada correctamente.")
            self.limpiar_form_parcela()
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Error", str(e))

    def actualizar_parcela(self):
        if not self.parcela_seleccionada_id:
            messagebox.showwarning("Atención", "Seleccione una parcela de la tabla para editar.")
            return
        try:
            nombre = self.p_nombre.get()
            ubicacion = self.p_ubicacion.get()
            tamano = float(self.p_tamano.get())
            db.actualizar_parcela(self.parcela_seleccionada_id, nombre, ubicacion, tamano, self.usuario_actual["id"])
            messagebox.showinfo("Éxito", "Parcela actualizada correctamente.")
            self.limpiar_form_parcela()
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Error", str(e))

    def eliminar_parcela(self):
        if not self.parcela_seleccionada_id:
            messagebox.showwarning("Atención", "Seleccione una parcela de la tabla para eliminar.")
            return
        if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar esta parcela? Todos sus cultivos asociados se eliminarán también."):
            try:
                db.eliminar_parcela(self.parcela_seleccionada_id, self.usuario_actual["id"])
            except (ValueError, PermissionError, sqlite3.IntegrityError) as error:
                messagebox.showerror("Error", str(error))
                return
            messagebox.showinfo("Éxito", "Parcela eliminada.")
            self.limpiar_form_parcela()
            self.recargar_todo()

    # ==================== PESTAÑA CULTIVOS (CRUD) ====================
    def crear_tab_cultivos(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="🌾 Gestión de Cultivos (CRUD)")

        frame_form = ttk.LabelFrame(tab, text="Formulario de Cultivo", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Parcela:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.c_parcela_combo = ttk.Combobox(frame_form, width=23, state="readonly")
        self.c_parcela_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Cultivo:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.c_tipo = ttk.Entry(frame_form, width=25)
        self.c_tipo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Siembra (AAAA-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.c_siembra = ttk.Entry(frame_form, width=25)
        self.c_siembra.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Cosecha (AAAA-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.c_cosecha = ttk.Entry(frame_form, width=25)
        self.c_cosecha.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Estado:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.c_estado = ttk.Combobox(frame_form, values=["Sembrado", "En Crecimiento", "Listo para Cosecha", "Cosechado"], state="readonly", width=23)
        self.c_estado.current(0)
        self.c_estado.grid(row=2, column=1, padx=5, pady=5)

        frame_botones = ttk.Frame(frame_form)
        frame_botones.grid(row=2, column=2, columnspan=2, pady=5, sticky="e")

        self.btn_nuevo_cultivo = ttk.Button(frame_botones, text="Guardar Nuevo", command=self.guardar_cultivo)
        self.btn_nuevo_cultivo.pack(side="left", padx=2)
        self.btn_actualizar_cultivo = ttk.Button(frame_botones, text="Actualizar", command=self.actualizar_cultivo)
        self.btn_actualizar_cultivo.pack(side="left", padx=2)
        self.btn_eliminar_cultivo = ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_cultivo)
        self.btn_eliminar_cultivo.pack(side="left", padx=2)
        ttk.Button(frame_botones, text="Limpiar", command=self.limpiar_form_cultivo).pack(side="left", padx=2)

        self.tabla_cultivos = ttk.Treeview(tab, columns=("ID", "Parcela ID", "Cultivo", "Siembra", "Cosecha", "Estado"), show="headings", height=12)
        anchos_cultivos = {"ID": 55, "Parcela ID": 90, "Cultivo": 210, "Siembra": 120, "Cosecha": 120, "Estado": 180}
        for col in ("ID", "Parcela ID", "Cultivo", "Siembra", "Cosecha", "Estado"):
            self.tabla_cultivos.heading(col, text=col)
            self.tabla_cultivos.column(col, width=anchos_cultivos[col], minwidth=anchos_cultivos[col], anchor="center", stretch=False)
        self.tabla_cultivos.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabla_cultivos.bind("<<TreeviewSelect>>", self.cargar_cultivo_seleccionado)

    def cargar_cultivo_seleccionado(self, event):
        item = self.tabla_cultivos.focus()
        if item:
            val = self.tabla_cultivos.item(item, "values")
            self.cultivo_seleccionado_id = int(val[0])
            parcela_id_actual = val[1]
            for v in self.c_parcela_combo["values"]:
                if v.startswith(f"{parcela_id_actual} -"):
                    self.c_parcela_combo.set(v)
                    break
            self.c_tipo.delete(0, tk.END)
            self.c_tipo.insert(0, val[2])
            self.c_siembra.delete(0, tk.END)
            self.c_siembra.insert(0, val[3])
            self.c_cosecha.delete(0, tk.END)
            self.c_cosecha.insert(0, val[4])
            self.c_estado.set(val[5])

    def limpiar_form_cultivo(self):
        self.cultivo_seleccionado_id = None
        self.c_tipo.delete(0, tk.END)
        self.c_siembra.delete(0, tk.END)
        self.c_cosecha.delete(0, tk.END)
        self.c_estado.current(0)

    def guardar_cultivo(self):
        try:
            sel = self.c_parcela_combo.get()
            if not sel:
                raise ValueError("Seleccione una parcela.")
            p_id = int(sel.split(" - ")[0])
            db.registrar_cultivo(p_id, self.c_tipo.get(), self.c_siembra.get(), self.c_cosecha.get(), self.c_estado.get(), self.usuario_actual["id"])
            messagebox.showinfo("Éxito", "Cultivo registrado.")
            self.limpiar_form_cultivo()
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Error", str(e))

    def actualizar_cultivo(self):
        if not self.cultivo_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cultivo de la tabla para editar.")
            return
        try:
            sel = self.c_parcela_combo.get()
            if not sel:
                raise ValueError("Seleccione una parcela válida.")
            p_id = int(sel.split(" - ")[0])
            db.actualizar_cultivo(self.cultivo_seleccionado_id, p_id, self.c_tipo.get(), self.c_siembra.get(), self.c_cosecha.get(), self.c_estado.get(), self.usuario_actual["id"])
            messagebox.showinfo("Éxito", "Cultivo actualizado.")
            self.limpiar_form_cultivo()
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Error", str(e))

    def eliminar_cultivo(self):
        if not self.cultivo_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un cultivo de la tabla para eliminar.")
            return
        if messagebox.askyesno("Confirmar", "¿Desea eliminar el cultivo seleccionado?"):
            try:
                db.eliminar_cultivo(self.cultivo_seleccionado_id, self.usuario_actual["id"])
            except (ValueError, PermissionError, sqlite3.IntegrityError) as error:
                messagebox.showerror("Error", str(error))
                return
            messagebox.showinfo("Éxito", "Cultivo eliminado.")
            self.limpiar_form_cultivo()
            self.recargar_todo()

    # ==================== PESTAÑA USUARIOS ====================
    def crear_tab_usuarios(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="👤 Usuarios y Accesos")

        frame_form = ttk.LabelFrame(tab, text="Registrar Usuario", padding=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_form, text="Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.u_user = ttk.Entry(frame_form, width=25)
        self.u_user.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Email:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.u_email = ttk.Entry(frame_form, width=25)
        self.u_email.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame_form, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.u_pass = ttk.Entry(frame_form, width=25, show="*")
        self.u_pass.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Rol:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.u_rol = ttk.Combobox(frame_form, values=["1 - Administrador", "2 - Encargado de Producción", "3 - Trabajador"], state="readonly", width=23)
        self.u_rol.current(0)
        self.u_rol.grid(row=1, column=3, padx=5, pady=5)

        btn_guardar = ttk.Button(frame_form, text="Registrar Usuario", command=self.guardar_usuario)
        btn_guardar.grid(row=2, column=3, pady=5, sticky="e")
        ttk.Button(frame_form, text="Actualizar seleccionado", command=self.actualizar_usuario).grid(row=3, column=1, pady=5)
        ttk.Button(frame_form, text="Eliminar seleccionado", command=self.eliminar_usuario).grid(row=3, column=3, pady=5, sticky="e")

        self.tabla_usuarios = ttk.Treeview(tab, columns=("ID", "Usuario", "Email", "Rol ID", "Activo"), show="headings", height=12)
        anchos_usuarios = {"ID": 55, "Usuario": 180, "Email": 300, "Rol ID": 90, "Activo": 90}
        for col in ("ID", "Usuario", "Email", "Rol ID", "Activo"):
            self.tabla_usuarios.heading(col, text=col)
            self.tabla_usuarios.column(col, width=anchos_usuarios[col], minwidth=anchos_usuarios[col], anchor="center", stretch=False)
        self.tabla_usuarios.pack(fill="both", expand=True, padx=10, pady=5)
        self.tabla_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

    def cargar_usuario_seleccionado(self, event):
        item = self.tabla_usuarios.focus()
        if item:
            valores = self.tabla_usuarios.item(item, "values")
            self.usuario_seleccionado_id = int(valores[0])
            self.u_user.delete(0, tk.END)
            self.u_user.insert(0, valores[1])
            self.u_email.delete(0, tk.END)
            self.u_email.insert(0, valores[2])
            self.u_rol.set(f"{valores[3]} - {db.ROLES[int(valores[3])]}")

    def actualizar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario para actualizar.")
            return
        try:
            db.actualizar_usuario(
                self.usuario_seleccionado_id,
                self.u_user.get(),
                self.u_email.get(),
                self.u_pass.get(),
                int(self.u_rol.get().split(" - ")[0]),
                1,
                self.usuario_actual["id"],
            )
            messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
            self.usuario_seleccionado_id = None
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Error", str(error))

    def eliminar_usuario(self):
        if not self.usuario_seleccionado_id:
            messagebox.showwarning("Atención", "Seleccione un usuario para eliminar.")
            return
        if messagebox.askyesno("Confirmar", "¿Desea eliminar el usuario seleccionado?"):
            try:
                db.eliminar_usuario(self.usuario_seleccionado_id, self.usuario_actual["id"])
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.usuario_seleccionado_id = None
                self.recargar_todo()
            except (ValueError, PermissionError, sqlite3.IntegrityError) as error:
                messagebox.showerror("Error", str(error))

    def guardar_usuario(self):
        try:
            rol_id = int(self.u_rol.get().split(" - ")[0])
            db.registrar_usuario(self.u_user.get(), self.u_email.get(), self.u_pass.get(), rol_id, self.usuario_actual["id"])
            messagebox.showinfo("Éxito", "Usuario registrado exitosamente.")
            self.u_user.delete(0, tk.END)
            self.u_email.delete(0, tk.END)
            self.u_pass.delete(0, tk.END)
            self.recargar_todo()
        except (ValueError, PermissionError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Error", str(e))

    # ==================== RECARGA GENERAL ====================
    def recargar_todo(self):
        for item in self.tabla_parcelas.get_children():
            self.tabla_parcelas.delete(item)
        parcelas = db.obtener_datos("parcelas")
        combo_vals = []
        for p in parcelas:
            self.tabla_parcelas.insert("", "end", values=(p["id"], p["nombre"], p["ubicacion"], f"{p['tamano_m2']} m²"))
            combo_vals.append(f"{p['id']} - {p['nombre']}")
        self.c_parcela_combo["values"] = combo_vals

        for item in self.tabla_cultivos.get_children():
            self.tabla_cultivos.delete(item)
        for c in db.obtener_datos("cultivos"):
            self.tabla_cultivos.insert("", "end", values=(c["id"], c["parcela_id"], c["tipo_cultivo"], c["fecha_siembra"], c["fecha_cosecha_estimada"], c["estado"]))

        if self.rol_id == 1:
            for item in self.tabla_usuarios.get_children():
                self.tabla_usuarios.delete(item)
            for u in db.obtener_datos("usuarios"):
                self.tabla_usuarios.insert("", "end", values=(u["id"], u["username"], u["email"], u["rol_id"], "Sí" if u["activo"] else "No"))

if __name__ == "__main__":
    ventana = tk.Tk()
    LoginWindow(ventana)
    ventana.mainloop()