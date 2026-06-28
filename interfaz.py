# ARCHIVO DE INTERFAZ GRÁFICA.
# Este archivo es el que ve el usuario. Usa Tkinter para crear ventanas, botones, cuadros de texto, pantallas de login, selección de facción, partida activa y ranking.
# No decide por sí solo quién gana ni guarda datos directamente: llama a Gestion para usuarios y al MotorJuego para la partida.
#


"""
Castle Flesh — menu_gui.py

GUI completa compatible con:
  - gestion.py       (clase Gestion)
  - unidades.py      (FACCIONES_VALIDAS, Faccion, Unidad)
  - logica_juego.py  (crear_partida, MotorJuego, ResultadoCombate)

Facciones: Humano | Leyenda | No Muerto
"""

import tkinter as tk
from tkinter import messagebox
from gestion import Gestion
from logica_juego import (
    crear_partida, ResultadoCombate, Fase,
    FACCIONES_VALIDAS, DINERO_INICIAL_DEFENSOR, DINERO_INICIAL_ATACANTE
)

#  PALETA  (oscuro + toques por facción)
#
BG        = "#0A0A0F"
BG_PANEL  = "#12101A"
BG_INPUT  = "#1C1828"
BG_BTN    = "#1E1628"
BG_HOV    = "#2E2040"
BORDE     = "#3A2E50"
BORDE_ACT = "#7A5EAA"
FG_TITULO = "#D4AF37"
FG_SUBT   = "#8A7AAA"
FG_TEXTO  = "#C8C0D8"
FG_DIM    = "#554A6A"
FG_ERR    = "#D44040"
FG_OK     = "#50C870"

COLOR_FACCION = {
    "Humano":    {"p": "#C8A040", "s": "#1A1200", "a": "#F0D080"},
    "Leyenda":   {"p": "#40A860", "s": "#001A0A", "a": "#80F0A0"},
    "No Muerto": {"p": "#9040C8", "s": "#0D001A", "a": "#C880F0"},
}
ICONO_FACCION = {
    "Humano":    "⚔️",
    "Leyenda":   "✨",
    "No Muerto": "💀",
}

#  HELPERS GLOBALES
# 
# Función auxiliar: centra una ventana en la pantalla. Recibe la ventana y su tamaño deseado.
# 
def _centrar(win, w, h):
    win.update_idletasks()
    x = (win.winfo_screenwidth()  - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

# 
# Función auxiliar: crea una línea separadora visual. Evita repetir tk.Frame cada vez que se ocupa una línea.
# 
def _sep(parent, color=BORDE, h=1, **kw):
    return tk.Frame(parent, bg=color, height=h, **kw)

# 
# Función auxiliar: crea etiquetas de texto con estilo uniforme.
# 
def _lbl(parent, txt, size=12, bold=False, color=FG_TEXTO, bg=BG, **kw):
    return tk.Label(parent, text=txt, bg=bg, fg=color,
                    font=("Segoe UI", size, "bold" if bold else "normal"), **kw)

# 
# Función auxiliar: crea campos de entrada con estilo oscuro. Se usa para usuario y contraseña.
# 
def _entry(parent, show=None, w=26):
    return tk.Entry(parent, show=show, width=w,
                    bg=BG_INPUT, fg=FG_TEXTO, insertbackground=FG_TEXTO,
                    relief="flat", font=("Segoe UI", 12),
                    highlightthickness=1,
                    highlightbackground=BORDE, highlightcolor=BORDE_ACT)

# 
# Función auxiliar: crea botones reutilizables con efecto al pasar el mouse.
# 
def _btn(parent, txt, cmd, bg=BG_BTN, fg=FG_TEXTO, size=12, w=20, **kw):
    b = tk.Button(parent, text=txt, command=cmd, bg=bg, fg=fg,
                  font=("Segoe UI", size, "bold"), relief="flat", bd=0,
                  activebackground=BG_HOV, activeforeground="#FFF",
                  cursor="hand2", width=w, pady=9, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=BG_HOV))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

# 
# Dibuja el fondo decorativo del menú: degradado, bordes y líneas.
# 
def _fondo_canvas(cvs, ancho, alto):
    """Degradado + líneas decorativas."""
    pasos = 30
    for i in range(pasos):
    # Este for repite instrucciones para cada elemento de una lista/conjunto.
        t  = i / pasos
        r, g, b2 = int(10+t*8), int(10+t*5), int(15+t*20)
        y0 = int(i * alto / pasos)
        y1 = int((i+1) * alto / pasos)
        cvs.create_rectangle(0, y0, ancho, y1,
                              fill=f"#{r:02x}{g:02x}{b2:02x}", outline="")
    for x in (8, ancho-8):
    # Este for repite instrucciones para cada elemento de una lista/conjunto.
        cvs.create_line(x, 8, x, alto-8, fill=BORDE, width=1)
    for y in (8, alto-8):
    # Este for repite instrucciones para cada elemento de una lista/conjunto.
        cvs.create_line(8, y, ancho-8, y, fill=BORDE, width=1)
    for cx, cy in [(8,8),(ancho-8,8),(8,alto-8),(ancho-8,alto-8)]:
    # Este for repite instrucciones para cada elemento de una lista/conjunto.
        cvs.create_polygon(cx, cy-8, cx+8, cy, cx, cy+8, cx-8, cy,
                           fill=FG_TITULO, outline="")
    for i in range(0, ancho, 80):
    # Este for repite instrucciones para cada elemento de una lista/conjunto.
        cvs.create_line(i, 0, i+60, alto, fill="#1A1630", width=1)


