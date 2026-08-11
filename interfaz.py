
"""
OvenOps - Interfaz gráfica
Requiere: pip install customtkinter
 
Esta interfaz reutiliza toda la lógica de negocio ya existente
(ventas.py, datos.py, produccion.py, inventario.py, reparto.py,
config.py, utils.py) sin modificarla — solo cambia la forma de
capturar y mostrar los datos.
"""
 
import csv
import os
import customtkinter as ctk
from datetime import date, datetime
from tkinter import messagebox
 
from ventas import calcular_precio, registrar_venta
from datos import guardar_corte, marcar_ventas_como_cerradas, recuperar_ventas_pendientes, cancelar_venta
from produccion import guardar_produccion, generar_pago
from inventario import registrar_movimiento_inventario, leer_inventario
from reparto import registrar_salida_repartidor, leer_repartidores_pendientes, liquidar_repartidor
from config import precio_pieza, precio_caja_publico, piezas_por_charola
from utils import calcular_resumen_piezas
 
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
 
# Paleta cálida tipo panadería (ámbar / café)
PALETTE = {
    "bg_app": "#FBF1E4",
    "bg_card": "#FFFFFF",
    "bg_card_alt": "#FCE9CE",
    "accent": "#C0783C",
    "accent_hover": "#9C5F2C",
    "accent_light": "#E8B074",
    "text_dark": "#4A2E1E",
    "text_muted": "#8A6F5D",
    "danger": "#B23B3B",
    "danger_hover": "#8F2E2E",
    "success": "#4F7942",
    "neutral": "#8A6F5D",
    "neutral_hover": "#6B5342",
}
 
 
class OvenOpsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OvenOps")
        self.geometry("1200x750")
        self.configure(fg_color=PALETTE["bg_app"])
        self.after(10, lambda: self.state("zoomed"))
 
        # Estado de sesión compartido entre pantallas
        ahora = datetime.now()
        self.fecha = ahora.date()
        self.hora = ahora.time().strftime("%H:%M:%S")
        self.ventas = []
        self.ventas_piezas_hoy = 0
        self.ventas_cajas_hoy = 0
 
        self._recuperar_turno_anterior()
 
        self.frame_actual = None
        self.mostrar_inicio()
 
    def _recuperar_turno_anterior(self):
        pendientes = recuperar_ventas_pendientes()
        if pendientes:
            self.ventas.extend(pendientes)
            piezas_rec, cajas_rec, monto_rec = calcular_resumen_piezas(self.ventas)
            self.ventas_piezas_hoy += piezas_rec
            self.ventas_cajas_hoy += cajas_rec
            messagebox.showinfo(
                "Recuperación de turno",
                f"Se recuperaron {len(pendientes)} ventas no contabilizadas.\n"
                f"Monto recuperado: ${monto_rec:.2f}"
            )
 
    def _cambiar_frame(self, frame_cls):
        if self.frame_actual is not None:
            self.frame_actual.destroy()
        self.frame_actual = frame_cls(self)
        self.frame_actual.pack(fill="both", expand=True)
 
    def mostrar_inicio(self):
        self._cambiar_frame(PantallaInicio)
 
    def mostrar_caja(self):
        self._cambiar_frame(PantallaCaja)
 
    def mostrar_admin(self):
        self._cambiar_frame(PantallaAdmin)
 
 
# ===========================================================================
# PANTALLA DE INICIO
# ===========================================================================
 
