# -*- coding: utf-8 -*-
"""
main.py  -  Cifra a PDF (version Android / Kivy)
================================================
Interfaz para Android. La logica vive en logica.py y NO se toco.

Reemplaza a cifra_app.py (que usaba customtkinter, eso no existe en Android).
"""

import os
import shutil
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import logica

VERSION = "7.0"

# ------------------------------------------------------------------ paleta --
FONDO        = "#EEF1F8"
TARJETA      = "#FFFFFF"
BORDE        = "#DDE3EF"
CAMPO        = "#F7F9FD"
TINTA        = "#101A3E"
TINTA_SUAVE  = "#6B7280"
APAGADO      = "#9AA3B2"
INDIGO       = "#1A237E"
VERDE        = "#17B26A"
VERDE_HOVER  = "#0E9C57"
ROJO         = "#DC2626"
AMBAR        = "#B45309"
AZUL         = "#2563EB"

SUGERENCIAS = [
    "Soda Stereo De Musica Ligera",
    "Coldplay Sparks",
    "Fito Paez A Rodar Mi Vida",
]

SISTEMA = ("Roboto", "Roboto-Bold")   # fuentes que Kivy trae incluidas


def c(hexstr, alpha=1.0):
    """'#RRGGBB' -> (r, g, b, a) para Kivy."""
    h = hexstr.lstrip("#")
    return (int(h[0:2], 16) / 255.0,
            int(h[2:4], 16) / 255.0,
            int(h[4:6], 16) / 255.0, alpha)


class Panel(BoxLayout):
    """Caja blanca con esquinas redondeadas (como la 'tarjeta' de la v7)."""

    def __init__(self, bg=TARJETA, radio=18, borde=BORDE, **kw):
        super().__init__(**kw)
        self._radio = dp(radio)
        with self.canvas.before:
            self._col = Color(*c(bg))
            self._rect = RoundedRectangle(radius=[self._radio])
            self._bcol = Color(*c(borde))
            self._borde = Line(rounded_rectangle=(0, 0, 0, 0, self._radio),
                               width=1.0)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._borde.rounded_rectangle = (self.x, self.y, self.width,
                                         self.height, self._radio)


class Boton(ButtonBehavior, Label):
    """Boton plano con esquinas redondeadas, tipografia controlada."""

    def __init__(self, texto, fondo=VERDE, letra="#FFFFFF", radio=13,
                 tam=15, negrita=True, borde=None, **kw):
        kw.setdefault("markup", True)
        super().__init__(text=texto, **kw)
        self._radio = dp(radio)
        self._fondo = c(fondo)
        self._fondo_off = c(fondo, 0.45)
        self._hover = c(VERDE_HOVER) if fondo == VERDE else c(fondo)
        with self.canvas.before:
            self._col = Color(*self._fondo)
            self._rect = RoundedRectangle(radius=[self._radio])
            if borde:
                self._bcol = Color(*c(borde))
                self._line = Line(rounded_rectangle=(0, 0, 0, 0, self._radio),
                                  width=1.0)
        self.color = c(letra)
        self.font_size = sp(tam)
        self.bold = negrita
        self.font_name = SISTEMA[1] if negrita else SISTEMA[0]
        self.bind(pos=self._sync, size=self._sync, state=self._estado)
        self._sync()

    def _sync(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        if hasattr(self, "_line"):
            self._line.rounded_rectangle = (self.x, self.y, self.width,
                                            self.height, self._radio)

    def _estado(self, inst, valor):
        self._col.rgba = (self._fondo if valor == "normal"
                          else self._fondo_off)


class Campo(TextInput):
    def __init__(self, **kw):
        kw.setdefault("multiline", False)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(52))
        kw.setdefault("font_size", sp(15))
        kw.setdefault("padding", [dp(14), dp(15)])
        kw.setdefault("background_color", c(CAMPO))
        kw.setdefault("foreground_color", c(TINTA))
        kw.setdefault("cursor_color", c(INDIGO))
        kw.setdefault("hint_text_color", c(APAGADO))
        kw.setdefault("write_tab", False)
        kw.setdefault("halign", "left")
        super().__init__(**kw)