# 
#  MENÚ PRINCIPAL
# 
# 
# Ventana principal del juego. Es la primera pantalla que aparece.
# Desde aquí se inicia una partida, se revisa el top de jugadores o se sale.
# 
class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Castle Flesh")
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.resizable(False, False)
        _centrar(self, 860, 660)
        self.gestion = Gestion()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.j1: dict = {}
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.j2: dict = {}
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._ui()

    def _ui(self):
        cvs = tk.Canvas(self, width=860, height=660, bg=BG, highlightthickness=0)
        cvs.place(x=0, y=0)
        _fondo_canvas(cvs, 860, 660)

        cen = tk.Frame(self, bg=BG)
        cen.place(relx=.5, rely=.5, anchor="center")

        tk.Label(cen, text="CASTLE FLESH", bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 52, "bold")).pack()
        tk.Label(cen, text="⚔  Defensa y Asalto de Base  ⚔",
                 bg=BG, fg=FG_SUBT,
                 font=("Segoe UI", 13, "italic")).pack(pady=(2, 22))
        _sep(cen, width=460).pack(fill="x", pady=(0, 28))

        items = [
            ("⚔   NUEVA PARTIDA",  self._nueva_partida,  FG_TITULO),
            ("🏆   TOP JUGADORES",  self._top,            FG_TEXTO),
            ("🚪   SALIR",          self.quit,            FG_ERR),
        ]
        for txt, cmd, fg in items:
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            b = tk.Button(cen, text=txt, command=cmd,
                          bg=BG_PANEL, fg=fg,
                          font=("Segoe UI", 15, "bold"),
                          relief="flat", bd=0,
                          activebackground=BG_HOV, activeforeground="#FFF",
                          cursor="hand2", width=26, pady=12,
                          highlightthickness=1, highlightbackground=BORDE)
            b.pack(pady=6)
            b.bind("<Enter>", lambda e, w=b: w.config(bg=BG_HOV, highlightbackground=BORDE_ACT))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=BG_PANEL, highlightbackground=BORDE))

        tk.Label(self, text="v0.1 Alpha  ·  Introducción a la Programación",
                 bg=BG, fg=FG_DIM, font=("Segoe UI", 9)
                 ).place(relx=.5, rely=.97, anchor="center")

    # 
    # Arranca el flujo completo de nueva partida: primero abre LoginDual y luego selección de facción.
    # 
    def _nueva_partida(self):
        LoginDual(self, self.gestion, self.j1, self.j2,
                  callback=lambda: SeleccionFaccion(self, self.j1, self.j2,
                  # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                                     callback=self._iniciar_juego))
                                                     # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    def _iniciar_juego(self):
        HUD(self, self.j1, self.j2, self.gestion)

    def _top(self):
        TopJugadores(self, self.gestion)


# 
#  LOGIN DUAL  J1 → J2
# 
# 
# Ventana de ingreso para dos jugadores.
# Primero se autentica o registra J1, después J2. Ambos deben ser usuarios distintos.
# 
class LoginDual(tk.Toplevel):
    def __init__(self, master, gestion: Gestion, j1, j2, callback):
        super().__init__(master)
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.resizable(False, False)
        self.grab_set()
        self.gestion  = gestion
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.j1, self.j2 = j1, j2
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.callback = callback
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.turno    = 1
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.title("Castle Flesh — Iniciar Sesión")
        _centrar(self, 520, 560)
        self._ui()

    def _color(self):
        return "#C8A040" if self.turno == 1 else "#9040C8"
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    def _ui(self):
        for w in self.winfo_children(): w.destroy()
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
        color = self._color()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        # Encabezado
        cab = tk.Frame(self, bg=BG); cab.pack(fill="x", padx=40, pady=(28,8))
        tk.Label(cab, text="CASTLE FLESH", bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 26, "bold")).pack()
        tk.Label(cab, text=f"— Jugador {self.turno} —", bg=BG, fg=color,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 font=("Segoe UI", 14, "bold")).pack(pady=4)
        _sep(cab, color=color).pack(fill="x", pady=(6, 0))

        # Panel
        panel = tk.Frame(self, bg=BG_PANEL,
                         highlightthickness=1, highlightbackground=BORDE)
        panel.pack(padx=45, pady=16, fill="both", expand=True)

        # Pestañas
        tabs = tk.Frame(panel, bg=BG_PANEL); tabs.pack(fill="x")
        self.tab_in  = tk.Button(tabs, text="Iniciar sesión",
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                  command=lambda: self._modo("login"),
                                  # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                  bg=BORDE_ACT, fg="#FFF",
                                  font=("Segoe UI", 11, "bold"),
                                  relief="flat", bd=0, pady=8, cursor="hand2")
        self.tab_in.pack(side="left", fill="x", expand=True)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.tab_reg = tk.Button(tabs, text="Registrarse",
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                  command=lambda: self._modo("registro"),
                                  # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                  bg=BG_PANEL, fg=FG_DIM,
                                  font=("Segoe UI", 11, "bold"),
                                  relief="flat", bd=0, pady=8, cursor="hand2")
        self.tab_reg.pack(side="left", fill="x", expand=True)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        _sep(panel, color=BORDE_ACT, h=2).pack(fill="x")

        self.form = tk.Frame(panel, bg=BG_PANEL)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.form.pack(padx=28, pady=18, fill="both", expand=True)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._form_login(color)

        self.lbl_msg = tk.Label(panel, text="", bg=BG_PANEL, fg=FG_ERR,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                 font=("Segoe UI", 10))
        self.lbl_msg.pack(pady=(0, 12))
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    # 
    # Cambia entre formulario de login y formulario de registro.
    # 
    def _modo(self, m):
        color = self._color()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        for w in self.form.winfo_children(): w.destroy()
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
        self.lbl_msg.config(text="")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if m == "login":
        # Este if toma una decisión según una condición.
            self.tab_in.config(bg=BORDE_ACT, fg="#FFF")
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.tab_reg.config(bg=BG_PANEL, fg=FG_DIM)
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self._form_login(color)
        else:
            self.tab_reg.config(bg=BORDE_ACT, fg="#FFF")
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.tab_in.config(bg=BG_PANEL, fg=FG_DIM)
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self._form_registro(color)

    def _form_login(self, color):
        f = self.form
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        _lbl(f, "Usuario", 11, color=FG_SUBT, bg=BG_PANEL).pack(anchor="w")
        self.eu = _entry(f); self.eu.pack(fill="x", ipady=6, pady=(2,12))
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        _lbl(f, "Contraseña", 11, color=FG_SUBT, bg=BG_PANEL).pack(anchor="w")
        pf = tk.Frame(f, bg=BG_PANEL); pf.pack(fill="x", pady=(2,20))
        self.ep = _entry(pf, show="●"); self.ep.pack(side="left", fill="x", expand=True, ipady=6)
        self._ver = False
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        tk.Button(pf, text="👁", command=self._toggle,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                  bg=BG_INPUT, fg=FG_DIM, relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI", 12)
                  ).pack(side="left", padx=(4,0), ipady=6)

        tk.Button(f, text="ENTRAR  ➤", command=self._login,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                  bg=color, fg="#000", font=("Segoe UI", 13, "bold"),
                  relief="flat", bd=0, pady=10, cursor="hand2",
                  activebackground=FG_TITULO).pack(fill="x")
        self.bind("<Return>", lambda e: self._login())

    def _form_registro(self, color):
        f = self.form
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        _lbl(f, "Usuario (mín. 3 caracteres)", 11, color=FG_SUBT, bg=BG_PANEL).pack(anchor="w")
        self.eu = _entry(f); self.eu.pack(fill="x", ipady=6, pady=(2,12))
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        _lbl(f, "Contraseña (mín. 4 caracteres)", 11, color=FG_SUBT, bg=BG_PANEL).pack(anchor="w")
        self.ep = _entry(f, show="●"); self.ep.pack(fill="x", ipady=6, pady=(2,12))
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        _lbl(f, "Confirmar contraseña", 11, color=FG_SUBT, bg=BG_PANEL).pack(anchor="w")
        self.ep2 = _entry(f, show="●"); self.ep2.pack(fill="x", ipady=6, pady=(2,18))
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        tk.Button(f, text="CREAR CUENTA  ➤", command=self._registro,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                  bg=color, fg="#000", font=("Segoe UI", 13, "bold"),
                  relief="flat", bd=0, pady=10, cursor="hand2",
                  activebackground=FG_TITULO).pack(fill="x")

    def _toggle(self):
        self._ver = not self._ver
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.ep.config(show="" if self._ver else "●")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    # 
    # Valida datos escritos por el usuario y pregunta a Gestion si el login es correcto.
    # 
    def _login(self):
        u, p = self.eu.get().strip(), self.ep.get()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if not u or not p:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="⚠ Completá los campos.", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        ok = self.gestion.iniciar_sesion(u, p)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if not ok:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="✗ Usuario o contraseña incorrectos.", fg=FG_ERR); return
        self.lbl_msg.config(text="✔ Sesión iniciada.", fg=FG_OK)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.after(400, lambda: self._guardar(u))

    # 
    # Valida campos y pide a Gestion crear el usuario en jugadores.json.
    # 
    def _registro(self):
        u  = self.eu.get().strip()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        p  = self.ep.get()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        p2 = self.ep2.get()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if not u or not p:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="⚠ Completá los campos.", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if len(u) < 3:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="⚠ Usuario muy corto (mín. 3).", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if len(p) < 4:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="⚠ Contraseña muy corta (mín. 4).", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if p != p2:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="✗ Las contraseñas no coinciden.", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        ok = self.gestion.registrar_usuario(u, p)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        if not ok:
        # Este if toma una decisión según una condición.
            self.lbl_msg.config(text="✗ El usuario ya existe.", fg=FG_ERR); return
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.lbl_msg.config(text="✔ Cuenta creada. Iniciando...", fg=FG_OK)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.after(600, lambda: self._guardar(u))

    # 
    # Después del login/registro, carga estadísticas del jugador y guarda los datos en j1 o j2.
    # 
    def _guardar(self, usuario):
        info = self.gestion.info_jugador(usuario)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        datos = {
            "nombre":   usuario,
            "faccion":  None,
            "victorias_defensor": info.get("victorias_defensor", 0),
            "victorias_atacante": info.get("victorias_atacante", 0),
        }
        if self.turno == 1:
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.j1.update(datos)
            self._stats(usuario, info, sig=self._ir_j2)
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        else:
            if usuario == self.j1.get("nombre"):
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                self.lbl_msg.config(text="✗ J2 debe ser distinto de J1.", fg=FG_ERR); return
                # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.j2.update(datos)
            self._stats(usuario, info, sig=self._finalizar)
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    def _stats(self, usuario, info, sig):
        """Pantalla de bienvenida con estadísticas."""
        for w in self.winfo_children(): w.destroy()
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
        color = self._color()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        tk.Label(self, text="¡Bienvenido!", bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 28, "bold")).pack(pady=(36,4))
        tk.Label(self, text=usuario, bg=BG, fg=color,
                 font=("Segoe UI", 20, "bold")).pack()
        _sep(self, color=color, width=320).pack(pady=16)

        panel = tk.Frame(self, bg=BG_PANEL,
                         highlightthickness=1, highlightbackground=BORDE)
        panel.pack(padx=60, pady=6, fill="x")

        for etiq, val, c in [
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            ("🛡  Victorias como Defensor", info.get("victorias_defensor", 0), "#C8A040"),
            ("⚔  Victorias como Atacante",  info.get("victorias_atacante", 0),  "#9040C8"),
        ]:
            fila = tk.Frame(panel, bg=BG_PANEL); fila.pack(fill="x", padx=20, pady=10)
            tk.Label(fila, text=etiq, bg=BG_PANEL, fg=FG_TEXTO,
                     font=("Segoe UI", 12)).pack(side="left")
            tk.Label(fila, text=str(val), bg=BG_PANEL, fg=c,
                     font=("Segoe UI", 16, "bold")).pack(side="right")

        txt = "Continuar con Jugador 2  ➤" if self.turno == 1 else "Elegir Facciones  ➤"
        tk.Button(self, text=txt, command=sig,
                  bg=color, fg="#000", font=("Segoe UI", 13, "bold"),
                  relief="flat", bd=0, pady=10, cursor="hand2", width=26,
                  activebackground=FG_TITULO).pack(pady=26)

    def _ir_j2(self):
        self.turno = 2; self._ui()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    def _finalizar(self):
        self.destroy(); self.callback()