class PantallaInicio(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=PALETTE["bg_app"])
 
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.place(relx=0.5, rely=0.5, anchor="center")
 
        tarjeta = ctk.CTkFrame(contenedor, fg_color=PALETTE["bg_card"], corner_radius=32,
                                border_width=3, border_color=PALETTE["accent_light"])
        tarjeta.pack(padx=10, pady=10)
 
        ctk.CTkLabel(tarjeta, text="🥖", font=ctk.CTkFont(size=88)).pack(pady=(70, 0), padx=110)
        ctk.CTkLabel(tarjeta, text="OvenOps", font=ctk.CTkFont(size=52, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(10, 5))
        ctk.CTkLabel(tarjeta, text="Sistema de gestión — Panificadora",
                     font=ctk.CTkFont(size=17), text_color=PALETTE["text_muted"]).pack(pady=(0, 15))
 
        ctk.CTkFrame(tarjeta, fg_color=PALETTE["accent_light"], height=4, width=280,
                     corner_radius=2).pack(pady=(0, 45))
 
        ctk.CTkButton(tarjeta, text="🧾  Caja", width=340, height=76,
                      font=ctk.CTkFont(size=22, weight="bold"),
                      fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                      corner_radius=16, command=app.mostrar_caja).pack(pady=12)
        ctk.CTkButton(tarjeta, text="⚙️  Administración", width=340, height=76,
                      font=ctk.CTkFont(size=22, weight="bold"),
                      fg_color=PALETTE["neutral"], hover_color=PALETTE["neutral_hover"],
                      corner_radius=16, command=app.mostrar_admin).pack(pady=(12, 70))
 
 
# ===========================================================================
# PANTALLA DE CAJA
# ===========================================================================
 
class PantallaCaja(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=PALETTE["bg_app"])
        self.app = app
        self.tipo_actual = "piezas"
 
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkButton(header, text="← Inicio", width=90, fg_color=PALETTE["neutral"],
                      hover_color=PALETTE["neutral_hover"], command=app.mostrar_inicio).pack(side="left")
        ctk.CTkLabel(header, text="🧾 Caja", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(side="left", padx=20)
 
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=20, pady=(0, 20))
 
        # ---- Panel izquierdo: venta rápida, siempre visible, sin pop-ups ----
        panel_venta = ctk.CTkFrame(cuerpo, fg_color=PALETTE["bg_card_alt"], corner_radius=18)
        panel_venta.pack(side="left", fill="y", padx=(0, 15))
 
        ctk.CTkLabel(panel_venta, text="Nueva venta", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(20, 10))
 
        self.selector_tipo = ctk.CTkSegmentedButton(
            panel_venta, values=["Piezas", "Cajas"], command=self._cambiar_tipo,
            selected_color=PALETTE["accent"], selected_hover_color=PALETTE["accent_hover"],
            unselected_color=PALETTE["bg_card"], text_color=PALETTE["text_dark"]
        )
        self.selector_tipo.set("Piezas")
        self.selector_tipo.pack(pady=(0, 15), padx=20)
 
        ctk.CTkLabel(panel_venta, text="Cantidad:", text_color=PALETTE["text_muted"]).pack()
        self.entry_cantidad = ctk.CTkEntry(panel_venta, width=220, height=44,
                                            font=ctk.CTkFont(size=20), justify="center",
                                            fg_color=PALETTE["bg_card"], border_color=PALETTE["accent_light"])
        self.entry_cantidad.pack(padx=20, pady=(0, 10))
        self.entry_cantidad.bind("<KeyRelease>", self._actualizar_total)
        self.entry_cantidad.bind("<Return>", lambda e: self.entry_pago.focus())
 
        self.label_total = ctk.CTkLabel(panel_venta, text="Total: $0.00", font=ctk.CTkFont(size=20, weight="bold"),
                                         text_color=PALETTE["accent_hover"])
        self.label_total.pack(pady=(0, 15))
 
        ctk.CTkLabel(panel_venta, text="Pago del cliente:", text_color=PALETTE["text_muted"]).pack()
        self.entry_pago = ctk.CTkEntry(panel_venta, width=220, height=44,
                                        font=ctk.CTkFont(size=20), justify="center",
                                        fg_color=PALETTE["bg_card"], border_color=PALETTE["accent_light"])
        self.entry_pago.pack(padx=20, pady=(0, 10))
        self.entry_pago.bind("<Return>", lambda e: self._cobrar())
 
        self.label_feedback = ctk.CTkLabel(panel_venta, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_feedback.pack(pady=(0, 10))
 
        ctk.CTkButton(panel_venta, text="Cobrar  (Enter)", width=220, height=48,
                      font=ctk.CTkFont(size=16, weight="bold"), corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                      command=self._cobrar).pack(padx=20, pady=(0, 25))
 
        # ---- Panel derecho: estado del turno ----
        panel_turno = ctk.CTkFrame(cuerpo, fg_color=PALETTE["bg_card"], corner_radius=18)
        panel_turno.pack(side="left", fill="both", expand=True)
 
        ctk.CTkLabel(panel_turno, text="📋 Turno actual", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(20, 15))
 
        stats_frame = ctk.CTkFrame(panel_turno, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        stats_frame.columnconfigure((0, 1, 2), weight=1)
 
        self.label_stat_piezas = self._crear_tarjeta_stat(stats_frame, "🥖", "Piezas", 0)
        self.label_stat_cajas = self._crear_tarjeta_stat(stats_frame, "📦", "Cajas", 1)
        self.label_stat_monto = self._crear_tarjeta_stat(stats_frame, "💰", "Monto", 2)
 
        # Botones fijos al fondo — se empacan antes que la lista para reservarles espacio
        botones_turno = ctk.CTkFrame(panel_turno, fg_color="transparent")
        botones_turno.pack(side="bottom", pady=(10, 20))
 
        ctk.CTkButton(botones_turno, text="Cancelar venta", width=170, corner_radius=12,
                      fg_color=PALETTE["neutral"], hover_color=PALETTE["neutral_hover"],
                      command=self.abrir_cancelar_venta).grid(row=0, column=0, padx=5)
        ctk.CTkButton(botones_turno, text="Cerrar caja", width=170, corner_radius=12,
                      fg_color=PALETTE["danger"], hover_color=PALETTE["danger_hover"],
                      command=self.cerrar_caja).grid(row=0, column=1, padx=5)
 
        ctk.CTkLabel(panel_turno, text="Ventas del turno", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=PALETTE["text_muted"]).pack(anchor="w", padx=25, pady=(0, 5))
 
        self.lista_ventas_frame = ctk.CTkScrollableFrame(panel_turno, fg_color=PALETTE["bg_app"], corner_radius=12)
        self.lista_ventas_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
 
        self._actualizar_resumen_visible()
        self.entry_cantidad.focus()
 
    def _crear_tarjeta_stat(self, parent, icono, etiqueta, columna):
        tarjeta = ctk.CTkFrame(parent, fg_color=PALETTE["bg_card_alt"], corner_radius=14)
        tarjeta.grid(row=0, column=columna, padx=6, sticky="nsew")
        ctk.CTkLabel(tarjeta, text=f"{icono} {etiqueta}", font=ctk.CTkFont(size=13),
                     text_color=PALETTE["text_muted"]).pack(pady=(12, 2))
        valor = ctk.CTkLabel(tarjeta, text="0", font=ctk.CTkFont(size=22, weight="bold"),
                              text_color=PALETTE["accent_hover"])
        valor.pack(pady=(0, 12))
        return valor
 
    def _cambiar_tipo(self, valor):
        self.tipo_actual = "piezas" if valor == "Piezas" else "cajas"
        self._actualizar_total()
 
    def _precio_actual(self):
        return precio_pieza if self.tipo_actual == "piezas" else precio_caja_publico
 
    def _actualizar_total(self, event=None):
        texto = self.entry_cantidad.get()
        if texto.isdigit() and int(texto) > 0:
            total = calcular_precio(int(texto), self._precio_actual())
            self.label_total.configure(text=f"Total: ${total:.2f}")
        else:
            self.label_total.configure(text="Total: $0.00")
 
    def _actualizar_resumen_visible(self):
        piezas, cajas, total = calcular_resumen_piezas(self.app.ventas)
        self.label_stat_piezas.configure(text=str(piezas))
        self.label_stat_cajas.configure(text=str(cajas))
        self.label_stat_monto.configure(text=f"${total:.2f}")
 
        for widget in self.lista_ventas_frame.winfo_children():
            widget.destroy()
 
        if not self.app.ventas:
            ctk.CTkLabel(self.lista_ventas_frame, text="Sin ventas registradas todavía.",
                         text_color=PALETTE["text_muted"]).pack(pady=15)
            return
 
        for v in reversed(self.app.ventas):
            tipo = "piezas" if v["piezas"] > 0 else "cajas"
            cantidad = v["piezas"] if tipo == "piezas" else v["cajas"]
            icono = "🥖" if tipo == "piezas" else "📦"
            fila = ctk.CTkFrame(self.lista_ventas_frame, fg_color=PALETTE["bg_card"], corner_radius=10)
            fila.pack(fill="x", pady=3, padx=3)
            ctk.CTkLabel(fila, text=f"{icono}  {cantidad} {tipo}",
                         text_color=PALETTE["text_dark"]).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(fila, text=f"${v['total']:.2f}", font=ctk.CTkFont(weight="bold"),
                         text_color=PALETTE["accent_hover"]).pack(side="right", padx=12, pady=8)
 
    def _cobrar(self):
        cantidad_texto = self.entry_cantidad.get()
        pago_texto = self.entry_pago.get()
 
        if not cantidad_texto.isdigit() or int(cantidad_texto) <= 0:
            self._mostrar_feedback("Cantidad inválida.", error=True)
            return
        if not pago_texto.isdigit():
            self._mostrar_feedback("Monto de pago inválido.", error=True)
            return
 
        cantidad = int(cantidad_texto)
        pago = int(pago_texto)
 
        exito, resultado = registrar_venta(
            cantidad, pago, self.app.ventas, self._precio_actual(),
            self.tipo_actual, self.app.fecha, self.app.hora
        )
 
        if not exito:
            self._mostrar_feedback(resultado.strip(), error=True)
            return
 
        if self.tipo_actual == "piezas":
            self.app.ventas_piezas_hoy += cantidad
        else:
            self.app.ventas_cajas_hoy += cantidad
 
        self._actualizar_resumen_visible()
 
        if resultado == 0:
            self._mostrar_feedback("✅ Pago exacto. Gracias.", error=False)
        else:
            self._mostrar_feedback(f"✅ Cambio: ${resultado:.2f}", error=False)
 
        self.entry_cantidad.delete(0, "end")
        self.entry_pago.delete(0, "end")
        self.label_total.configure(text="Total: $0.00")
        self.entry_cantidad.focus()
 
    def _mostrar_feedback(self, texto, error):
        self.label_feedback.configure(text=texto, text_color=PALETTE["danger"] if error else PALETTE["success"])
 
    def cerrar_caja(self):
        if not self.app.ventas:
            messagebox.showwarning("Cierre de caja", "No existen movimientos para realizar el corte.")
            return
        if not messagebox.askyesno("Confirmar cierre", "¿Ejecutar cierre de caja y guardar el corte?"):
            return
        guardar_corte(self.app.fecha, self.app.ventas)
        marcar_ventas_como_cerradas()
        self.app.ventas.clear()
        self.app.ventas_piezas_hoy = 0
        self.app.ventas_cajas_hoy = 0
        self._actualizar_resumen_visible()
        messagebox.showinfo("Cierre de caja", "Turno finalizado. Valores reiniciados.")
 
    def abrir_cancelar_venta(self):
        VentanaCancelarVenta(self.app, self)
 
 
class VentanaCancelarVenta(ctk.CTkToplevel):
    def __init__(self, app, pantalla_caja):
        super().__init__(app)
        self.app = app
        self.pantalla_caja = pantalla_caja
        self.configure(fg_color=PALETTE["bg_app"])
 
        self.title("Cancelar venta")
        self.geometry("400x400")
        self.grab_set()
 
        ctk.CTkLabel(self, text="Ventas del turno actual", font=ctk.CTkFont(weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(15, 5))
 
        lista_frame = ctk.CTkScrollableFrame(self, width=340, height=260, fg_color=PALETTE["bg_card"])
        lista_frame.pack(pady=10)
 
        if not self.app.ventas:
            ctk.CTkLabel(lista_frame, text="No hay ventas en el turno actual.").pack(pady=10)
            return
 
        for i, v in enumerate(self.app.ventas):
            tipo = "piezas" if v["piezas"] > 0 else "cajas"
            cantidad = v["piezas"] if tipo == "piezas" else v["cajas"]
            fila = ctk.CTkFrame(lista_frame, fg_color=PALETTE["bg_card_alt"], corner_radius=10)
            fila.pack(fill="x", pady=4)
            ctk.CTkLabel(fila, text=f"{cantidad} {tipo} — ${v['total']:.2f}",
                         text_color=PALETTE["text_dark"]).pack(side="left", padx=10)
            ctk.CTkButton(fila, text="Cancelar", width=80, fg_color=PALETTE["danger"],
                          hover_color=PALETTE["danger_hover"],
                          command=lambda idx=i: self._cancelar(idx)).pack(side="right", padx=10)
 
    def _cancelar(self, indice):
        v = self.app.ventas[indice]
        tipo = "piezas" if v["piezas"] > 0 else "cajas"
        cantidad = v["piezas"] if tipo == "piezas" else v["cajas"]
 
        if not messagebox.askyesno("Confirmar cancelación",
                                     f"¿Cancelar {cantidad} {tipo} por ${v['total']:.2f}?"):
            return
 
        exito = cancelar_venta(self.app.ventas, indice)
        if exito:
            messagebox.showinfo("Venta cancelada", "Venta cancelada correctamente.")
            self.pantalla_caja._actualizar_resumen_visible()
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo cancelar la venta.")
 
 
# ===========================================================================
# PANTALLA DE ADMINISTRACIÓN
# ===========================================================================
 
class PantallaAdmin(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=PALETTE["bg_app"])
        self.app = app
 
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkButton(header, text="← Inicio", width=90, fg_color=PALETTE["neutral"],
                      hover_color=PALETTE["neutral_hover"], command=app.mostrar_inicio).pack(side="left")
        ctk.CTkLabel(header, text="⚙️ Administración", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(side="left", padx=20)
 
        self.tabview = ctk.CTkTabview(
            self, width=1100, height=620, corner_radius=18,
            fg_color=PALETTE["bg_card"], segmented_button_fg_color=PALETTE["bg_card_alt"],
            segmented_button_selected_color=PALETTE["accent"],
            segmented_button_selected_hover_color=PALETTE["accent_hover"],
            segmented_button_unselected_color=PALETTE["bg_card_alt"],
            text_color=PALETTE["text_dark"]
        )
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
 
        self.tabview.add("🍞 Producción")
        self.tabview.add("🚴 Reparto")
        self.tabview.add("📊 Históricos")
 
        self._construir_tab_produccion(self.tabview.tab("🍞 Producción"))
        self._construir_tab_reparto(self.tabview.tab("🚴 Reparto"))
        self._construir_tab_historicos(self.tabview.tab("📊 Históricos"))
 
    # ---------------- PRODUCCIÓN ----------------
 
    def _construir_tab_produccion(self, tab):
        cuerpo = ctk.CTkFrame(tab, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)
 
        # ---- Panel izquierdo: registrar producción ----
        form_card = ctk.CTkFrame(cuerpo, fg_color=PALETTE["bg_card_alt"], corner_radius=18)
        form_card.pack(side="left", fill="y", padx=(0, 15))
 
        ctk.CTkLabel(form_card, text="Registrar producción del día", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(20, 15), padx=20)
 
        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(padx=20)
 
        ctk.CTkLabel(form, text="Piezas producidas:", text_color=PALETTE["text_muted"]).grid(
            row=0, column=0, sticky="e", padx=5, pady=8)
        self.entry_produccion_piezas = ctk.CTkEntry(form, width=140, fg_color=PALETTE["bg_card"])
        self.entry_produccion_piezas.grid(row=0, column=1, padx=5, pady=8)
 
        ctk.CTkLabel(form, text="Cajas producidas:", text_color=PALETTE["text_muted"]).grid(
            row=1, column=0, sticky="e", padx=5, pady=8)
        self.entry_produccion_cajas = ctk.CTkEntry(form, width=140, fg_color=PALETTE["bg_card"])
        self.entry_produccion_cajas.grid(row=1, column=1, padx=5, pady=8)
 
        ctk.CTkLabel(form, text="Merma en piezas:", text_color=PALETTE["text_muted"]).grid(
            row=2, column=0, sticky="e", padx=5, pady=8)
        self.entry_merma_piezas = ctk.CTkEntry(form, width=140, fg_color=PALETTE["bg_card"])
        self.entry_merma_piezas.insert(0, "0")
        self.entry_merma_piezas.grid(row=2, column=1, padx=5, pady=8)
 
        ctk.CTkLabel(form, text="Merma en cajas:", text_color=PALETTE["text_muted"]).grid(
            row=3, column=0, sticky="e", padx=5, pady=8)
        self.entry_merma_cajas = ctk.CTkEntry(form, width=140, fg_color=PALETTE["bg_card"])
        self.entry_merma_cajas.insert(0, "0")
        self.entry_merma_cajas.grid(row=3, column=1, padx=5, pady=8)
 
        self.label_error_produccion = ctk.CTkLabel(form, text="", text_color=PALETTE["danger"])
        self.label_error_produccion.grid(row=4, column=0, columnspan=2, pady=(5, 0))
 
        ctk.CTkButton(form_card, text="Registrar producción", width=280, height=42, corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                      command=self._registrar_produccion).pack(pady=(15, 10))
 
        ctk.CTkButton(form_card, text="Pagar producción de la semana anterior", width=280, height=42,
                      corner_radius=12, fg_color=PALETTE["neutral"], hover_color=PALETTE["neutral_hover"],
                      command=self._pagar_produccion).pack(pady=(0, 25))
 
        # ---- Panel derecho: inventario en vivo ----
        panel_inventario = ctk.CTkFrame(cuerpo, fg_color=PALETTE["bg_card"], corner_radius=18)
        panel_inventario.pack(side="left", fill="both", expand=True)
 
        ctk.CTkLabel(panel_inventario, text="📦 Inventario actual", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=PALETTE["text_dark"]).pack(pady=(30, 20))
 
        self.label_inventario = ctk.CTkLabel(panel_inventario, text="", font=ctk.CTkFont(size=28, weight="bold"),
                                              text_color=PALETTE["accent_hover"])
        self.label_inventario.pack(pady=10)
 
        ctk.CTkLabel(panel_inventario, text="Se actualiza automáticamente con cada\nproducción, salida y liquidación de reparto.",
                     font=ctk.CTkFont(size=12), text_color=PALETTE["text_muted"], justify="center").pack(pady=(10, 0))
 
        self._actualizar_inventario_visible()
 
    def _actualizar_inventario_visible(self):
        inv = leer_inventario()
        self.label_inventario.configure(
            text=f"Inventario actual: {inv['piezas']} piezas | {inv['cajas']} cajas"
        )
 
    def _registrar_produccion(self):
        campos = [
            self.entry_produccion_piezas.get(),
            self.entry_produccion_cajas.get(),
            self.entry_merma_piezas.get(),
            self.entry_merma_cajas.get(),
        ]
        if not all(c.isdigit() for c in campos):
            self.label_error_produccion.configure(text="Todos los campos deben ser números válidos.")
            return
 
        produccion, cajas, merma_piezas, merma_cajas = (int(c) for c in campos)
 
        guardar_produccion(self.app.fecha, produccion, cajas)
        registrar_movimiento_inventario(
            self.app.fecha.isoformat(),
            produccion,
            cajas,
            merma_piezas,
            merma_cajas,
            self.app.ventas_piezas_hoy,
            self.app.ventas_cajas_hoy,
        )
        self.app.ventas_piezas_hoy = 0
        self.app.ventas_cajas_hoy = 0
 
        self.label_error_produccion.configure(text="")
        self.entry_produccion_piezas.delete(0, "end")
        self.entry_produccion_cajas.delete(0, "end")
        self.entry_merma_piezas.delete(0, "end")
        self.entry_merma_piezas.insert(0, "0")
        self.entry_merma_cajas.delete(0, "end")
        self.entry_merma_cajas.insert(0, "0")
 
        self._actualizar_inventario_visible()
        messagebox.showinfo("Producción registrada", "Inventario actualizado correctamente.")
 
    def _pagar_produccion(self):
        resultado = generar_pago()
        if resultado is None:
            messagebox.showinfo("Pago de producción", "No hay producción pendiente para pagar.")
            return
        messagebox.showinfo(
            "Pago generado",
            f"Fecha: {resultado['fecha_pago']}\n"
            f"Piezas: {resultado['piezas']}\n"
            f"Cajas: {resultado['cajas']}\n"
            f"Total a pagar: ${resultado['total_pago']:.2f}"
        )
 
    # ---------------- REPARTO ----------------
 
    def _construir_tab_reparto(self, tab):
        contenedor = ctk.CTkFrame(tab, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=10, pady=10)
 
        salida_frame = ctk.CTkFrame(contenedor, fg_color=PALETTE["bg_card_alt"], corner_radius=18)
        salida_frame.pack(side="left", fill="y", padx=(0, 15))
 
        ctk.CTkLabel(salida_frame, text="Registrar salida de repartidor",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=PALETTE["text_dark"]).pack(pady=(20, 15), padx=20)
 
        ctk.CTkLabel(salida_frame, text="Nombre:", text_color=PALETTE["text_muted"]).pack(pady=(5, 0))
        self.entry_reparto_nombre = ctk.CTkEntry(salida_frame, width=200, fg_color=PALETTE["bg_card"])
        self.entry_reparto_nombre.pack()
 
        ctk.CTkLabel(salida_frame, text="ID del repartidor:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_reparto_id = ctk.CTkEntry(salida_frame, width=200, fg_color=PALETTE["bg_card"])
        self.entry_reparto_id.pack()
 
        ctk.CTkLabel(salida_frame, text="Charolas que se lleva:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_reparto_charolas = ctk.CTkEntry(salida_frame, width=200, fg_color=PALETTE["bg_card"])
        self.entry_reparto_charolas.pack()
 
        ctk.CTkLabel(salida_frame, text="Cajas que se lleva:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_reparto_cajas = ctk.CTkEntry(salida_frame, width=200, fg_color=PALETTE["bg_card"])
        self.entry_reparto_cajas.insert(0, "0")
        self.entry_reparto_cajas.pack()
 
        self.label_error_reparto = ctk.CTkLabel(salida_frame, text="", text_color=PALETTE["danger"])
        self.label_error_reparto.pack(pady=(10, 0))
 
        ctk.CTkButton(salida_frame, text="Registrar salida", width=200, height=40, corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                      command=self._registrar_salida_repartidor).pack(pady=(15, 25))
 
        pendientes_frame = ctk.CTkFrame(contenedor, fg_color=PALETTE["bg_card"], corner_radius=18)
        pendientes_frame.pack(side="left", fill="both", expand=True)
 
        ctk.CTkLabel(pendientes_frame, text="Repartidores pendientes",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=PALETTE["text_dark"]).pack(pady=(20, 10))
 
        self.lista_pendientes_frame = ctk.CTkScrollableFrame(pendientes_frame, width=380, height=380,
                                                               fg_color=PALETTE["bg_app"])
        self.lista_pendientes_frame.pack(padx=15, pady=(0, 15), fill="both", expand=True)
 
        self._refrescar_pendientes_reparto()
 
    def _registrar_salida_repartidor(self):
        nombre = self.entry_reparto_nombre.get().strip()
        id_repartidor = self.entry_reparto_id.get().strip()
        charolas_texto = self.entry_reparto_charolas.get().strip()
        cajas_texto = self.entry_reparto_cajas.get().strip()
 
        if not nombre or not id_repartidor:
            self.label_error_reparto.configure(text="Nombre e ID son obligatorios.")
            return
        if not charolas_texto.isdigit() or not cajas_texto.isdigit():
            self.label_error_reparto.configure(text="Charolas y cajas deben ser números válidos.")
            return
 
        piezas = int(charolas_texto) * piezas_por_charola
        cajas = int(cajas_texto)
 
        if piezas == 0 and cajas == 0:
            self.label_error_reparto.configure(text="Debes registrar al menos una charola o caja.")
            return
 
        exito, mensaje = registrar_salida_repartidor(date.today(), nombre, id_repartidor, piezas, cajas)
 
        if exito:
            self.label_error_reparto.configure(text="")
            self.entry_reparto_nombre.delete(0, "end")
            self.entry_reparto_id.delete(0, "end")
            self.entry_reparto_charolas.delete(0, "end")
            self.entry_reparto_cajas.delete(0, "end")
            self.entry_reparto_cajas.insert(0, "0")
            self._refrescar_pendientes_reparto()
            self._actualizar_inventario_visible()
            messagebox.showinfo("Salida registrada", mensaje)
        else:
            self.label_error_reparto.configure(text=mensaje)
 
    def _refrescar_pendientes_reparto(self):
        for widget in self.lista_pendientes_frame.winfo_children():
            widget.destroy()
 
        pendientes = leer_repartidores_pendientes()
 
        if not pendientes:
            ctk.CTkLabel(self.lista_pendientes_frame, text="No hay repartidores pendientes.").pack(pady=10)
            return
 
        for r in pendientes:
            fila = ctk.CTkFrame(self.lista_pendientes_frame, fg_color=PALETTE["bg_card_alt"], corner_radius=10)
            fila.pack(fill="x", pady=4)
            texto = f"{r['nombre']} ({r['id_repartidor']}) — {r['fecha']} — {r['piezas_salida']} piezas, {r['cajas_salida']} cajas"
            ctk.CTkLabel(fila, text=texto, wraplength=250, justify="left",
                         text_color=PALETTE["text_dark"]).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(fila, text="Liquidar", width=80, corner_radius=10,
                          fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                          command=lambda reg=r: self._abrir_liquidar(reg)).pack(side="right", padx=10)
 
    def _abrir_liquidar(self, registro):
        VentanaLiquidarRepartidor(self.app, self, registro)
 
    # ---------------- HISTÓRICOS ----------------
 
    def _construir_tab_historicos(self, tab):
        selector = ctk.CTkFrame(tab, fg_color="transparent")
        selector.pack(pady=20)
 
        ctk.CTkButton(selector, text="📋 Ver cortes de caja", width=220, height=40, corner_radius=12,
                      fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
                      command=self._mostrar_cortes).pack(side="left", padx=10)
        ctk.CTkButton(selector, text="💰 Ver pagos de producción", width=220, height=40, corner_radius=12,
                      fg_color=PALETTE["neutral"], hover_color=PALETTE["neutral_hover"],
                      command=self._mostrar_pagos).pack(side="left", padx=10)
 
        self.texto_historicos = ctk.CTkTextbox(tab, width=1000, height=440, corner_radius=14,
                                                fg_color=PALETTE["bg_app"], text_color=PALETTE["text_dark"],
                                                font=ctk.CTkFont(family="Courier"))
        self.texto_historicos.pack(padx=20, pady=10, fill="both", expand=True)
        self.texto_historicos.configure(state="disabled")
 
        self._mostrar_cortes()
 
    def _escribir_historico(self, texto):
        self.texto_historicos.configure(state="normal")
        self.texto_historicos.delete("1.0", "end")
        self.texto_historicos.insert("end", texto)
        self.texto_historicos.configure(state="disabled")
 
    def _mostrar_cortes(self):
        if not os.path.exists("cortes.csv"):
            self._escribir_historico("No se encontró el archivo de cortes.")
            return
        with open("cortes.csv", "r", encoding="utf-8") as f:
            filas = list(csv.reader(f))
        if len(filas) <= 1:
            self._escribir_historico("No hay cortes registrados todavía.")
            return
        lineas = [f"{'Fecha':<12} | {'Piezas':>8} | {'Cajas':>8} | {'Total':>12}"]
        for fecha, piezas, cajas, total in filas[1:]:
            lineas.append(f"{fecha:<12} | {piezas:>8} | {cajas:>8} | ${float(total):>10.2f}")
        self._escribir_historico("\n".join(lineas))
 
    def _mostrar_pagos(self):
        if not os.path.exists("pagos.csv"):
            self._escribir_historico("No se encontró el archivo de pagos de producción.")
            return
        with open("pagos.csv", "r", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
        if not filas:
            self._escribir_historico("No hay pagos de producción registrados todavía.")
            return
        lineas = [f"{'Fecha pago':<12} | {'Piezas':>8} | {'Cajas':>8} | {'Total':>12}"]
        for fila in filas:
            lineas.append(
                f"{fila['fecha_pago']:<12} | {fila['piezas']:>8} | {fila['cajas']:>8} | ${float(fila['total_pago']):>10.2f}"
            )
        self._escribir_historico("\n".join(lineas))
 
 
class VentanaLiquidarRepartidor(ctk.CTkToplevel):
    def __init__(self, app, pantalla_admin, registro):
        super().__init__(app)
        self.pantalla_admin = pantalla_admin
        self.registro = registro
        self.configure(fg_color=PALETTE["bg_app"])
 
        self.title(f"Liquidar a {registro['nombre']}")
        self.geometry("360x440")
        self.grab_set()
 
        ctk.CTkLabel(self, text=f"{registro['nombre']} — {registro['fecha']}",
                     font=ctk.CTkFont(weight="bold"), text_color=PALETTE["text_dark"]).pack(pady=(15, 5))
        ctk.CTkLabel(
            self, text=f"Salió con {registro['piezas_salida']} piezas, {registro['cajas_salida']} cajas",
            text_color=PALETTE["text_muted"]
        ).pack(pady=(0, 15))
 
        ctk.CTkLabel(self, text="Piezas que devuelve:", text_color=PALETTE["text_muted"]).pack(pady=(5, 0))
        self.entry_pd = ctk.CTkEntry(self, width=200, fg_color=PALETTE["bg_card"])
        self.entry_pd.insert(0, "0")
        self.entry_pd.pack()
 
        ctk.CTkLabel(self, text="Cajas que devuelve:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_cd = ctk.CTkEntry(self, width=200, fg_color=PALETTE["bg_card"])
        self.entry_cd.insert(0, "0")
        self.entry_cd.pack()
 
        ctk.CTkLabel(self, text="Merma de piezas:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_mp = ctk.CTkEntry(self, width=200, fg_color=PALETTE["bg_card"])
        self.entry_mp.insert(0, "0")
        self.entry_mp.pack()
 
        ctk.CTkLabel(self, text="Merma de cajas:", text_color=PALETTE["text_muted"]).pack(pady=(10, 0))
        self.entry_mc = ctk.CTkEntry(self, width=200, fg_color=PALETTE["bg_card"])
        self.entry_mc.insert(0, "0")
        self.entry_mc.pack()
 
        self.label_error = ctk.CTkLabel(self, text="", text_color=PALETTE["danger"])
        self.label_error.pack(pady=(10, 0))
 
        ctk.CTkButton(self, text="Liquidar", corner_radius=12, fg_color=PALETTE["accent"],
                      hover_color=PALETTE["accent_hover"], command=self._liquidar).pack(pady=20)
 
    def _liquidar(self):
        campos = [self.entry_pd.get(), self.entry_cd.get(), self.entry_mp.get(), self.entry_mc.get()]
        if not all(c.isdigit() for c in campos):
            self.label_error.configure(text="Todos los campos deben ser números válidos.")
            return
 
        piezas_devueltas, cajas_devueltas, merma_piezas, merma_cajas = (int(c) for c in campos)
 
        resumen = liquidar_repartidor(
            self.registro["nombre"], self.registro["id_repartidor"], self.registro["fecha"],
            piezas_devueltas, cajas_devueltas, merma_piezas, merma_cajas
        )
 
        if resumen is None:
            self.label_error.configure(text="No se pudo liquidar. Intenta de nuevo.")
            return
 
        self.pantalla_admin._refrescar_pendientes_reparto()
        self.pantalla_admin._actualizar_inventario_visible()
 
        messagebox.showinfo(
            "Liquidación completada",
            f"Piezas vendidas: {resumen['piezas_vendidas']}\n"
            f"Cajas vendidas: {resumen['cajas_vendidas']}\n"
            f"Piezas devueltas: {resumen['piezas_devueltas']}\n"
            f"Cajas devueltas: {resumen['cajas_devueltas']}\n"
            f"Merma piezas: {resumen['merma_piezas']}\n"
            f"Merma cajas: {resumen['merma_cajas']}\n"
            f"Total a cobrar: ${resumen['total']:.2f}"
        )
        self.destroy()
 
 
if __name__ == "__main__":
    app = OvenOpsApp()
    app.mainloop()
 