class CifraApp(App):

    # ------------------------------------------------------------- android --
    def _pedir_permisos(self):
        """En Android hace falta permiso para escribir en Descargas."""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                 Permission.READ_EXTERNAL_STORAGE])
        except Exception:
            pass  # en Windows/Linux no existe el modulo android

    def carpeta_descargas(self):
        """Carpeta visible desde el telefono: Descargas/CifraApp."""
        try:
            from jnius import autoclass
            Env = autoclass("android.os.Environment")
            base = Env.getExternalStoragePublicDirectory(
                autoclass("android.os.Environment").DIRECTORY_DOWNLOADS)
            ruta = os.path.join(base.getAbsolutePath(), "CifraApp")
        except Exception:
            ruta = os.path.join(os.path.expanduser("~"), "CifraApp")

        try:
            os.makedirs(ruta, exist_ok=True)
            return ruta
        except Exception:
            return None

    # ------------------------------------------------------------- interfaz --
    def build(self):
        self.title = "Cifra a PDF"
        self.ocupado = False
        self.ultimo_pdf = None
        try:
            Window.softinput_mode = "pan"
        except Exception:
            pass

        raiz = FloatLayout()
        with raiz.canvas.before:
            Color(*c(FONDO))
            self._fondo_rect = RoundedRectangle(radius=[0])
        raiz.bind(size=self._fondo_size)

        # --- columna central -------------------------------------------------
        self.col = BoxLayout(orientation="vertical", spacing=dp(8),
                             padding=[dp(20), dp(18), dp(20), dp(12)],
                             size_hint=(1, 1))

        self.col.add_widget(Label(
            text="Cifra a PDF", bold=True, font_name=SISTEMA[1],
            color=c(TINTA), font_size=sp(30), size_hint_y=None,
            height=dp(44), halign="left", valign="middle",
            text_size=(None, dp(44))))

        self.col.add_widget(Label(
            text="Acordes y letra de Cifra Club, listos para imprimir",
            color=c(TINTA_SUAVE), font_size=sp(12), size_hint_y=None,
            height=dp(24), halign="left", valign="middle",
            text_size=(None, dp(24))))

        # --- tarjeta ---------------------------------------------------------
        tarjeta = Panel(orientation="vertical", spacing=dp(8),
                        padding=[dp(18), dp(16), dp(18), dp(16)],
                        size_hint_y=None)
        tarjeta.bind(minimum_height=tarjeta.setter("height"))

        tarjeta.add_widget(Label(
            text="[b]ARTISTA Y TEMA[/b]", markup=True, color=c(APAGADO),
            font_size=sp(10), size_hint_y=None, height=dp(18),
            halign="left", valign="middle", text_size=(None, dp(18))))

        self.entrada = Campo(hint_text="Ej: Coldplay Sparks")
        self.entrada.bind(on_text_validate=lambda *a: self.generar())
        tarjeta.add_widget(self.entrada)

        tarjeta.add_widget(Label(
            text="O pega el link de Cifra Club",
            color=c(APAGADO), font_size=sp(10), size_hint_y=None,
            height=dp(20), halign="left", valign="middle",
            text_size=(None, dp(20))))

        # sugerencias rapidas
        fila_sug = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        for texto in SUGERENCIAS:
            fila_sug.add_widget(Boton(
                texto.split(" ")[0], fondo=CAMPO, letra=INDIGO, tam=11,
                radio=10, borde=BORDE, size_hint_x=1,
                on_release=lambda inst, t=texto: self._sugerir(t)))
        tarjeta.add_widget(fila_sug)

        # casilla "incluir diagramas"
        self.incluir = True
        self.check = Boton("Incluir diagramas de acordes",
                           fondo="#E8EDFA", letra=TINTA, tam=12, negrita=False,
                           radio=10, borde=BORDE, size_hint_y=None,
                           height=dp(42), halign="left", valign="middle",
                           text_size=(None, dp(42)))
        self.check.bind(on_release=self._alternar_check)
        tarjeta.add_widget(self.check)

        # boton principal
        self.boton = Boton("Generar PDF", fondo=VERDE, tam=16,
                           size_hint_y=None, height=dp(56))
        self.boton.bind(on_release=lambda *a: self.generar())
        tarjeta.add_widget(self.boton)

        self.col.add_widget(tarjeta)

        # --- estado ----------------------------------------------------------
        self.estado = Label(text="Listo para procesar", color=c(APAGADO),
                            font_size=sp(12), size_hint_y=None,
                            height=dp(46), halign="center", valign="middle",
                            text_size=(Window.width - dp(48), dp(46)))
        self.col.add_widget(self.estado)

        # --- registro (oculto hasta que hace falta) --------------------------
        self.registro = Label(text="", color=c(TINTA_SUAVE), font_size=sp(9),
                              size_hint_y=None, halign="left", valign="top",
                              text_size=(Window.width - dp(60), None))
        self.registro.bind(texture_size=self._alto_registro)
        self.scroll = ScrollView(size_hint_y=None, height=dp(96),
                                 do_scroll_x=False)
        self.scroll.add_widget(self.registro)
        self.scroll.opacity = 0
        self.scroll.disabled = True
        self.col.add_widget(self.scroll)

        # --- pie -------------------------------------------------------------
        pie = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.btn_abrir = Boton("Abrir ultimo PDF", fondo=CAMPO, letra=INDIGO,
                               tam=12, radio=10, borde=BORDE, size_hint_x=1)
        self.btn_abrir.bind(on_release=lambda *a: self.abrir_ultimo())
        pie.add_widget(self.btn_abrir)

        self.btn_log = Boton("Ver registro", fondo=CAMPO, letra=APAGADO,
                             tam=12, negrita=False, radio=10, borde=BORDE,
                             size_hint_x=1)
        self.btn_log.bind(on_release=lambda *a: self._ver_registro())
        pie.add_widget(self.btn_log)
        self.col.add_widget(pie)

        self.col.add_widget(Label(
            text="v%s  ·  Cifra Club  ·  uso personal" % VERSION,
            color=c(APAGADO), font_size=sp(9), size_hint_y=None,
            height=dp(22), halign="center", valign="middle",
            text_size=(None, dp(22))))

        raiz.add_widget(self.col)

        Clock.schedule_once(lambda dt: self._pedir_permisos(), 0.5)
        return raiz

    def _fondo_size(self, inst, tam):
        self._fondo_rect.pos = inst.pos
        self._fondo_rect.size = tam

    def _alto_registro(self, inst, tam):
        inst.height = tam[1]

    # ---------------------------------------------------------------- acciones
    def _sugerir(self, texto):
        self.entrada.text = texto

    def _alternar_check(self, *a):
        self.incluir = not self.incluir
        self.check.text = ("Incluir diagramas de acordes" if self.incluir
                           else "Sin diagramas de acordes")
        self.check.opacity = 1.0 if self.incluir else 0.7

    def _estado(self, texto, color=APAGADO):
        self.estado.text = texto
        self.estado.color = c(color)

    def _ocupar(self):
        self.ocupado = True
        self.boton.text = "Buscando..."
        self.boton.disabled = True
        self.entrada.disabled = True

    def _liberar(self, texto, color=APAGADO):
        self.ocupado = False
        self.boton.text = "Generar PDF"
        self.boton.disabled = False
        self.entrada.disabled = False
        self._estado(texto, color)

    def generar(self):
        if self.ocupado:
            return
        consulta = (self.entrada.text or "").strip()
        if not consulta:
            self._estado("Escribi el artista y el tema.", ROJO)
            return
        self._ocupar()
        self._estado("Buscando en Cifra Club...", AZUL)
        threading.Thread(target=self._trabajar, args=(consulta,),
                         daemon=True).start()

    def _trabajar(self, consulta):
        """Corre en segundo plano: red + PDF. Nunca toca la interfaz."""
        try:
            del logica.LOG[:]
            datos = logica.procesar(consulta, self.incluir)
        except Exception as e:
            datos = {"ok": False, "error": "Error inesperado: %s" % e}
        Clock.schedule_once(lambda dt: self._terminado(datos), 0)

    def _terminado(self, datos):
        if not datos.get("ok"):
            self._liberar(datos.get("error", "No se pudo generar el PDF."), ROJO)
            self._volcar_registro()
            return

        ruta = datos["ruta"]
        destino = self._copiar_a_descargas(ruta)
        self.ultimo_pdf = destino or ruta

        texto = "%s  ·  %d acordes" % (datos["titulo"], len(datos["acordes"]))
        if destino:
            carpeta = os.path.dirname(destino)
            if "download" in carpeta.lower():
                texto += "\nGuardado en Descargas/CifraApp"
            else:
                texto += "\nGuardado en %s" % carpeta
        self._liberar(texto, VERDE_HOVER)
        self._volcar_registro()

    def _copiar_a_descargas(self, ruta):
        """Deja una copia visible en Descargas/CifraApp. Devuelve la ruta."""
        carpeta = self.carpeta_descargas()
        if not carpeta:
            return None
        try:
            destino = os.path.join(carpeta, os.path.basename(ruta))
            if os.path.abspath(destino) != os.path.abspath(ruta):
                shutil.copy2(ruta, destino)
            return destino
        except Exception:
            return None

    def abrir_ultimo(self):
        if not self.ultimo_pdf or not os.path.exists(self.ultimo_pdf):
            self._estado("Todavia no generaste ningun PDF.", APAGADO)
            return
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            File = autoclass("java.io.File")
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.fromFile(File(self.ultimo_pdf)),
                                  "application/pdf")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            PythonActivity.mActivity.startActivity(intent)
            self._estado("Abriendo el PDF...", AZUL)
        except Exception:
            self._estado("El PDF esta en:\n%s" % self.ultimo_pdf, TINTA_SUAVE)

    def _volcar_registro(self):
        if logica.LOG:
            self.registro.text = "\n".join(logica.LOG[-40:])
        else:
            self.registro.text = "(sin mensajes de diagnostico)"

    def _ver_registro(self):
        visible = self.scroll.opacity > 0
        self.scroll.opacity = 0 if visible else 1
        self.scroll.disabled = visible
        if not visible:
            self._volcar_registro()


if __name__ == "__main__":
    CifraApp().run()