# 
#  SELECCIÓN DE FACCIÓN
# 
# 
# Pantalla donde cada jugador elige una facción.
# Evita que J2 seleccione la misma facción que J1.
# 
class SeleccionFaccion(tk.Toplevel):
    def __init__(self, master, j1, j2, callback):
        super().__init__(master)
        self.title("Castle Flesh — Selección de Facción")
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.resizable(False, False)
        self.grab_set()
        _centrar(self, 1020, 700)
        self.j1, self.j2 = j1, j2
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.callback = callback
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.turno = 1
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.sel1 = self.sel2 = ""
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._ui()

    def _ui(self):
        for w in self.winfo_children(): w.destroy()
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
        color  = "#C8A040" if self.turno == 1 else "#9040C8"
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        nombre = (self.j1 if self.turno == 1 else self.j2).get("nombre", f"J{self.turno}")

        cab = tk.Frame(self, bg=BG); cab.pack(fill="x", padx=40, pady=(22,8))
        tk.Label(cab, text="SELECCIÓN DE FACCIÓN", bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 30, "bold")).pack()
        tk.Label(cab, text=f"— Turno de {nombre} —", bg=BG, fg=color,
                 font=("Segoe UI", 13, "italic")).pack(pady=4)
        _sep(cab, color=color, h=2).pack(fill="x", pady=(6,0))

        marco = tk.Frame(self, bg=BG); marco.pack(fill="both", expand=True, padx=20, pady=12)
        marco.columnconfigure((0,1,2), weight=1)

        for col, nombre_fac in enumerate(FACCIONES_VALIDAS.keys()):
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            bloq = (self.turno == 2 and self.sel1 == nombre_fac)
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self._tarjeta(marco, nombre_fac, col, bloq)

        # Pie
        pie = tk.Frame(self, bg=BG); pie.pack(fill="x", padx=40, pady=(0,14))
        _sep(pie).pack(fill="x", pady=(0,10))
        ind = tk.Frame(pie, bg=BG); ind.pack(side="left")
        for i, (jd, sel) in enumerate([(self.j1,self.sel1),(self.j2,self.sel2)], 1):
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            c   = "#C8A040" if i == 1 else "#9040C8"
            txt = sel if sel else "Sin elegir"
            row = tk.Frame(ind, bg=BG); row.pack(anchor="w", pady=2)
            tk.Label(row, text=f"J{i} — {jd.get('nombre','?')}:",
                     bg=BG, fg=c, font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0,8))
            tk.Label(row, text=txt, bg=BG, fg=FG_TEXTO,
                     font=("Segoe UI", 11)).pack(side="left")

        if self.sel1 and self.sel2:
        # Este if toma una decisión según una condición.
            tk.Button(pie, text="¡COMENZAR PARTIDA!  ⚔",
                      command=self._confirmar,
                      # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                      bg=FG_TITULO, fg="#000",
                      font=("Segoe UI", 14, "bold"),
                      relief="flat", bd=0, pady=10, cursor="hand2", width=22,
                      activebackground="#E8C040").pack(side="right")

    # 
    # Construye visualmente cada tarjeta de facción con nombre, icono y unidades.
    # 
    def _tarjeta(self, parent, nombre_fac, col, bloq):
        d  = COLOR_FACCION[nombre_fac]
        cp, cs, ca = d["p"], d["s"], d["a"]
        sel    = self.sel1 if self.turno == 1 else self.sel2
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        selec  = sel == nombre_fac
        borde  = ca if selec else (BORDE if not bloq else "#222")
        bg_c   = cs if not bloq else "#0A0A0A"
        fg_c   = FG_TEXTO if not bloq else FG_DIM

        ext = tk.Frame(parent, bg=borde, padx=2, pady=2)
        ext.grid(row=0, column=col, padx=10, pady=4, sticky="nsew")
        inner = tk.Frame(ext, bg=bg_c); inner.pack(fill="both", expand=True)

        tk.Label(inner, text=ICONO_FACCION[nombre_fac],
                 bg=bg_c, fg=cp if not bloq else "#333",
                 font=("Segoe UI", 48)).pack(pady=(16,4))
        tk.Label(inner, text=nombre_fac.upper(),
                 bg=bg_c, fg=cp if not bloq else "#444",
                 font=("Palatino Linotype", 15, "bold")).pack()

        _sep(inner, color=cp if not bloq else "#222", width=200).pack(pady=7)

        # Unidades de la facción
        tk.Label(inner, text="Unidades disponibles:",
                 bg=bg_c, fg=ca if not bloq else "#444",
                 font=("Segoe UI", 9, "bold")).pack()
        for u in FACCIONES_VALIDAS[nombre_fac]:
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            tk.Label(inner, text=f"• {u}", bg=bg_c, fg=fg_c,
                     font=("Segoe UI", 9)).pack()

        tk.Label(inner, text=" ", bg=bg_c).pack()

        if bloq:
        # Este if toma una decisión según una condición.
            tk.Label(inner, text="🔒  Elegida por J1",
                     bg=bg_c, fg="#444", font=("Segoe UI", 10, "bold")).pack(pady=(0,14))
        elif selec:
            tk.Button(inner, text="✔  SELECCIONADA",
                      command=lambda n=nombre_fac: self._elegir(n),
                      # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                      bg=cp, fg="#000", font=("Segoe UI", 11, "bold"),
                      relief="flat", bd=0, pady=8, cursor="hand2", width=18).pack(pady=(0,14))
        else:
            b = tk.Button(inner, text="ELEGIR",
                          command=lambda n=nombre_fac: self._elegir(n),
                          # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                          bg=BG_BTN, fg=FG_TEXTO, font=("Segoe UI", 11, "bold"),
                          relief="flat", bd=0, pady=8, cursor="hand2", width=18)
            b.pack(pady=(0,14))
            b.bind("<Enter>", lambda e, btn=b, c=cp: btn.config(bg=c, fg="#000"))
            b.bind("<Leave>", lambda e, btn=b: btn.config(bg=BG_BTN, fg=FG_TEXTO))

    # 
    # Guarda la facción elegida y pasa el turno al siguiente jugador.
    # 
    def _elegir(self, nombre_fac):
        if self.turno == 1:
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.sel1 = nombre_fac; self.j1["faccion"] = nombre_fac; self.turno = 2
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        else:
            self.sel2 = nombre_fac; self.j2["faccion"] = nombre_fac
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._ui()

    def _confirmar(self):
        self.destroy(); self.callback()


# 
#  HUD DE PARTIDA
# 
# 
# Pantalla de partida activa.
# Aquí se ve ronda, fase, dinero, marcador y botón principal.
# También aquí se crea el MotorJuego y se conectan callbacks.
# 
class HUD(tk.Toplevel):
    """
    Pantalla de partida activa.
    Muestra rondas, monedas, fase actual y marcador.
    El mapa/combate se conecta aquí mediante callbacks del motor.
    """
    def __init__(self, master, j1: dict, j2: dict, gestion: Gestion):
        super().__init__(master)
        self.title("Castle Flesh — Partida")
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.resizable(False, False)
        _centrar(self, 1100, 720)
        self.grab_set()

        self.j1, self.j2   = j1, j2
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.gestion        = gestion
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._fase_actual   = None
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        # Variables Tkinter para actualización dinámica
        self._var_ronda     = tk.StringVar(value="Ronda 1")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_fase      = tk.StringVar(value="—")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_din_def   = tk.StringVar(value=f"💰 {DINERO_INICIAL_DEFENSOR}")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_din_atk   = tk.StringVar(value=f"💰 {DINERO_INICIAL_ATACANTE}")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_marc_def  = tk.StringVar(value="⬛⬛⬛")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_marc_atk  = tk.StringVar(value="⬛⬛⬛")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._var_log       = tk.StringVar(value="Iniciando partida...")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        self._construir_ui()

        # Motor de juego
        self.motor = crear_partida(
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            j1, j2,
            fn_combate           = self._combate_placeholder,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            fn_cambio_fase       = self._on_fase,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            fn_fin_ronda         = self._on_fin_ronda,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            fn_fin_partida       = self._on_fin_partida,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            fn_actualizar_dinero = self._on_dinero,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        )
        self.motor.iniciar_partida()

    #   
    # 
    # Construye la pantalla principal de juego: barra superior, área de mapa y barra inferior.
    # 
    def _construir_ui(self):
        c1 = COLOR_FACCION[self.j1["faccion"]]["p"]
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        c2 = COLOR_FACCION[self.j2["faccion"]]["p"]
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        # ── Barra superior ──
        top = tk.Frame(self, bg=BG_PANEL, height=70)
        top.pack(fill="x")
        top.pack_propagate(False)

        # J1 (defensor)
        f1 = tk.Frame(top, bg=BG_PANEL); f1.pack(side="left", padx=24, pady=8)
        tk.Label(f1, text=f"{ICONO_FACCION[self.j1['faccion']]}  {self.j1['nombre']}",
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c1,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(f1, text="DEFENSOR", bg=BG_PANEL, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(f1, textvariable=self._var_din_def,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c1, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(f1, textvariable=self._var_marc_def,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c1, font=("Segoe UI", 12)).pack(anchor="w")

        # Centro
        cen = tk.Frame(top, bg=BG_PANEL); cen.pack(side="left", expand=True)
        tk.Label(cen, textvariable=self._var_ronda,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=FG_TITULO,
                 font=("Palatino Linotype", 20, "bold")).pack()
        tk.Label(cen, textvariable=self._var_fase,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=FG_SUBT,
                 font=("Segoe UI", 11, "italic")).pack()

        # J2 (atacante)
        f2 = tk.Frame(top, bg=BG_PANEL); f2.pack(side="right", padx=24, pady=8)
        tk.Label(f2, text=f"{self.j2['nombre']}  {ICONO_FACCION[self.j2['faccion']]}",
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c2,
                 font=("Segoe UI", 13, "bold")).pack(anchor="e")
        tk.Label(f2, text="ATACANTE", bg=BG_PANEL, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(anchor="e")
        tk.Label(f2, textvariable=self._var_din_atk,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c2, font=("Segoe UI", 14, "bold")).pack(anchor="e")
        tk.Label(f2, textvariable=self._var_marc_atk,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=c2, font=("Segoe UI", 12)).pack(anchor="e")

        _sep(self, color=BORDE_ACT, h=2).pack(fill="x")

        # ── Área principal (mapa va aquí) ──
        self.area_mapa = tk.Frame(self, bg="#0D0B15",
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                                   highlightthickness=1,
                                   highlightbackground=BORDE)
        self.area_mapa.pack(fill="both", expand=True, padx=16, pady=12)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        # Placeholder central
        self._lbl_placeholder = tk.Label(
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.area_mapa,
            text="[ MAPA DEL JUEGO ]\n\nAquí se renderizará la cuadrícula\nde juego implementada por el equipo.",
            bg="#0D0B15", fg=FG_DIM,
            font=("Segoe UI", 14, "italic"),
            justify="center"
        )
        self._lbl_placeholder.place(relx=.5, rely=.5, anchor="center")
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        _sep(self, color=BORDE).pack(fill="x")

        # ── Barra inferior ──
        bot = tk.Frame(self, bg=BG_PANEL, height=60)
        bot.pack(fill="x"); bot.pack_propagate(False)

        tk.Label(bot, textvariable=self._var_log,
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                 bg=BG_PANEL, fg=FG_TEXTO,
                 font=("Segoe UI", 10, "italic")).pack(side="left", padx=20, pady=16)

        self._btn_accion = tk.Button(
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            bot, text="CONFIRMAR CONSTRUCCIÓN  ➤",
            command=self._accion_principal,
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            bg=FG_TITULO, fg="#000",
            font=("Segoe UI", 12, "bold"),
            relief="flat", bd=0, pady=10, cursor="hand2", width=28,
            activebackground="#E8C040"
        )
        self._btn_accion.pack(side="right", padx=16, pady=8)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

    # Callbacks del motor 
    # 
    # Callback llamado por MotorJuego cuando cambia la fase. Actualiza texto y botón.
    # 
    def _on_fase(self, fase: Fase):
        self._fase_actual = fase
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        textos = {
            Fase.CONSTRUCCION: ("Fase de Construcción", "CONFIRMAR CONSTRUCCIÓN  ➤"),
            Fase.DESPLIEGUE:   ("Fase de Despliegue",   "CONFIRMAR DESPLIEGUE  ➤"),
            Fase.COMBATE:      ("⚔ Combate en curso...", ""),
            Fase.FIN_RONDA:    ("Fin de Ronda",          "SIGUIENTE RONDA  ➤"),
            Fase.FIN_PARTIDA:  ("¡Partida terminada!",   ""),
        }
        fase_txt, btn_txt = textos.get(fase, ("—", ""))
        self._var_fase.set(fase_txt)
        self._var_ronda.set(f"Ronda {self.motor.ronda_actual}")
        if btn_txt:
        # Este if toma una decisión según una condición.
            self._btn_accion.config(text=btn_txt, state="normal")
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        else:
            self._btn_accion.config(state="disabled")
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self._log(f"Fase: {fase_txt}")

    # 
    # Callback llamado por MotorJuego cuando cambia el dinero. Actualiza los valores visibles.
    # 
    def _on_dinero(self, din_def: int, din_atk: int):
        self._var_din_def.set(f"💰 {din_def}")
        self._var_din_atk.set(f"💰 {din_atk}")

    # 
    # Callback llamado al terminar una ronda. Actualiza marcador y muestra resumen.
    # 
    def _on_fin_ronda(self, resumen):
        def _estrella(n):
            return "⭐" * n + "⬛" * (3 - n)
        self._var_marc_def.set(_estrella(self.motor.defensor.rondas_ganadas))
        self._var_marc_atk.set(_estrella(self.motor.atacante.rondas_ganadas))
        self._log(f"Ronda {resumen.numero} — Ganador: {resumen.ganador_nombre}")
        self._mostrar_resumen_ronda(resumen)

    # 
    # Callback llamado cuando alguien gana la partida completa.
    # 
    def _on_fin_partida(self, ganador):
        self._log(f"🏆 ¡{ganador.nombre} gana la partida!")
        self.after(300, lambda: self._pantalla_fin(ganador))

    # Botón principal 
    # 
    # Botón único que hace cosas distintas según la fase actual.
    # 
    def _accion_principal(self):
        if self._fase_actual == Fase.CONSTRUCCION:
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.motor.confirmar_construccion()
        elif self._fase_actual == Fase.DESPLIEGUE:
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.motor.confirmar_despliegue()
        elif self._fase_actual == Fase.FIN_RONDA:
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            self.motor.siguiente_ronda()

    # Combate placeholder 
    # 
    # Combate temporal. Debe reemplazarse por el módulo real de combate.
    # 
    def _combate_placeholder(self, defensor, atacante) -> ResultadoCombate:
        """
        REEMPLAZAR por el módulo de combate real cuando esté listo.
        Por ahora simula que el defensor siempre gana.
        """
        self._log("⚔ Ejecutando combate...")
        return ResultadoCombate(
            unidades_eliminadas=len(atacante.unidades),
            base_destruida=False,
        )

    #  Ventana resumen de ronda 
    def _mostrar_resumen_ronda(self, resumen):
        pop = tk.Toplevel(self)
        pop.title("Resumen de Ronda")
        pop.configure(bg=BG)
        pop.resizable(False, False)
        pop.grab_set()
        _centrar(pop, 420, 340)

        c = COLOR_FACCION[
            self.j1["faccion"] if resumen.ganador_nombre == self.j1["nombre"]
            # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
            else self.j2["faccion"]
        ]["p"]

        tk.Label(pop, text=f"RONDA {resumen.numero}",
                 bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 24, "bold")).pack(pady=(24,4))
        tk.Label(pop, text=f"🏆  {resumen.ganador_nombre}",
                 bg=BG, fg=c,
                 font=("Segoe UI", 18, "bold")).pack()
        _sep(pop, color=c, width=300).pack(pady=14)

        panel = tk.Frame(pop, bg=BG_PANEL); panel.pack(padx=40, fill="x")
        stats = []
        if resumen.combate:
        # Este if toma una decisión según una condición.
            stats = [
                ("Unidades eliminadas", resumen.combate.unidades_eliminadas),
                ("Daño a la base",      resumen.combate.daño_a_base),
                ("Torres destruidas",   resumen.combate.torres_destruidas),
            ]
        for etiq, val in stats:
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            fila = tk.Frame(panel, bg=BG_PANEL); fila.pack(fill="x", padx=16, pady=5)
            tk.Label(fila, text=etiq, bg=BG_PANEL, fg=FG_TEXTO,
                     font=("Segoe UI", 11)).pack(side="left")
            tk.Label(fila, text=str(val), bg=BG_PANEL, fg=c,
                     font=("Segoe UI", 13, "bold")).pack(side="right")

        _sep(pop, width=340).pack(pady=14)
        tk.Button(pop, text="CONTINUAR  ➤",
                  command=pop.destroy,
                  bg=c, fg="#000",
                  font=("Segoe UI", 13, "bold"),
                  relief="flat", bd=0, pady=9, cursor="hand2", width=20,
                  activebackground=FG_TITULO).pack()

    #  Pantalla de fin de partida 
    def _pantalla_fin(self, ganador):
        for w in self.winfo_children(): w.destroy()
        # Este for repite instrucciones para cada elemento de una lista/conjunto.

        c = COLOR_FACCION[ganador.faccion]["p"]
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.

        tk.Label(self, text="⚔  PARTIDA TERMINADA  ⚔",
                 bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 34, "bold")).pack(pady=(80,10))
        tk.Label(self, text="¡Ganador!",
                 bg=BG, fg=FG_SUBT,
                 font=("Segoe UI", 14)).pack()
        tk.Label(self, text=ganador.nombre,
                 bg=BG, fg=c,
                 font=("Palatino Linotype", 48, "bold")).pack(pady=8)
        tk.Label(self, text=f"{ICONO_FACCION[ganador.faccion]}  {ganador.faccion}  ·  {ganador.rol.value.capitalize()}",
                 bg=BG, fg=c,
                 font=("Segoe UI", 15)).pack()

        _sep(self, color=c, width=400).pack(pady=24)

        # Marcador final
        panel = tk.Frame(self, bg=BG_PANEL); panel.pack(padx=140, fill="x")
        for jd, jj in [(self.motor.defensor, self.j1), (self.motor.atacante, self.j2)]:
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            cf = COLOR_FACCION[jd.faccion]["p"]
            fila = tk.Frame(panel, bg=BG_PANEL); fila.pack(fill="x", padx=20, pady=8)
            tk.Label(fila, text=f"{jd.nombre}  ({jd.rol.value})",
                     bg=BG_PANEL, fg=cf,
                     font=("Segoe UI", 13, "bold")).pack(side="left")
            tk.Label(fila, text=f"{'⭐' * jd.rondas_ganadas}",
                     bg=BG_PANEL, fg=cf,
                     font=("Segoe UI", 14)).pack(side="right")

        _sep(self, color=BORDE, width=400).pack(pady=20)
        tk.Button(self, text="VOLVER AL MENÚ",
                  command=self.destroy,
                  # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
                  bg=c, fg="#000",
                  font=("Segoe UI", 14, "bold"),
                  relief="flat", bd=0, pady=12, cursor="hand2", width=22,
                  activebackground=FG_TITULO).pack()

    def _log(self, msg: str):
        self._var_log.set(msg)


# 
#  TOP JUGADORES
# 
# 
# Ventana que muestra rankings de mejores defensores y atacantes usando Gestion.
# 
class TopJugadores(tk.Toplevel):
    def __init__(self, master, gestion: Gestion):
        super().__init__(master)
        self.title("Castle Flesh — Top Jugadores")
        self.configure(bg=BG)
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.
        self.resizable(False, False)
        self.grab_set()
        _centrar(self, 680, 520)
        self._ui(gestion)

    def _ui(self, g: Gestion):
        tk.Label(self, text="🏆  TOP JUGADORES",
                 bg=BG, fg=FG_TITULO,
                 font=("Palatino Linotype", 28, "bold")).pack(pady=(28,6))
        _sep(self, color=FG_TITULO).pack(fill="x", padx=50, pady=(0,20))

        marco = tk.Frame(self, bg=BG); marco.pack(fill="both", expand=True, padx=30)
        marco.columnconfigure((0,1), weight=1)

        top_d = g.top_defensores()
        top_a = g.top_atacantes()
        medallas = ["🥇","🥈","🥉","④","⑤"]

        for col, (titulo, top, key, color) in enumerate([
        # Este for repite instrucciones para cada elemento de una lista/conjunto.
            ("🛡  Defensores", top_d, "victorias_defensor", "#C8A040"),
            ("⚔  Atacantes",  top_a, "victorias_atacante",  "#9040C8"),
        ]):
            cf = tk.Frame(marco, bg=BG); cf.grid(row=0, column=col, padx=10, sticky="nsew")
            tk.Label(cf, text=titulo, bg=BG, fg=color,
                     font=("Segoe UI", 14, "bold")).pack(pady=(0,10))
            if top:
            # Este if toma una decisión según una condición.
                for i, (user, dat) in enumerate(top):
                # Este for repite instrucciones para cada elemento de una lista/conjunto.
                    fila = tk.Frame(cf, bg=BG_PANEL,
                                    highlightthickness=1, highlightbackground=BORDE)
                    fila.pack(fill="x", pady=3, ipady=7, ipadx=10)
                    tk.Label(fila, text=medallas[i], bg=BG_PANEL, fg=color,
                             font=("Segoe UI", 13, "bold"), width=3).pack(side="left")
                    tk.Label(fila, text=user, bg=BG_PANEL, fg=FG_TEXTO,
                             font=("Segoe UI", 12)).pack(side="left")
                    tk.Label(fila, text=f"{dat.get(key, 0)} victorias",
                             bg=BG_PANEL, fg=FG_DIM,
                             font=("Segoe UI", 11)).pack(side="right", padx=10)
            else:
                tk.Label(cf, text="Sin registros aún", bg=BG, fg=FG_DIM,
                         font=("Segoe UI", 11, "italic")).pack(pady=20)

        _sep(self).pack(fill="x", padx=50, pady=18)
        _btn(self, "← VOLVER", self.destroy, w=16).pack()
        # Nota: self significa “este objeto”; guarda datos propios de esta ventana/clase.


# 
#  MAIN
# 
if __name__ == "__main__":
# Este if toma una decisión según una condición.
    app = MenuPrincipal()
    app.mainloop()
