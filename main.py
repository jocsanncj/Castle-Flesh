from __future__ import annotations

import os
import unicodedata
from difflib import SequenceMatcher
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog

from gestion import Gestion
from edificios import (
    Torre,
    Muro,
    crear_torre,
    crear_muro,
    crear_torre_central,
    listar_torres
)
from unidades import obtener_faccion, listar_facciones


#Pillow es opcional. Si no está instalado, el juego usa figuras de colores.
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False


#Pygame se utiliza únicamente para reproducir la música del juego.
try:
    import pygame
    PYGAME_DISPONIBLE = True
except ImportError:
    pygame = None
    PYGAME_DISPONIBLE = False


#Ruta principal del proyecto
BASE_DIR = Path(__file__).resolve().parent

#Configuración del tablero horizontal
FILAS_MAPA = 12
COLUMNAS_MAPA = 18
TAM_CELDA = 45
COLUMNAS_DESPLIEGUE = 4
COLUMNA_INICIO_DEFENSA = 7
TORRE_CENTRAL_ALTO = 4
TORRE_CENTRAL_ANCHO = 4
ORIGEN_TORRE_CENTRAL = (
    (FILAS_MAPA - TORRE_CENTRAL_ALTO) // 2,
    COLUMNAS_MAPA - TORRE_CENTRAL_ANCHO - 1
)
POSICION_CENTRAL = (
    ORIGEN_TORRE_CENTRAL[0] + TORRE_CENTRAL_ALTO // 2,
    ORIGEN_TORRE_CENTRAL[1] + TORRE_CENTRAL_ANCHO // 2
)
MAX_TURNOS_COMBATE = 55

#Tiempo de espera antes de ejecutar el primer turno del combate
#El valor se expresa en milisegundos
RETARDO_INICIO_COMBATE = 800

#Tiempo de espera entre cada turno automático
#Un valor mayor hace que el combate sea más fácil de seguir visualmente
RETARDO_ENTRE_TURNOS = 650

#Economía de la partida
DINERO_INICIAL_DEFENSOR = 1100
DINERO_INICIAL_ATACANTE = 1000
BONO_POR_RONDA = 180
RECOMPENSA_POR_UNIDAD = 25
RECOMPENSA_POR_DESTRUCCION = 45
RONDAS_PARA_GANAR = 3

#Paleta general inspirada en fantasía nocturna
BG = "#06131D"
BG_PANEL = "#0E2633"
BG_INPUT = "#173746"
BG_MAPA = "#081B24"
BORDE = "#2F6673"
DORADO = "#F4A261"
TEXTO = "#F1F7F9"
TEXTO_SUAVE = "#A9C3CA"
VERDE = "#2EC4B6"
ROJO = "#E76F51"
AZUL = "#4CC9F0"

#Cada facción conserva un color propio dentro de la nueva paleta
COLOR_FACCION = {
    "Humano": "#F4A261",
    "No muerto": "#C77DFF",
    "Leyenda": "#2EC4B6"
}

ICONO_FACCION = {
    "Humano": "H",
    "No muerto": "N",
    "Leyenda": "L"
}

ABREVIATURAS = {
    "Torre de Magos": "TM",
    "Torre de Arqueras": "TA",
    "Cañón": "C",
    "Muro": "M",
    "Torre Central": "TC",
    "Valquiria": "V",
    "Matón": "MT",
    "Bandido": "B",
    "Esqueleto": "E",
    "Zombie": "Z",
    "Espectro": "ES",
    "Goblin": "G",
    "Minotauro": "MI",
    "Golem": "GO"
}


#Estructura de datos que resume todo lo ocurrido durante un combate.
#Se usa al finalizar una ronda para actualizar dinero, marcador y registro de eventos.

@dataclass
class ResultadoCombate:
    #Guarda las estadísticas principales de una ronda
    ganador: str
    turnos: int
    unidades_eliminadas: int = 0
    daño_a_estructuras: int = 0
    estructuras_destruidas: int = 0
    daño_a_base: int = 0
    base_destruida: bool = False
    eventos: list = field(default_factory=list)


#Servicio encargado de localizar, cargar, redimensionar y almacenar sprites.
#La búsqueda tolera diferencias de mayúsculas, tildes, espacios y rutas antiguas.

class GestorSprites:
    #Prepara la caché de imágenes y las estructuras usadas para localizar sprites.

    def __init__(self):
        #Guarda las imágenes cargadas para evitar abrirlas repetidamente
        self.cache = {}

        #Guarda las rutas encontradas dentro del proyecto
        self.archivos_imagen = None

        #Evita repetir el mismo mensaje de error muchas veces
        self.rutas_faltantes = set()

    #Convierte un nombre o una ruta a un formato uniforme para facilitar comparaciones.

    def normalizar(self, texto):
        #Convierte rutas y nombres a una forma comparable
        texto = str(texto).replace("\\", "/")
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            caracter for caracter in texto
            if not unicodedata.combining(caracter)
        )
        texto = texto.casefold()

        #Trata arqueros y arqueras como el mismo nombre visual
        texto = texto.replace("torre de arqueros", "torre arquera")
        texto = texto.replace("torre de arqueras", "torre arquera")

        #Elimina signos y espacios para tolerar diferencias de nombres
        return "".join(caracter for caracter in texto if caracter.isalnum())

    #Construye la lista de carpetas donde pueden encontrarse recursos gráficos.

    def raices_busqueda(self):
        #Busca sprites junto al programa, en la carpeta actual y en una carpeta hermana
        posibles = [
            BASE_DIR,
            BASE_DIR / "Sprites",
            BASE_DIR.parent / "Sprites"
        ]

        #Incluye la carpeta de ejecución solamente cuando parece ser el proyecto
        actual = Path.cwd()
        #Comprueba que el archivo o la carpeta exista antes de usarlo
        if actual != Path(actual.anchor) and (
            (actual / "Sprites").exists()
            or (actual / "main.py").exists()
        ):
            posibles.extend([actual, actual / "Sprites"])

        raices = []
        vistas = set()
        #Recorre las rutas disponibles hasta encontrar el recurso correcto
        for ruta in posibles:
            #Intenta ejecutar esta operación y controla cualquier error posible
            try:
                ruta = ruta.resolve()
            except OSError:
                #Omite este elemento y continúa con la siguiente repetición
                continue

            #Comprueba que el archivo o la carpeta exista antes de usarlo
            if ruta.exists() and ruta not in vistas:
                #Agrega el elemento al conjunto para evitar duplicados
                vistas.add(ruta)
                #Agrega el elemento a la lista para conservarlo durante la partida
                raices.append(ruta)

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return raices

    #Recorre las carpetas de recursos una sola vez y registra todas las imágenes disponibles.

    def indexar_imagenes(self):
        #Crea una lista de imágenes disponibles para búsquedas tolerantes
        if self.archivos_imagen is not None:
            #Finaliza el método y devuelve el control al punto anterior
            return

        extensiones = {".png", ".gif", ".jpg", ".jpeg", ".webp"}
        encontrados = []
        vistas = set()

        #Recorre los elementos de esta colección para procesarlos uno por uno
        for raiz in self.raices_busqueda():
            #os.walk ignora carpetas sin permiso mediante onerror
            for carpeta, _, nombres in os.walk(
                raiz,
                onerror=lambda error: None
            ):
                #Recorre los elementos de esta colección para procesarlos uno por uno
                for nombre in nombres:
                    archivo = Path(carpeta) / nombre
                    #Evalúa esta condición para decidir qué acción debe ejecutarse
                    if archivo.suffix.casefold() not in extensiones:
                        #Omite este elemento y continúa con la siguiente repetición
                        continue

                    #Intenta ejecutar esta operación y controla cualquier error posible
                    try:
                        resuelta = archivo.resolve()
                    except OSError:
                        resuelta = archivo

                    #Evalúa esta condición para decidir qué acción debe ejecutarse
                    if resuelta in vistas:
                        #Omite este elemento y continúa con la siguiente repetición
                        continue

                    #Agrega el elemento al conjunto para evitar duplicados
                    vistas.add(resuelta)
                    #Agrega el elemento a la lista para conservarlo durante la partida
                    encontrados.append(resuelta)

        #Guarda archivos imagen como parte del estado que utilizará esta clase
        self.archivos_imagen = encontrados

    #Busca una ruta válida para un sprite, incluso cuando el nombre no coincide exactamente.

    def resolver_ruta(self, ruta):
        #Acepta listas antiguas y utiliza la primera ruta válida
        if isinstance(ruta, (list, tuple)):
            #Recorre los elementos de esta colección para procesarlos uno por uno
            for opcion in ruta:
                #Obtiene el recurso gráfico que corresponde al objeto actual
                encontrada = self.resolver_ruta(opcion)
                #Comprueba que el dato necesario exista antes de continuar
                if encontrada is not None:
                    #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                    return encontrada
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        #Comprueba que se cumplan los requisitos antes de continuar
        if not ruta:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        ruta_texto = str(ruta).strip().replace("\\", "/")
        ruta_objeto = Path(ruta_texto)

        #Prueba primero la ruta absoluta
        if ruta_objeto.is_absolute() and ruta_objeto.exists():
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return ruta_objeto

        #Prueba las ubicaciones más comunes sin realizar una búsqueda completa
        for raiz in self.raices_busqueda():
            candidatos = [raiz / ruta_objeto]

            #Si la raíz ya es la carpeta Sprites, evita repetir "Sprites"
            partes = ruta_objeto.parts
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if partes and self.normalizar(partes[0]) == "sprites":
                #Agrega el elemento a la lista para conservarlo durante la partida
                candidatos.append(raiz.joinpath(*partes[1:]))

            #Recorre los elementos de esta colección para procesarlos uno por uno
            for candidato in candidatos:
                #Comprueba que el archivo o la carpeta exista antes de usarlo
                if candidato.exists() and candidato.is_file():
                    #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                    return candidato

        #Busca por similitud cuando hay diferencias de mayúsculas, tildes o nombres
        self.indexar_imagenes()
        solicitada = self.normalizar(ruta_texto)
        nombre_solicitado = self.normalizar(ruta_objeto.name)

        mejor = None
        mejor_puntaje = 0.0

        #Recorre las rutas disponibles hasta encontrar el recurso correcto
        for archivo in self.archivos_imagen:
            normalizada = self.normalizar(archivo.as_posix())
            nombre_archivo = self.normalizar(archivo.name)

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if nombre_archivo != nombre_solicitado:
                #Omite este elemento y continúa con la siguiente repetición
                continue

            #La comparación completa ayuda cuando existen muchos archivos full.png
            puntaje = SequenceMatcher(
                None,
                solicitada,
                normalizada
            ).ratio()

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if normalizada.endswith(solicitada):
                puntaje += 2.0

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if puntaje > mejor_puntaje:
                mejor = archivo
                mejor_puntaje = puntaje

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return mejor

    #Carga y ajusta una imagen al tamaño solicitado; reutiliza resultados mediante una caché.

    def cargar(self, ruta, ancho, alto):
        #Localiza la imagen dentro del proyecto
        ruta_completa = self.resolver_ruta(ruta)

        #Comprueba que el dato necesario exista antes de continuar
        if ruta_completa is None or not ruta_completa.exists():
            clave_faltante = str(ruta)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if clave_faltante not in self.rutas_faltantes:
                #Agrega el elemento al conjunto para evitar duplicados
                self.rutas_faltantes.add(clave_faltante)
                print(f"[Sprites] No se encontró: {ruta}")
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        clave = (str(ruta_completa), ancho, alto)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if clave in self.cache:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.cache[clave]

        #Intenta ejecutar esta operación y controla cualquier error posible
        try:
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if PIL_DISPONIBLE:
                imagen = Image.open(ruta_completa).convert("RGBA")

                #Elimina bordes transparentes para aprovechar mejor la casilla
                alfa = imagen.getchannel("A")
                limites = alfa.getbbox()
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if limites:
                    imagen = imagen.crop(limites)

                imagen.thumbnail((ancho, alto), Image.Resampling.LANCZOS)
                foto = ImageTk.PhotoImage(imagen)
            else:
                #Tkinter también puede cargar PNG aunque con menos opciones de ajuste
                original = tk.PhotoImage(file=str(ruta_completa))
                factor_ancho = max(1, (original.width() + ancho - 1) // ancho)
                factor_alto = max(1, (original.height() + alto - 1) // alto)
                factor = max(factor_ancho, factor_alto)
                foto = original.subsample(factor, factor)

            self.cache[clave] = foto
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return foto
        except Exception as error:
            clave_faltante = str(ruta_completa)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if clave_faltante not in self.rutas_faltantes:
                #Agrega el elemento al conjunto para evitar duplicados
                self.rutas_faltantes.add(clave_faltante)
                print(f"[Sprites] No se pudo abrir {ruta_completa}: {error}")
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None


#Controlador de música ambiental basado en pygame.mixer.
#Permite iniciar automáticamente, pausar, reanudar y seleccionar un archivo de audio.

class GestorMusica:
    #Inicializa el estado interno del reproductor sin arrancar todavía pygame.

    def __init__(self):
        #Guarda el archivo de música seleccionado
        self.archivo = None

        #Indica si ya existe una canción cargada en pygame
        self.cargada = False

        #Indica si la canción está pausada
        self.pausada = False

        #Indica si pygame.mixer fue inicializado
        self.inicializada = False

    #Inicializa el mezclador de audio de pygame de forma segura.

    def inicializar(self):
        #Comprueba que pygame se encuentre instalado
        if not PYGAME_DISPONIBLE:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Pygame no está instalado. Ejecuta: pip install pygame"

        #Evita inicializar el mezclador más de una vez
        if self.inicializada:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return True, ""

        #Intenta ejecutar esta operación y controla cualquier error posible
        try:
            #Inicializa únicamente el módulo de audio de pygame
            pygame.mixer.init()
            #Guarda inicializada como parte del estado que utilizará esta clase
            self.inicializada = True
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return True, ""
        except Exception as error:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, f"No fue posible iniciar el audio: {error}"

    #Busca automáticamente el primer archivo de música compatible dentro del proyecto.

    def buscar_archivo(self):
        #Extensiones de audio admitidas por el juego
        extensiones = {".mp3", ".ogg", ".wav"}

        #Carpetas donde se intenta localizar una canción automáticamente
        carpetas = [
            BASE_DIR / "Musica",
            BASE_DIR / "Música",
            BASE_DIR / "Music",
            BASE_DIR / "Sonidos",
            BASE_DIR
        ]

        #Recorre las carpetas hasta encontrar el primer archivo de audio
        for carpeta in carpetas:
            #Comprueba que el archivo o la carpeta exista antes de usarlo
            if not carpeta.exists():
                #Omite este elemento y continúa con la siguiente repetición
                continue

            #Recorre las rutas disponibles hasta encontrar el recurso correcto
            for archivo in carpeta.rglob("*"):
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if archivo.is_file() and archivo.suffix.casefold() in extensiones:
                    #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                    return archivo

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return None

    #Abre el selector de archivos para que el usuario elija una canción manualmente.

    def seleccionar_archivo(self, parent):
        #Abre una ventana para seleccionar música manualmente
        ruta = filedialog.askopenfilename(
            parent=parent,
            title="Seleccionar música",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.ogg *.wav"),
                ("Todos los archivos", "*.*")
            ]
        )

        #Retorna None cuando el usuario cancela la selección
        if not ruta:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return Path(ruta)

    #Carga una canción y la reproduce en bucle durante la ejecución del juego.

    def reproducir_archivo(self, archivo):
        #Inicializa pygame antes de cargar la canción
        correcto, mensaje = self.inicializar()
        #Comprueba que se cumplan los requisitos antes de continuar
        if not correcto:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, mensaje

        #Intenta ejecutar esta operación y controla cualquier error posible
        try:
            #Carga el archivo y lo reproduce indefinidamente
            pygame.mixer.music.load(str(archivo))
            #Inicia la reproducción continua de la música seleccionada
            pygame.mixer.music.play(-1)

            #Guarda el estado actual del reproductor
            self.archivo = Path(archivo)
            #Guarda cargada como parte del estado que utilizará esta clase
            self.cargada = True
            #Guarda pausada como parte del estado que utilizará esta clase
            self.pausada = False
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return True, f"Reproduciendo: {self.archivo.name}"
        except Exception as error:
            #Guarda archivo como parte del estado que utilizará esta clase
            self.archivo = None
            #Guarda cargada como parte del estado que utilizará esta clase
            self.cargada = False
            #Guarda pausada como parte del estado que utilizará esta clase
            self.pausada = False
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, f"No fue posible reproducir la música: {error}"

    #Intenta iniciar la música al abrir la aplicación sin mostrar ventanas adicionales.

    def iniciar_automaticamente(self):
        #No abre ventanas al iniciar; solamente usa una canción incluida en el proyecto
        if self.cargada and not self.pausada:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return True, "La música ya se encuentra activa."

        archivo = self.buscar_archivo()
        #Comprueba que el dato necesario exista antes de continuar
        if archivo is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No se encontró música dentro de la carpeta del proyecto."

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return self.reproducir_archivo(archivo)

    #Cambia entre reproducción y pausa; también permite escoger una canción si todavía no existe una.

    def alternar(self, parent):
        #Reanuda la música cuando estaba pausada
        if self.cargada and self.pausada:
            #Intenta ejecutar esta operación y controla cualquier error posible
            try:
                #Reanuda la música desde el punto donde se había pausado
                pygame.mixer.music.unpause()
                #Guarda pausada como parte del estado que utilizará esta clase
                self.pausada = False
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return True, "Música reanudada."
            except Exception as error:
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return False, f"No fue posible reanudar la música: {error}"

        #Pausa la música cuando se encuentra activa
        if self.cargada and not self.pausada:
            #Intenta ejecutar esta operación y controla cualquier error posible
            try:
                #Pausa la música sin perder el punto actual de reproducción
                pygame.mixer.music.pause()
                #Guarda pausada como parte del estado que utilizará esta clase
                self.pausada = True
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return False, "Música pausada."
            except Exception as error:
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return False, f"No fue posible pausar la música: {error}"

        #Busca una canción incluida dentro de la carpeta del proyecto
        archivo = self.buscar_archivo()

        #Permite seleccionar una canción cuando no existe una dentro del proyecto
        if archivo is None:
            archivo = self.seleccionar_archivo(parent)

        #Comprueba que el dato necesario exista antes de continuar
        if archivo is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No se seleccionó ningún archivo de música."

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return self.reproducir_archivo(archivo)

    #Devuelve el texto y los colores del botón según el estado actual de la música.

    def estilo_boton(self):
        #Retorna el texto y los colores que representan el estado actual
        if self.cargada and not self.pausada:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return "MÚSICA: ENCENDIDA", VERDE, "#001B1A"

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if self.cargada and self.pausada:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return "MÚSICA: PAUSADA", BG_INPUT, TEXTO

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return "MÚSICA: APAGADA", BG_INPUT, TEXTO

    #Detiene el audio y libera los recursos de pygame antes de cerrar la aplicación.

    def cerrar(self):
        #Detiene la música antes de cerrar el programa
        if not PYGAME_DISPONIBLE or not self.inicializada:
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Intenta ejecutar esta operación y controla cualquier error posible
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass


#Modelo principal de la partida activa.
#Conserva jugadores, facciones, dinero, fase, estructuras, unidades y marcador por rondas.

class EstadoPartida:
    #Crea el estado de una nueva partida con los dos jugadores y su gestor de persistencia.

    def __init__(self, defensor, atacante, gestion):
        #Guarda los datos de ambos jugadores
        self.datos_defensor = defensor
        #Guarda datos atacante como parte del estado que utilizará esta clase
        self.datos_atacante = atacante
        #Guarda gestion como parte del estado que utilizará esta clase
        self.gestion = gestion

        #Guarda el marcador general
        self.rondas_defensor = 0
        #Guarda rondas atacante como parte del estado que utilizará esta clase
        self.rondas_atacante = 0
        #Guarda ronda actual como parte del estado que utilizará esta clase
        self.ronda_actual = 0

        #Guarda bonos obtenidos durante el combate anterior
        self.bono_defensor = 0
        #Guarda bono atacante como parte del estado que utilizará esta clase
        self.bono_atacante = 0

        #Guarda las estructuras y unidades actuales
        self.torres = []
        #Guarda muros como parte del estado que utilizará esta clase
        self.muros = []
        #Guarda unidades como parte del estado que utilizará esta clase
        self.unidades = []
        #Guarda torre central como parte del estado que utilizará esta clase
        self.torre_central = None

        #Guarda la fase y el dinero
        self.fase = "construccion"
        #Guarda dinero defensor como parte del estado que utilizará esta clase
        self.dinero_defensor = 0
        #Guarda dinero atacante como parte del estado que utilizará esta clase
        self.dinero_atacante = 0

        self.nueva_ronda()

    #Expone la facción seleccionada por el jugador defensor.

    @property
    def faccion_defensor(self):
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return self.datos_defensor["faccion"]

    #Expone la facción seleccionada por el jugador atacante.

    @property
    def faccion_atacante(self):
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return self.datos_atacante["faccion"]

    #Reinicia el tablero, crea la torre central y calcula el dinero disponible para una nueva ronda.

    def nueva_ronda(self):
        #Aumenta el número de ronda y limpia el mapa anterior
        self.ronda_actual += 1
        #Guarda torres como parte del estado que utilizará esta clase
        self.torres = []
        #Guarda muros como parte del estado que utilizará esta clase
        self.muros = []
        #Guarda unidades como parte del estado que utilizará esta clase
        self.unidades = []

        #Crea automáticamente la torre central en el centro del mapa
        #Crea la torre central usando la firma original de edificios.py
        self.torre_central = crear_torre_central(self.faccion_defensor)

        #Ajusta la posición al centro del mapa grande
        if self.torre_central is not None:
            self.torre_central.posicion_fija = POSICION_CENTRAL
            self.torre_central.posicion = POSICION_CENTRAL

        #Calcula el dinero inicial de la ronda
        bono_ronda = (self.ronda_actual - 1) * BONO_POR_RONDA
        #Guarda dinero defensor como parte del estado que utilizará esta clase
        self.dinero_defensor = (
            DINERO_INICIAL_DEFENSOR
            + bono_ronda
            + self.bono_defensor
        )
        #Guarda dinero atacante como parte del estado que utilizará esta clase
        self.dinero_atacante = (
            DINERO_INICIAL_ATACANTE
            + bono_ronda
            + self.bono_atacante
        )

        #Los bonos se consumen al comenzar la ronda
        self.bono_defensor = 0
        #Guarda bono atacante como parte del estado que utilizará esta clase
        self.bono_atacante = 0
        #Guarda fase como parte del estado que utilizará esta clase
        self.fase = "construccion"

    #Comprueba si una posición pertenece a los límites válidos del tablero.

    def dentro_mapa(self, posicion):
        #Comprueba que una posición pertenezca al tablero
        fila, columna = posicion
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return (
            0 <= fila < FILAS_MAPA
            and 0 <= columna < COLUMNAS_MAPA
        )

    #Calcula todas las casillas ocupadas por la torre central de tamaño ampliado.

    def casillas_torre_central(self):
        #Retorna las dieciséis casillas ocupadas por la torre central
        fila_inicial, columna_inicial = ORIGEN_TORRE_CENTRAL
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return {
            (fila, columna)
            for fila in range(
                fila_inicial,
                fila_inicial + TORRE_CENTRAL_ALTO
            )
            for columna in range(
                columna_inicial,
                columna_inicial + TORRE_CENTRAL_ANCHO
            )
        }

    #Devuelve el conjunto de casillas ocupado por una estructura o unidad.

    def casillas_objeto(self, objeto):
        #La torre central ocupa 4 x 4; los demás objetos ocupan una casilla
        if objeto is self.torre_central:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.casillas_torre_central()
        #Comprueba que la posición sea válida y esté disponible
        if objeto is None or objeto.posicion is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return set()
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return {objeto.posicion}

    #Calcula la menor distancia Manhattan entre una posición y las casillas de un objeto.

    def distancia_a_objeto(self, posicion, objeto):
        #Calcula la menor distancia hacia cualquiera de las casillas del objeto
        casillas = self.casillas_objeto(objeto)
        #Comprueba que se cumplan los requisitos antes de continuar
        if not casillas:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return 9999
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return min(
            abs(posicion[0] - casilla[0])
            + abs(posicion[1] - casilla[1])
            for casilla in casillas
        )

    #Selecciona la casilla más apropiada para dibujar un ataque o proyectil.

    def casilla_objetivo_visual(self, objeto, origen=None):
        #Selecciona una casilla representativa para proyectiles y golpes
        casillas = self.casillas_objeto(objeto)
        #Comprueba que se cumplan los requisitos antes de continuar
        if not casillas:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return objeto.posicion
        #Comprueba que el dato necesario exista antes de continuar
        if origen is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return min(casillas)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return min(
            casillas,
            key=lambda casilla: (
                abs(origen[0] - casilla[0])
                + abs(origen[1] - casilla[1])
            )
        )

    #Indica si una casilla pertenece al área reservada para el atacante.

    def es_zona_despliegue(self, posicion):
        #El atacante solamente coloca tropas en el lado izquierdo
        fila, columna = posicion
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return self.dentro_mapa(posicion) and columna < COLUMNAS_DESPLIEGUE

    #Indica si una casilla pertenece al área donde el defensor puede construir.

    def es_zona_construccion(self, posicion):
        #El defensor construye en el lado derecho del tablero
        fila, columna = posicion
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return (
            self.dentro_mapa(posicion)
            and columna >= COLUMNA_INICIO_DEFENSA
            and posicion not in self.casillas_torre_central()
        )

    #Busca la estructura o unidad que ocupa una casilla determinada.

    def objeto_en(self, posicion, incluir_destruidos=True):
        #La torre central se puede seleccionar desde cualquiera de sus dieciséis casillas
        if posicion in self.casillas_torre_central():
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.torre_central

        #Busca estructuras y unidades en la casilla
        objetos = self.torres + self.muros + self.unidades
        #Recorre los elementos de esta colección para procesarlos uno por uno
        for objeto in objetos:
            #Comprueba que la posición sea válida y esté disponible
            if objeto.posicion != posicion:
                #Omite este elemento y continúa con la siguiente repetición
                continue

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if incluir_destruidos:
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return objeto

            #Comprueba si el objeto continúa activo dentro de la partida
            if hasattr(objeto, "esta_destruido") and objeto.esta_destruido():
                #Omite este elemento y continúa con la siguiente repetición
                continue
            #Comprueba si el objeto continúa activo dentro de la partida
            if hasattr(objeto, "esta_eliminada") and objeto.esta_eliminada():
                #Omite este elemento y continúa con la siguiente repetición
                continue
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return objeto

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return None

    #Comprueba rápidamente si una casilla ya contiene algún objeto del juego.

    def casilla_ocupada(self, posicion):
        #Comprueba si existe un objeto activo en la casilla
        return self.objeto_en(posicion, incluir_destruidos=False) is not None

    #Valida dinero, fase y posición antes de crear y colocar una torre defensiva.

    def comprar_torre(self, nombre, posicion):
        #Solo permite comprar durante construcción
        if self.fase != "construccion":
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No estás en la fase de construcción."

        #Comprueba que la posición sea válida y esté disponible
        if not self.es_zona_construccion(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Las torres deben colocarse en el lado derecho del tablero."

        #Comprueba que la posición sea válida y esté disponible
        if self.casilla_ocupada(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "La casilla ya está ocupada."

        #Crea una copia independiente del objeto seleccionado por el jugador
        torre = crear_torre(nombre, self.faccion_defensor)
        #Comprueba que el dato necesario exista antes de continuar
        if torre is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No se pudo crear la torre."

        #Comprueba que haya dinero suficiente antes de realizar la compra
        if self.dinero_defensor < torre.costo:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Dinero insuficiente."

        torre.colocar(posicion)
        self.dinero_defensor -= torre.costo
        #Agrega el elemento a la lista para conservarlo durante la partida
        self.torres.append(torre)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True, f"{nombre} colocada en {posicion}."

    #Valida dinero, fase y posición antes de crear y colocar un muro.

    def comprar_muro(self, posicion):
        #Solo permite comprar durante construcción
        if self.fase != "construccion":
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No estás en la fase de construcción."

        #Comprueba que la posición sea válida y esté disponible
        if not self.es_zona_construccion(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Los muros deben colocarse en el lado derecho del tablero."

        #Comprueba que la posición sea válida y esté disponible
        if self.casilla_ocupada(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "La casilla ya está ocupada."

        #Crea una copia independiente del objeto seleccionado por el jugador
        muro = crear_muro(self.faccion_defensor)
        #Comprueba que el dato necesario exista antes de continuar
        if muro is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No se pudo crear el muro."

        #Comprueba que haya dinero suficiente antes de realizar la compra
        if self.dinero_defensor < muro.costo:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Dinero insuficiente."

        muro.colocar(posicion)
        self.dinero_defensor -= muro.costo
        #Agrega el elemento a la lista para conservarlo durante la partida
        self.muros.append(muro)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True, f"Muro colocado en {posicion}."

    #Valida dinero, facción y posición antes de desplegar una unidad atacante.

    def comprar_unidad(self, nombre, posicion):
        #Solo permite comprar durante despliegue
        if self.fase != "despliegue":
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No estás en la fase de despliegue."

        #Comprueba que la posición sea válida y esté disponible
        if not self.es_zona_despliegue(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Las unidades deben colocarse en las cuatro columnas del lado izquierdo."

        #Comprueba que la posición sea válida y esté disponible
        if self.casilla_ocupada(posicion):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "La casilla ya está ocupada."

        #Obtiene los datos disponibles para construir esta parte de la interfaz
        faccion = obtener_faccion(self.faccion_atacante)
        #Comprueba que el dato necesario exista antes de continuar
        if faccion is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "La facción atacante no existe."

        #Crea una copia independiente del objeto seleccionado por el jugador
        unidad = faccion.crear_unidad(nombre)
        #Comprueba que el dato necesario exista antes de continuar
        if unidad is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "La unidad no pertenece a la facción atacante."

        #Comprueba que haya dinero suficiente antes de realizar la compra
        if self.dinero_atacante < unidad.costo:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Dinero insuficiente."

        #Mueve la unidad a la siguiente casilla de su recorrido
        unidad.mover(posicion)
        unidad.cambiar_animacion("idle")
        self.dinero_atacante -= unidad.costo
        #Agrega el elemento a la lista para conservarlo durante la partida
        self.unidades.append(unidad)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True, f"{nombre} desplegado en {posicion}."

    #Retira un objeto colocado durante la preparación y devuelve su costo cuando corresponde.

    def eliminar_objeto(self, posicion):
        #Permite retirar y reembolsar objetos durante las fases de preparación
        objeto = self.objeto_en(posicion)
        #Comprueba que el dato necesario exista antes de continuar
        if objeto is None or objeto is self.torre_central:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "No hay un objeto removible en esa casilla."

        #Comprueba la fase actual antes de permitir esta acción
        if self.fase == "construccion":
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if objeto in self.torres:
                self.torres.remove(objeto)
                self.dinero_defensor += objeto.costo
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return True, f"{objeto.nombre} removida y reembolsada."

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if objeto in self.muros:
                self.muros.remove(objeto)
                self.dinero_defensor += objeto.costo
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return True, "Muro removido y reembolsado."

        #Comprueba la fase actual antes de permitir esta acción
        if self.fase == "despliegue" and objeto in self.unidades:
            self.unidades.remove(objeto)
            self.dinero_atacante += objeto.costo
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return True, f"{objeto.nombre} removido y reembolsado."

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return False, "Ese objeto no puede retirarse en la fase actual."

    #Cierra la fase del defensor y habilita el despliegue de las unidades atacantes.

    def confirmar_construccion(self):
        #Exige al menos una torre para proteger la base
        if len(self.torres) == 0:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Debes colocar al menos una torre defensiva."

        #Guarda fase como parte del estado que utilizará esta clase
        self.fase = "despliegue"
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True, "Construcción confirmada. Ahora despliega las unidades."

    #Cierra la preparación del atacante y permite comenzar el combate.

    def confirmar_despliegue(self):
        #Exige al menos una unidad atacante
        if len(self.unidades) == 0:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False, "Debes desplegar al menos una unidad."

        #Guarda fase como parte del estado que utilizará esta clase
        self.fase = "combate"
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True, "Despliegue confirmado. Comienza el combate."

    #Aplica recompensas y actualiza el marcador después de finalizar una ronda.

    def registrar_resultado(self, resultado):
        #Actualiza el marcador de rondas
        if resultado.ganador == "defensor":
            self.rondas_defensor += 1
        else:
            self.rondas_atacante += 1

        #Calcula las recompensas para la siguiente ronda
        self.bono_defensor = (
            resultado.unidades_eliminadas * RECOMPENSA_POR_UNIDAD
        )
        #Guarda bono atacante como parte del estado que utilizará esta clase
        self.bono_atacante = (
            int(resultado.daño_a_estructuras // 10)
            + int(resultado.daño_a_base // 10)
            + resultado.estructuras_destruidas * RECOMPENSA_POR_DESTRUCCION
        )

        #Guarda fase como parte del estado que utilizará esta clase
        self.fase = "fin_ronda"

    #Comprueba si alguno de los jugadores alcanzó las victorias necesarias.

    def ganador_partida(self):
        #Comprueba si alguno de los jugadores llegó a tres rondas
        if self.rondas_defensor >= RONDAS_PARA_GANAR:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return "defensor"
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if self.rondas_atacante >= RONDAS_PARA_GANAR:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return "atacante"
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return None

    #Guarda en jugadores.json la victoria del ganador según su rol.

    def guardar_victoria_final(self, rol):
        #Guarda una victoria persistente en jugadores.json
        if rol == "defensor":
            usuario = self.datos_defensor["nombre"]
        else:
            usuario = self.datos_atacante["nombre"]

        #Guarda la victoria del jugador en el archivo de estadísticas
        self.gestion.sumar_victorias(usuario, rol)


#Motor responsable de ejecutar un turno completo de combate automático.
#Administra caminos, ataques de torres, movimiento de unidades y condiciones de victoria.

class MotorCombate:
    #Recibe el estado compartido y prepara contadores y eventos de combate.

    def __init__(self, estado):
        #Guarda el estado compartido de la partida
        self.estado = estado
        #Guarda turno como parte del estado que utilizará esta clase
        self.turno = 0
        #Guarda eventos como parte del estado que utilizará esta clase
        self.eventos = []
        #Guarda logs turno como parte del estado que utilizará esta clase
        self.logs_turno = []

        #Guarda estadísticas acumuladas
        self.unidades_eliminadas = 0
        #Guarda daño a estructuras como parte del estado que utilizará esta clase
        self.daño_a_estructuras = 0
        #Guarda estructuras destruidas como parte del estado que utilizará esta clase
        self.estructuras_destruidas = 0
        #Guarda daño a base como parte del estado que utilizará esta clase
        self.daño_a_base = 0

        #Evita contar dos veces una misma destrucción
        self.unidades_contadas = set()
        #Guarda estructuras contadas como parte del estado que utilizará esta clase
        self.estructuras_contadas = set()

    #Calcula la distancia Manhattan entre dos casillas del tablero.

    def distancia(self, origen, destino):
        #Calcula distancia Manhattan entre dos casillas
        return abs(origen[0] - destino[0]) + abs(origen[1] - destino[1])

    #Obtiene las casillas adyacentes válidas para el movimiento por el mapa.

    def vecinos(self, posicion):
        #Genera las cuatro casillas vecinas dentro del mapa
        fila, columna = posicion
        opciones = (
            (fila - 1, columna),
            (fila + 1, columna),
            (fila, columna - 1),
            (fila, columna + 1)
        )
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return [p for p in opciones if self.estado.dentro_mapa(p)]

    #Construye el conjunto de casillas que no pueden atravesarse durante la búsqueda de caminos.

    def posiciones_bloqueadas(self, ignorar_unidad=None):
        #Las estructuras y las otras unidades bloquean el movimiento
        bloqueadas = set()

        #Recorre las estructuras colocadas para procesar su estado
        for estructura in self.estado.torres + self.estado.muros:
            #Comprueba si el objeto continúa activo dentro de la partida
            if not estructura.esta_destruido():
                #Agrega el elemento al conjunto para evitar duplicados
                bloqueadas.add(estructura.posicion)

        #La torre central bloquea las dieciséis casillas que ocupa
        if not self.estado.torre_central.esta_destruido():
            bloqueadas.update(self.estado.casillas_torre_central())

        #Recorre las unidades para actualizar su comportamiento en el turno
        for unidad in self.estado.unidades:
            #Comprueba si el objeto continúa activo dentro de la partida
            if unidad is ignorar_unidad or unidad.esta_eliminada():
                #Omite este elemento y continúa con la siguiente repetición
                continue
            #Agrega el elemento al conjunto para evitar duplicados
            bloqueadas.add(unidad.posicion)

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return bloqueadas

    #Busca el camino más corto hacia una de las metas mediante búsqueda en anchura.

    def buscar_camino(self, inicio, metas, bloqueadas):
        #Busca el camino más corto con una exploración en anchura
        metas = set(metas)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if inicio in metas:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return [inicio]

        cola = deque([inicio])
        anterior = {inicio: None}
        encontrada = None

        #Repite el proceso mientras la condición de este ciclo siga activa
        while cola:
            actual = cola.popleft()
            #Recorre los elementos de esta colección para procesarlos uno por uno
            for vecino in self.vecinos(actual):
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if vecino in anterior:
                    #Omite este elemento y continúa con la siguiente repetición
                    continue
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if vecino in bloqueadas and vecino not in metas:
                    #Omite este elemento y continúa con la siguiente repetición
                    continue

                anterior[vecino] = actual
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if vecino in metas:
                    encontrada = vecino
                    #Limpia los datos anteriores antes de preparar el nuevo estado
                    cola.clear()
                    #Finaliza el ciclo porque ya se obtuvo el resultado necesario
                    break
                #Agrega el elemento a la lista para conservarlo durante la partida
                cola.append(vecino)

        #Comprueba que el dato necesario exista antes de continuar
        if encontrada is None:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return []

        camino = []
        actual = encontrada
        #Repite el proceso mientras la condición de este ciclo siga activa
        while actual is not None:
            #Agrega el elemento a la lista para conservarlo durante la partida
            camino.append(actual)
            actual = anterior[actual]
        camino.reverse()
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return camino

    #Retorna solamente las estructuras defensivas que todavía conservan vida.

    def estructuras_vivas(self):
        #Retorna todas las estructuras que todavía pueden recibir daño
        estructuras = [
            e for e in self.estado.torres + self.estado.muros
            if not e.esta_destruido()
        ]
        #Comprueba si el objeto continúa activo dentro de la partida
        if not self.estado.torre_central.esta_destruido():
            #Agrega el elemento a la lista para conservarlo durante la partida
            estructuras.append(self.estado.torre_central)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return estructuras

    #Retorna solamente las unidades atacantes que todavía pueden participar.

    def unidades_vivas(self):
        #Retorna las unidades que todavía tienen vida
        return [
            u for u in self.estado.unidades
            if not u.esta_eliminada()
        ]

    #Localiza estructuras que una unidad puede atacar desde su posición actual.

    def objetivos_adyacentes(self, unidad):
        #Busca estructuras enemigas a una casilla de distancia
        objetivos = []
        #Recorre las estructuras colocadas para procesar su estado
        for estructura in self.estructuras_vivas():
            #Comprueba que la posición sea válida y esté disponible
            if self.estado.distancia_a_objeto(unidad.posicion, estructura) == 1:
                #Agrega el elemento a la lista para conservarlo durante la partida
                objetivos.append(estructura)

        #Prioriza la torre central, después torres y finalmente muros
        objetivos.sort(
            key=lambda e: (
                0 if e is self.estado.torre_central else 1 if isinstance(e, Torre) else 2,
                e.vida
            )
        )
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return objetivos

    #Actualiza estadísticas y eventos cuando una estructura recibe daño.

    def registrar_daño_estructura(self, estructura, vida_anterior):
        #Calcula el daño real causado sin contar valores negativos
        daño = max(0, vida_anterior - estructura.vida)

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if estructura is self.estado.torre_central:
            self.daño_a_base += int(daño)
        else:
            self.daño_a_estructuras += int(daño)

        #Cuenta una destrucción solamente una vez
        if estructura.esta_destruido() and id(estructura) not in self.estructuras_contadas:
            #Agrega el elemento al conjunto para evitar duplicados
            self.estructuras_contadas.add(id(estructura))
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if estructura is not self.estado.torre_central:
                self.estructuras_destruidas += 1

    #Registra la eliminación de una unidad sin duplicar el evento.

    def registrar_muerte_unidad(self, unidad):
        #Cuenta una unidad eliminada solamente una vez
        if unidad.esta_eliminada() and id(unidad) not in self.unidades_contadas:
            #Agrega el elemento al conjunto para evitar duplicados
            self.unidades_contadas.add(id(unidad))
            self.unidades_eliminadas += 1
            #Agrega el elemento a la lista para conservarlo durante la partida
            self.logs_turno.append(f"{unidad.nombre} fue eliminado.")

    #Ejecuta los ataques de todas las torres contra objetivos dentro de su alcance.

    def turno_torres(self):
        #Cada torre ataca a la unidad más cercana dentro de su alcance
        for torre in self.estado.torres:
            #Comprueba si el objeto continúa activo dentro de la partida
            if torre.esta_destruido():
                #Omite este elemento y continúa con la siguiente repetición
                continue

            #Actualiza las recargas y efectos temporales para el siguiente turno
            torre.avanzar_turno()

            #Repite el proceso mientras la condición de este ciclo siga activa
            while torre.ataques_restantes > 0:
                objetivos = [
                    unidad for unidad in self.unidades_vivas()
                    if self.distancia(torre.posicion, unidad.posicion) <= torre.alcance
                ]

                #Comprueba que se cumplan los requisitos antes de continuar
                if not objetivos:
                    #Finaliza el ciclo porque ya se obtuvo el resultado necesario
                    break

                objetivos.sort(
                    key=lambda unidad: (
                        self.distancia(torre.posicion, unidad.posicion),
                        unidad.vida
                    )
                )
                objetivo = objetivos[0]
                vida_anterior = objetivo.vida

                #Usa la habilidad cuando está disponible
                if torre.turnos_recarga == 0:
                    atacó = torre.usar_habilidad(objetivo)
                    #Evalúa esta condición para decidir qué acción debe ejecutarse
                    if atacó:
                        torre.ataques_restantes -= 1
                    else:
                        atacó = torre.atacar(objetivo)
                else:
                    atacó = torre.atacar(objetivo)

                #Comprueba que se cumplan los requisitos antes de continuar
                if not atacó:
                    #Finaliza el ciclo porque ya se obtuvo el resultado necesario
                    break

                daño = max(0, vida_anterior - objetivo.vida)
                #Agrega el elemento a la lista para conservarlo durante la partida
                self.logs_turno.append(
                    f"{torre.nombre} causó {int(daño)} de daño a {objetivo.nombre}."
                )
                #Agrega el elemento a la lista para conservarlo durante la partida
                self.eventos.append({
                    "tipo": "proyectil",
                    "origen": torre.posicion,
                    "destino": objetivo.posicion,
                    "sprite": torre.sprite_proyectil
                })
                self.registrar_muerte_unidad(objetivo)

    #Activa habilidades defensivas o de apoyo de una unidad cuando están disponibles.

    def usar_habilidad_pasiva(self, unidad):
        #Activa habilidades defensivas o de movimiento cuando conviene
        if not unidad.habilidad_disponible():
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if unidad.tipo_habilidad in ("escudo", "intangibilidad", "velocidad"):
            unidad.usar_habilidad()
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        elif unidad.tipo_habilidad in ("curacion", "regeneracion"):
            #Comprueba si el objeto continúa activo dentro de la partida
            if unidad.vida < unidad.vida_maxima * 0.75:
                unidad.usar_habilidad()

    #Hace que una unidad ataque una estructura y aplica su habilidad cuando corresponde.

    def atacar_estructura(self, unidad, estructura):
        #Guarda la vida anterior para calcular estadísticas
        vida_anterior = estructura.vida
        atacó = False

        #Usa habilidades ofensivas cuando están disponibles
        if unidad.habilidad_disponible():
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if unidad.tipo_habilidad in ("ataque_doble", "daño_edificios"):
                atacó = unidad.usar_habilidad(estructura)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            elif unidad.tipo_habilidad == "daño_area":
                objetivos = self.objetivos_adyacentes(unidad)
                atacó = unidad.usar_habilidad(objetivos)

                #Registra el daño causado a cada estructura del área
                for objetivo in objetivos:
                    #Evalúa esta condición para decidir qué acción debe ejecutarse
                    if objetivo is estructura:
                        #Omite este elemento y continúa con la siguiente repetición
                        continue
                    #El daño de área ya ocurrió; se aproxima con el daño base
                    if objetivo is self.estado.torre_central:
                        self.daño_a_base += int(unidad.daño)
                    else:
                        self.daño_a_estructuras += int(unidad.daño)
                    #Comprueba si el objeto continúa activo dentro de la partida
                    if objetivo.esta_destruido() and id(objetivo) not in self.estructuras_contadas:
                        #Agrega el elemento al conjunto para evitar duplicados
                        self.estructuras_contadas.add(id(objetivo))
                        #Evalúa esta condición para decidir qué acción debe ejecutarse
                        if objetivo is not self.estado.torre_central:
                            self.estructuras_destruidas += 1

        #Comprueba que se cumplan los requisitos antes de continuar
        if not atacó:
            atacó = unidad.atacar(estructura)

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if atacó:
            self.registrar_daño_estructura(estructura, vida_anterior)
            daño = max(0, vida_anterior - estructura.vida)
            #Agrega el elemento a la lista para conservarlo durante la partida
            self.logs_turno.append(
                f"{unidad.nombre} causó {int(daño)} de daño a {estructura.nombre}."
            )
            #Agrega el elemento a la lista para conservarlo durante la partida
            self.eventos.append({
                "tipo": "golpe",
                "origen": unidad.posicion,
                "destino": self.estado.casilla_objetivo_visual(
                    estructura,
                    unidad.posicion
                )
            })
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return atacó

    #Calcula casillas libres desde las que una unidad puede atacar una estructura.

    def metas_adyacentes(self, estructura, bloqueadas):
        #Obtiene casillas libres alrededor de toda la estructura
        casillas_estructura = self.estado.casillas_objeto(estructura)
        metas = set()

        #Recorre los elementos de esta colección para procesarlos uno por uno
        for casilla in casillas_estructura:
            #Recorre los elementos de esta colección para procesarlos uno por uno
            for posicion in self.vecinos(casilla):
                #Comprueba que la posición sea válida y esté disponible
                if posicion in casillas_estructura:
                    #Omite este elemento y continúa con la siguiente repetición
                    continue
                #Comprueba que la posición sea válida y esté disponible
                if posicion not in bloqueadas:
                    #Agrega el elemento al conjunto para evitar duplicados
                    metas.add(posicion)

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return list(metas)

    #Selecciona el objetivo prioritario y calcula una ruta válida para alcanzarlo.

    def camino_hacia_objetivo(self, unidad):
        #Primero intenta llegar a la torre central
        bloqueadas = self.posiciones_bloqueadas(ignorar_unidad=unidad)
        metas_base = self.metas_adyacentes(self.estado.torre_central, bloqueadas)
        camino = self.buscar_camino(unidad.posicion, metas_base, bloqueadas)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if camino:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return camino

        #Si la base está cerrada, busca la estructura alcanzable más cercana
        mejor_camino = []
        #Recorre las estructuras colocadas para procesar su estado
        for estructura in self.estructuras_vivas():
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if estructura is self.estado.torre_central:
                #Omite este elemento y continúa con la siguiente repetición
                continue

            metas = self.metas_adyacentes(estructura, bloqueadas)
            candidato = self.buscar_camino(unidad.posicion, metas, bloqueadas)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if candidato and (not mejor_camino or len(candidato) < len(mejor_camino)):
                mejor_camino = candidato

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return mejor_camino

    #Avanza una unidad según su capacidad de movimiento y el camino calculado.

    def mover_unidad(self, unidad):
        #Busca un camino y mueve la unidad según su velocidad
        camino = self.camino_hacia_objetivo(unidad)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if len(camino) <= 1:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return False

        pasos = min(unidad.obtener_movimiento_actual(), len(camino) - 1)
        origen = unidad.posicion
        destino = camino[pasos]
        #Mueve la unidad a la siguiente casilla de su recorrido
        unidad.mover(destino)

        #Agrega el elemento a la lista para conservarlo durante la partida
        self.logs_turno.append(
            f"{unidad.nombre} avanzó de {origen} a {destino}."
        )
        #Agrega el elemento a la lista para conservarlo durante la partida
        self.eventos.append({
            "tipo": "movimiento",
            "origen": origen,
            "destino": destino
        })
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return True

    #Ejecuta las acciones de todas las unidades atacantes durante el turno.

    def turno_unidades(self):
        #Cada unidad usa su habilidad, se mueve y ataca si está cerca
        for unidad in list(self.unidades_vivas()):
            #Actualiza las recargas y efectos temporales para el siguiente turno
            unidad.avanzar_turno()
            unidad.cambiar_animacion("idle")

            #Comprueba que se cumplan los requisitos antes de continuar
            if not unidad.puede_actuar():
                #Omite este elemento y continúa con la siguiente repetición
                continue

            self.usar_habilidad_pasiva(unidad)
            objetivos = self.objetivos_adyacentes(unidad)

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if objetivos:
                self.atacar_estructura(unidad, objetivos[0])
                #Comprueba si el objeto continúa activo dentro de la partida
                if self.estado.torre_central.esta_destruido():
                    #Finaliza el método y devuelve el control al punto anterior
                    return
                #Omite este elemento y continúa con la siguiente repetición
                continue

            self.mover_unidad(unidad)
            objetivos = self.objetivos_adyacentes(unidad)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if objetivos:
                self.atacar_estructura(unidad, objetivos[0])
                #Comprueba si el objeto continúa activo dentro de la partida
                if self.estado.torre_central.esta_destruido():
                    #Finaliza el método y devuelve el control al punto anterior
                    return

    #Procesa un ciclo completo: torres, unidades, estados y condición de finalización.

    def ejecutar_turno(self):
        #Limpia los eventos visuales del turno anterior
        self.turno += 1
        #Guarda eventos como parte del estado que utilizará esta clase
        self.eventos = []
        #Guarda logs turno como parte del estado que utilizará esta clase
        self.logs_turno = [f"Turno de combate {self.turno}."]

        #Las defensas actúan primero
        self.turno_torres()
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if len(self.unidades_vivas()) == 0:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.crear_resultado("defensor")

        #Después actúan las unidades atacantes
        self.turno_unidades()
        #Comprueba si el objeto continúa activo dentro de la partida
        if self.estado.torre_central.esta_destruido():
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.crear_resultado("atacante")

        #El defensor gana si se alcanza el límite de turnos
        if self.turno >= MAX_TURNOS_COMBATE:
            #Agrega el elemento a la lista para conservarlo durante la partida
            self.logs_turno.append("Se agotó el tiempo de combate.")
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return self.crear_resultado("defensor")

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return None

    #Construye el resumen final del combate con todas sus estadísticas acumuladas.

    def crear_resultado(self, ganador):
        #Construye el resumen final del combate
        return ResultadoCombate(
            ganador=ganador,
            turnos=self.turno,
            unidades_eliminadas=self.unidades_eliminadas,
            daño_a_estructuras=self.daño_a_estructuras,
            estructuras_destruidas=self.estructuras_destruidas,
            daño_a_base=self.daño_a_base,
            base_destruida=self.estado.torre_central.esta_destruido(),
            eventos=self.eventos.copy()
        )


#Ventana raíz de Tkinter y punto central de navegación entre pantallas.
#También conserva los datos compartidos de jugadores, música, sprites y gestión de cuentas.

class Aplicacion(tk.Tk):
    #Configura la ventana principal, los servicios globales y los datos temporales de jugadores.

    def __init__(self):
        super().__init__()

        #Configura la ventana principal
        self.title("Castle Flesh - Defensa y Asalto de Base")
        #Actualiza la configuración de la ventana o del componente
        self.configure(bg=BG)
        self.minsize(1280, 760)

        #Gestion usa el archivo jugadores.json ubicado junto al programa
        self.gestion = Gestion(str(BASE_DIR / "jugadores.json"))
        #Guarda jugador 1 como parte del estado que utilizará esta clase
        self.jugador_1 = {}
        #Guarda jugador 2 como parte del estado que utilizará esta clase
        self.jugador_2 = {}
        #Guarda pantalla actual como parte del estado que utilizará esta clase
        self.pantalla_actual = None

        #Controla la música de todas las pantallas
        self.gestor_musica = GestorMusica()
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

        #Abre o actualiza la pantalla correspondiente a esta acción
        self.mostrar_menu()

        #Intenta reproducir automáticamente la música incluida en el proyecto
        self.after(350, self.iniciar_musica_automatica)

    #Solicita al gestor de música que reproduzca una canción al iniciar el programa.

    def iniciar_musica_automatica(self):
        #Inicia la música sin abrir una ventana de selección de archivos
        _, mensaje = self.gestor_musica.iniciar_automaticamente()

        #Sincroniza el botón de música de la pantalla que esté abierta
        if hasattr(self.pantalla_actual, "actualizar_boton_musica"):
            #Actualiza los datos visibles después de este cambio
            self.pantalla_actual.actualizar_boton_musica()

        #Muestra el resultado en consola sin interrumpir al usuario
        print(f"[Música] {mensaje}")

    #Cierra correctamente música, ventanas y recursos de la aplicación.

    def cerrar_aplicacion(self):
        #Detiene la música antes de cerrar la ventana
        self.gestor_musica.cerrar()
        #Cierra esta ventana o elimina el componente actual
        self.destroy()

    #Elimina la pantalla actual antes de mostrar una nueva.

    def limpiar(self):
        #Elimina la pantalla anterior antes de abrir otra
        if self.pantalla_actual is not None:
            #Cierra esta ventana o elimina el componente actual
            self.pantalla_actual.destroy()
        #Guarda pantalla actual como parte del estado que utilizará esta clase
        self.pantalla_actual = None

    #Sustituye la vista activa por un nuevo Frame de Tkinter.

    def usar_pantalla(self, frame):
        #Coloca un frame como pantalla principal
        self.limpiar()
        #Guarda pantalla actual como parte del estado que utilizará esta clase
        self.pantalla_actual = frame
        #Coloca el componente dentro de la ventana con el administrador pack
        frame.pack(fill="both", expand=True)

    #Navega hacia el menú principal.

    def mostrar_menu(self):
        #Abre el menú principal
        self.geometry("900x650")
        self.usar_pantalla(PantallaMenu(self))

    #Navega hacia el proceso de inicio de sesión de dos jugadores.

    def mostrar_login(self):
        #Reinicia los jugadores temporales y abre el login dual
        self.jugador_1 = {}
        #Guarda jugador 2 como parte del estado que utilizará esta clase
        self.jugador_2 = {}
        self.geometry("900x700")
        self.usar_pantalla(PantallaLogin(self))

    #Navega hacia la selección de facciones.

    def mostrar_facciones(self):
        #Abre la selección de facciones
        self.geometry("1050x720")
        self.usar_pantalla(PantallaFacciones(self))

    #Crea la pantalla de juego después de validar jugadores y facciones.

    def mostrar_juego(self):
        #Abre la partida utilizando el espacio disponible sin ocultar los controles
        ancho = min(1680, max(1280, self.winfo_screenwidth() - 30))
        alto = min(980, max(780, self.winfo_screenheight() - 60))
        self.state("normal")
        self.geometry(f"{ancho}x{alto}+10+10")
        self.usar_pantalla(PantallaJuego(self))

    #Navega hacia la clasificación de jugadores.

    def mostrar_ranking(self):
        #Abre el top cinco de jugadores
        self.geometry("900x650")
        self.usar_pantalla(PantallaRanking(self))


#Pantalla inicial del programa.
#Presenta el título, los accesos principales y el control de música.

class PantallaMenu(tk.Frame):
    #Construye el menú principal dentro de la ventana raíz.

    def __init__(self, app):
        #Inicializa la pantalla principal del juego
        super().__init__(app, bg=BG)
        #Guarda app como parte del estado que utilizará esta clase
        self.app = app
        #Guarda boton musica como parte del estado que utilizará esta clase
        self.boton_musica = None
        self.construir()

    #Crea y distribuye todos los componentes visuales de esta pantalla.

    def construir(self):
        #Crea un marco principal para mantener todos los elementos centrados
        contenido = tk.Frame(self, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        contenido.pack(fill="both", expand=True)

        #Coloca el control de música en la esquina superior derecha
        self.boton_musica = tk.Button(
            contenido,
            command=self.alternar_musica,
            width=19,
            pady=8,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold")
        )
        #Ubica el componente en una posición específica de la ventana
        self.boton_musica.place(relx=0.975, rely=0.035, anchor="ne")
        #Actualiza los datos visibles después de este cambio
        self.actualizar_boton_musica()

        #Ubica el título cerca de la parte superior de la pantalla
        bloque_titulo = tk.Frame(contenido, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        bloque_titulo.pack(pady=(72, 0))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_titulo,
            text="CASTLE FLESH",
            bg=BG,
            fg=DORADO,
            font=("Georgia", 54, "bold")
        ).pack(pady=(0, 8))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_titulo,
            text="Defensa y Asalto de Base",
            bg=BG,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 16)
        ).pack()

        #Agrupa los botones justo debajo del título
        marco_botones = tk.Frame(contenido, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        marco_botones.pack(pady=(38, 0))

        #Coloca el componente dentro de la ventana con el administrador pack
        self.boton(
            marco_botones,
            "NUEVA PARTIDA",
            self.app.mostrar_login,
            DORADO
        ).pack(pady=8)

        #Coloca el componente dentro de la ventana con el administrador pack
        self.boton(
            marco_botones,
            "TOP JUGADORES",
            self.app.mostrar_ranking,
            AZUL
        ).pack(pady=8)

        #Coloca el componente dentro de la ventana con el administrador pack
        self.boton(
            marco_botones,
            "SALIR",
            self.app.cerrar_aplicacion,
            ROJO
        ).pack(pady=8)

    #Crea un botón reutilizable con el estilo visual del menú.

    def boton(self, parent, texto, comando, color):
        #Crea un botón grande y uniforme para el menú principal
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            width=25,
            pady=12,
            bg=BG_PANEL,
            fg=color,
            activebackground=color,
            activeforeground="#001219",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 14, "bold"),
            highlightthickness=1,
            highlightbackground=BORDE
        )

    #Sincroniza el texto y los colores del botón con el estado real de la música.

    def actualizar_boton_musica(self):
        #Actualiza el botón para indicar si la música está activa o pausada
        if self.boton_musica is None:
            #Finaliza el método y devuelve el control al punto anterior
            return

        texto, fondo, color_texto = self.app.gestor_musica.estilo_boton()
        #Actualiza la apariencia o el estado actual del componente
        self.boton_musica.config(
            text=texto,
            bg=fondo,
            fg=color_texto,
            activebackground=VERDE,
            activeforeground="#001B1A"
        )

    #Pausa, reanuda o selecciona música y actualiza el botón correspondiente.

    def alternar_musica(self):
        #Inicia, pausa o reanuda la música desde el menú principal
        _, mensaje = self.app.gestor_musica.alternar(self)
        #Actualiza los datos visibles después de este cambio
        self.actualizar_boton_musica()

        #Muestra una advertencia solamente cuando pygame no está instalado
        if "Pygame no está instalado" in mensaje:
            messagebox.showwarning("Música", mensaje)


#Pantalla utilizada para autenticar o registrar a los dos jugadores.
#El proceso se realiza primero para el defensor y luego para el atacante.

class PantallaLogin(tk.Frame):
    #Prepara el formulario para autenticar al jugador correspondiente.

    def __init__(self, app):
        super().__init__(app, bg=BG)
        #Guarda app como parte del estado que utilizará esta clase
        self.app = app
        #Guarda numero jugador como parte del estado que utilizará esta clase
        self.numero_jugador = 1
        #Guarda modo como parte del estado que utilizará esta clase
        self.modo = "login"
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.mensaje = tk.StringVar()
        self.construir()

    #Crea y distribuye todos los componentes visuales de esta pantalla.

    def construir(self):
        #Limpia el formulario antes de reconstruirlo
        for widget in self.winfo_children():
            #Cierra esta ventana o elimina el componente actual
            widget.destroy()

        color = DORADO if self.numero_jugador == 1 else COLOR_FACCION["No muerto"]

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            self,
            text=f"JUGADOR {self.numero_jugador}",
            bg=BG,
            fg=color,
            font=("Georgia", 30, "bold")
        ).pack(pady=(35, 6))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            self,
            text="Inicia sesión o crea una cuenta",
            bg=BG,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 12)
        ).pack()

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        panel = tk.Frame(self, bg=BG_PANEL, padx=35, pady=28)
        #Coloca el componente dentro de la ventana con el administrador pack
        panel.pack(pady=25, ipadx=15, ipady=5)

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        pestañas = tk.Frame(panel, bg=BG_PANEL)
        #Coloca el componente dentro de la ventana con el administrador pack
        pestañas.pack(fill="x", pady=(0, 20))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            pestañas,
            text="Iniciar sesión",
            command=lambda: self.cambiar_modo("login"),
            bg=color if self.modo == "login" else BG_INPUT,
            fg="#000000" if self.modo == "login" else TEXTO,
            relief="flat",
            pady=8,
            width=16
        ).pack(side="left", padx=3)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            pestañas,
            text="Registrarse",
            command=lambda: self.cambiar_modo("registro"),
            bg=color if self.modo == "registro" else BG_INPUT,
            fg="#000000" if self.modo == "registro" else TEXTO,
            relief="flat",
            pady=8,
            width=16
        ).pack(side="left", padx=3)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(panel, text="Usuario", bg=BG_PANEL, fg=TEXTO).pack(anchor="w")
        #Crea el campo donde el jugador escribirá la información solicitada
        self.entrada_usuario = tk.Entry(
            panel,
            width=32,
            bg=BG_INPUT,
            fg=TEXTO,
            insertbackground=TEXTO,
            relief="flat",
            font=("Segoe UI", 12)
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.entrada_usuario.pack(ipady=7, pady=(4, 14))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(panel, text="Contraseña", bg=BG_PANEL, fg=TEXTO).pack(anchor="w")
        #Crea el campo donde el jugador escribirá la información solicitada
        self.entrada_clave = tk.Entry(
            panel,
            width=32,
            show="*",
            bg=BG_INPUT,
            fg=TEXTO,
            insertbackground=TEXTO,
            relief="flat",
            font=("Segoe UI", 12)
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.entrada_clave.pack(ipady=7, pady=(4, 14))

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if self.modo == "registro":
            #Coloca el componente dentro de la ventana con el administrador pack
            tk.Label(panel, text="Confirmar contraseña", bg=BG_PANEL, fg=TEXTO).pack(anchor="w")
            #Crea el campo donde el jugador escribirá la información solicitada
            self.entrada_confirmacion = tk.Entry(
                panel,
                width=32,
                show="*",
                bg=BG_INPUT,
                fg=TEXTO,
                insertbackground=TEXTO,
                relief="flat",
                font=("Segoe UI", 12)
            )
            #Coloca el componente dentro de la ventana con el administrador pack
            self.entrada_confirmacion.pack(ipady=7, pady=(4, 14))

        texto_boton = "ENTRAR" if self.modo == "login" else "CREAR CUENTA"
        comando = self.iniciar_sesion if self.modo == "login" else self.registrar

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            panel,
            text=texto_boton,
            command=comando,
            bg=color,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            pady=10,
            width=25,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(7, 8))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            panel,
            textvariable=self.mensaje,
            bg=BG_PANEL,
            fg=ROJO,
            wraplength=360,
            font=("Segoe UI", 10)
        ).pack()

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            self,
            text="Volver al menú",
            command=self.app.mostrar_menu,
            bg=BG,
            fg=TEXTO_SUAVE,
            relief="flat",
            cursor="hand2"
        ).pack()

    #Alterna el formulario entre inicio de sesión y registro.

    def cambiar_modo(self, modo):
        #Cambia entre inicio de sesión y registro
        self.modo = modo
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.mensaje.set("")
        self.construir()

    #Valida las credenciales escritas y continúa cuando la cuenta existe.

    def iniciar_sesion(self):
        #Valida los datos con Gestion
        usuario = self.entrada_usuario.get().strip()
        clave = self.entrada_clave.get()

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if not usuario or not clave:
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("Completa todos los campos.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Comprueba que se cumplan los requisitos antes de continuar
        if not self.app.gestion.iniciar_sesion(usuario, clave):
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("Usuario o contraseña incorrectos.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        self.guardar_jugador(usuario)

    #Valida los campos y crea una nueva cuenta de jugador.

    def registrar(self):
        #Registra un usuario nuevo y lo utiliza en la partida
        usuario = self.entrada_usuario.get().strip()
        clave = self.entrada_clave.get()
        confirmacion = self.entrada_confirmacion.get()

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if len(usuario) < 3:
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("El usuario debe tener al menos 3 caracteres.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if len(clave) < 4:
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("La contraseña debe tener al menos 4 caracteres.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if clave != confirmacion:
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("Las contraseñas no coinciden.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Comprueba que se cumplan los requisitos antes de continuar
        if not self.app.gestion.registrar_usuario(usuario, clave):
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("El usuario ya existe o los datos no son válidos.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        self.guardar_jugador(usuario)

    #Guarda temporalmente los datos del jugador autenticado y avanza al siguiente paso.

    def guardar_jugador(self, usuario):
        #Impide usar la misma cuenta para los dos jugadores
        if self.numero_jugador == 2 and usuario == self.app.jugador_1.get("nombre"):
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("El jugador 2 debe usar una cuenta distinta.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        info = self.app.gestion.info_jugador(usuario) or {}
        datos = {
            "nombre": usuario,
            "faccion": None,
            "victorias_defensor": info.get("victorias_defensor", 0),
            "victorias_atacante": info.get("victorias_atacante", 0)
        }

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if self.numero_jugador == 1:
            self.app.jugador_1 = datos
            #Guarda numero jugador como parte del estado que utilizará esta clase
            self.numero_jugador = 2
            #Guarda modo como parte del estado que utilizará esta clase
            self.modo = "login"
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.mensaje.set("")
            self.construir()
        else:
            self.app.jugador_2 = datos
            #Abre o actualiza la pantalla correspondiente a esta acción
            self.app.mostrar_facciones()


#Pantalla donde ambos jugadores seleccionan una facción.
#Impide que defensor y atacante utilicen la misma facción.

class PantallaFacciones(tk.Frame):
    #Prepara las variables que almacenan las facciones elegidas.

    def __init__(self, app):
        super().__init__(app, bg=BG)
        #Guarda app como parte del estado que utilizará esta clase
        self.app = app
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_defensor = tk.StringVar(value="")
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_atacante = tk.StringVar(value="")
        self.construir()

    #Crea y distribuye todos los componentes visuales de esta pantalla.

    def construir(self):
        #Crea la selección de facciones para los dos roles
        tk.Label(
            self,
            text="SELECCIÓN DE FACCIONES",
            bg=BG,
            fg=DORADO,
            font=("Georgia", 30, "bold")
        ).pack(pady=(28, 8))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            self,
            text="El defensor y el atacante deben utilizar facciones diferentes.",
            bg=BG,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 12)
        ).pack()

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        contenido = tk.Frame(self, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        contenido.pack(fill="both", expand=True, padx=35, pady=25)
        contenido.columnconfigure((0, 1), weight=1)

        self.crear_columna(
            contenido,
            0,
            "DEFENSOR",
            self.app.jugador_1["nombre"],
            self.var_defensor,
            DORADO
        )
        self.crear_columna(
            contenido,
            1,
            "ATACANTE",
            self.app.jugador_2["nombre"],
            self.var_atacante,
            COLOR_FACCION["No muerto"]
        )

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            self,
            text="COMENZAR PARTIDA",
            command=self.confirmar,
            bg=DORADO,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            pady=12,
            width=25,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(0, 28))

    #Construye la tarjeta de selección de facción para uno de los jugadores.

    def crear_columna(self, parent, columna, rol, usuario, variable, color):
        #Crea una tarjeta con las tres facciones
        marco = tk.Frame(parent, bg=BG_PANEL, padx=25, pady=20)
        #Coloca el componente en la fila y columna indicadas de la interfaz
        marco.grid(row=0, column=columna, padx=14, sticky="nsew")

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            marco,
            text=rol,
            bg=BG_PANEL,
            fg=color,
            font=("Segoe UI", 17, "bold")
        ).pack()
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            marco,
            text=usuario,
            bg=BG_PANEL,
            fg=TEXTO,
            font=("Segoe UI", 13)
        ).pack(pady=(0, 18))

        #Recorre los elementos de esta colección para procesarlos uno por uno
        for faccion in listar_facciones():
            #Obtiene los datos disponibles para construir esta parte de la interfaz
            datos = obtener_faccion(faccion)
            tarjeta = tk.Radiobutton(
                marco,
                text=(
                    f"{ICONO_FACCION[faccion]}  {faccion}\n"
                    f"{', '.join(datos.listar_unidades())}"
                ),
                variable=variable,
                value=faccion,
                indicatoron=False,
                justify="left",
                anchor="w",
                width=32,
                padx=14,
                pady=12,
                bg=BG_INPUT,
                fg=COLOR_FACCION[faccion],
                selectcolor=BORDE,
                activebackground=BORDE,
                activeforeground=TEXTO,
                relief="flat",
                cursor="hand2",
                font=("Segoe UI", 11, "bold")
            )
            #Coloca el componente dentro de la ventana con el administrador pack
            tarjeta.pack(fill="x", pady=5)

    #Valida las facciones elegidas y abre la partida.

    def confirmar(self):
        #Valida que ambos jugadores elijan facciones diferentes
        defensor = self.var_defensor.get()
        atacante = self.var_atacante.get()

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if not defensor or not atacante:
            messagebox.showwarning("Facciones", "Ambos jugadores deben elegir una facción.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if defensor == atacante:
            messagebox.showwarning("Facciones", "Las facciones deben ser diferentes.")
            #Finaliza el método y devuelve el control al punto anterior
            return

        self.app.jugador_1["faccion"] = defensor
        self.app.jugador_2["faccion"] = atacante
        #Abre o actualiza la pantalla correspondiente a esta acción
        self.app.mostrar_juego()


#Pantalla de clasificación que muestra los cinco mejores jugadores por rol.
#Los datos provienen del archivo jugadores.json mediante la clase Gestion.

class PantallaRanking(tk.Frame):
    #Solicita los rankings y crea la pantalla de clasificación.

    def __init__(self, app):
        super().__init__(app, bg=BG)
        #Guarda app como parte del estado que utilizará esta clase
        self.app = app
        self.construir()

    #Crea y distribuye todos los componentes visuales de esta pantalla.

    def construir(self):
        #Muestra los cinco mejores jugadores de cada rol
        tk.Label(
            self,
            text="TOP JUGADORES",
            bg=BG,
            fg=DORADO,
            font=("Georgia", 34, "bold")
        ).pack(pady=(35, 25))

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        contenido = tk.Frame(self, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        contenido.pack(fill="both", expand=True, padx=50)
        contenido.columnconfigure((0, 1), weight=1)

        self.crear_lista(
            contenido,
            0,
            "Defensores",
            self.app.gestion.top_defensores(),
            "victorias_defensor",
            DORADO
        )
        self.crear_lista(
            contenido,
            1,
            "Atacantes",
            self.app.gestion.top_atacantes(),
            "victorias_atacante",
            COLOR_FACCION["No muerto"]
        )

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            self,
            text="VOLVER",
            command=self.app.mostrar_menu,
            bg=BG_PANEL,
            fg=TEXTO,
            relief="flat",
            cursor="hand2",
            width=18,
            pady=10,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=25)

    #Dibuja una columna del ranking con posiciones, nombres y victorias.

    def crear_lista(self, parent, columna, titulo, datos, clave, color):
        #Construye una tabla sencilla para el ranking
        marco = tk.Frame(parent, bg=BG_PANEL, padx=18, pady=18)
        #Coloca el componente en la fila y columna indicadas de la interfaz
        marco.grid(row=0, column=columna, padx=12, sticky="nsew")

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            marco,
            text=titulo,
            bg=BG_PANEL,
            fg=color,
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(0, 15))

        #Comprueba que se cumplan los requisitos antes de continuar
        if not datos:
            #Coloca el componente dentro de la ventana con el administrador pack
            tk.Label(
                marco,
                text="Sin registros",
                bg=BG_PANEL,
                fg=TEXTO_SUAVE
            ).pack()
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Recorre los elementos de esta colección para procesarlos uno por uno
        for puesto, (usuario, info) in enumerate(datos, 1):
            #Crea un contenedor para organizar los elementos de esta parte de la pantalla
            fila = tk.Frame(marco, bg=BG_INPUT, padx=12, pady=9)
            #Coloca el componente dentro de la ventana con el administrador pack
            fila.pack(fill="x", pady=4)

            #Coloca el componente dentro de la ventana con el administrador pack
            tk.Label(
                fila,
                text=f"{puesto}. {usuario}",
                bg=BG_INPUT,
                fg=TEXTO,
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

            #Coloca el componente dentro de la ventana con el administrador pack
            tk.Label(
                fila,
                text=str(info.get(clave, 0)),
                bg=BG_INPUT,
                fg=color,
                font=("Segoe UI", 12, "bold")
            ).pack(side="right")


#---------------------------------------------------------------------
#---------------------------------------------------------------------

#Interfaz principal de la partida.
#Coordina tienda, tablero, panel de información, registro de eventos y avance de fases.

class PantallaJuego(tk.Frame):
    #Crea el estado de partida, el motor de combate y todos los controles del tablero.

    def __init__(self, app):
        super().__init__(app, bg=BG)
        #Guarda app como parte del estado que utilizará esta clase
        self.app = app
        #Guarda estado como parte del estado que utilizará esta clase
        self.estado = EstadoPartida(
            app.jugador_1,
            app.jugador_2,
            app.gestion
        )
        #Guarda gestor sprites como parte del estado que utilizará esta clase
        self.gestor_sprites = GestorSprites()
        #Guarda seleccion actual como parte del estado que utilizará esta clase
        self.seleccion_actual = None
        #Guarda motor combate como parte del estado que utilizará esta clase
        self.motor_combate = None
        #Guarda combate activo como parte del estado que utilizará esta clase
        self.combate_activo = False
        #Guarda ultimo resultado como parte del estado que utilizará esta clase
        self.ultimo_resultado = None

        #Variables que actualizan textos del HUD
        self.var_ronda = tk.StringVar()
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_fase = tk.StringVar()
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_dinero_def = tk.StringVar()
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_dinero_atk = tk.StringVar()
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_marcador = tk.StringVar()
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_seleccion = tk.StringVar(value="Sin selección")
        #Crea una variable de Tkinter para actualizar este texto dinámicamente
        self.var_instruccion = tk.StringVar()

        self.construir_interfaz()
        #Actualiza los datos visibles después de este cambio
        self.actualizar_interfaz()
        #Programa la siguiente acción sin detener la interfaz gráfica
        self.after(200, self.centrar_mapa)
        #Programa la siguiente acción sin detener la interfaz gráfica
        self.after(700, self.informar_sprites_faltantes)

    #Muestra en consola una advertencia cuando faltan archivos de imagen.

    def informar_sprites_faltantes(self):
        #Informa una sola vez cuando alguna ruta de sprite no pudo localizarse
        cantidad = len(self.gestor_sprites.rutas_faltantes)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if cantidad > 0:
            self.agregar_log(
                f"No se localizaron {cantidad} rutas de sprites. "
                "El programa intentó buscar nombres equivalentes dentro de la carpeta."
            )

    #Distribuye la barra superior, tienda, tablero, información y controles de la partida.

    def construir_interfaz(self):
        #Barra superior con información de la partida
        superior = tk.Frame(self, bg=BG_PANEL, height=96)
        #Coloca el componente dentro de la ventana con el administrador pack
        superior.pack(fill="x")
        superior.pack_propagate(False)

        defensor = self.app.jugador_1
        atacante = self.app.jugador_2

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        bloque_def = tk.Frame(superior, bg=BG_PANEL)
        #Coloca el componente dentro de la ventana con el administrador pack
        bloque_def.pack(side="left", padx=18, pady=8)
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_def,
            text=f"{defensor['nombre']} - DEFENSOR",
            bg=BG_PANEL,
            fg=COLOR_FACCION[defensor["faccion"]],
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_def,
            text=f"Facción: {defensor['faccion']}",
            bg=BG_PANEL,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 10, "italic")
        ).pack(anchor="w")
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_def,
            textvariable=self.var_dinero_def,
            bg=BG_PANEL,
            fg=TEXTO,
            font=("Segoe UI", 12)
        ).pack(anchor="w")

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        centro = tk.Frame(superior, bg=BG_PANEL)
        #Coloca el componente dentro de la ventana con el administrador pack
        centro.pack(side="left", expand=True)
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            textvariable=self.var_ronda,
            bg=BG_PANEL,
            fg=DORADO,
            font=("Georgia", 19, "bold")
        ).pack()
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            textvariable=self.var_fase,
            bg=BG_PANEL,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 11)
        ).pack()
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            textvariable=self.var_marcador,
            bg=BG_PANEL,
            fg=TEXTO,
            font=("Segoe UI", 11, "bold")
        ).pack()

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        bloque_atk = tk.Frame(superior, bg=BG_PANEL)
        #Coloca el componente dentro de la ventana con el administrador pack
        bloque_atk.pack(side="right", padx=18, pady=8)
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_atk,
            text=f"{atacante['nombre']} - ATACANTE",
            bg=BG_PANEL,
            fg=COLOR_FACCION[atacante["faccion"]],
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="e")
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_atk,
            text=f"Facción: {atacante['faccion']}",
            bg=BG_PANEL,
            fg=TEXTO_SUAVE,
            font=("Segoe UI", 10, "italic")
        ).pack(anchor="e")
        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            bloque_atk,
            textvariable=self.var_dinero_atk,
            bg=BG_PANEL,
            fg=TEXTO,
            font=("Segoe UI", 12)
        ).pack(anchor="e")

        #Barra visible para cambiar de fase, cancelar compras y controlar la música
        acciones = tk.Frame(self, bg=BG_PANEL, height=62)
        #Coloca el componente dentro de la ventana con el administrador pack
        acciones.pack(fill="x", padx=8, pady=(0, 6))
        acciones.pack_propagate(False)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            acciones,
            textvariable=self.var_seleccion,
            bg=BG_PANEL,
            fg=TEXTO,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(14, 10))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            acciones,
            text="CANCELAR SELECCIÓN",
            command=self.cancelar_seleccion,
            bg=BG_INPUT,
            fg=TEXTO_SUAVE,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8
        ).pack(side="left", padx=4)

        #Crea el botón y conecta la acción que se ejecutará al presionarlo
        self.boton_musica = tk.Button(
            acciones,
            text="MÚSICA: APAGADA",
            command=self.alternar_musica,
            bg=BG_INPUT,
            fg=TEXTO,
            relief="flat",
            cursor="hand2",
            width=18,
            pady=9,
            font=("Segoe UI", 10, "bold")
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.boton_musica.pack(side="right", padx=(4, 14), pady=8)
        #Actualiza los datos visibles después de este cambio
        self.actualizar_boton_musica()

        #Crea el botón y conecta la acción que se ejecutará al presionarlo
        self.boton_fase = tk.Button(
            acciones,
            command=self.accion_fase,
            bg=DORADO,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            width=28,
            pady=10,
            font=("Segoe UI", 12, "bold")
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.boton_fase.pack(side="right", padx=4, pady=8)

        #Área central dividida en tienda, mapa e información
        cuerpo = tk.Frame(self, bg=BG)
        #Coloca el componente dentro de la ventana con el administrador pack
        cuerpo.pack(fill="both", expand=True, padx=8, pady=8)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        self.panel_tienda = tk.Frame(cuerpo, bg=BG_PANEL, width=190)
        #Coloca el componente en la fila y columna indicadas de la interfaz
        self.panel_tienda.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        self.panel_tienda.grid_propagate(False)

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        marco_mapa = tk.Frame(cuerpo, bg=BG_MAPA)
        #Coloca el componente en la fila y columna indicadas de la interfaz
        marco_mapa.grid(row=0, column=1, sticky="nsew")
        marco_mapa.columnconfigure(0, weight=1)
        marco_mapa.rowconfigure(0, weight=1)

        #El tablero completo cabe en pantalla y no utiliza barras de desplazamiento
        ancho_tablero = COLUMNAS_MAPA * TAM_CELDA
        alto_tablero = FILAS_MAPA * TAM_CELDA

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        contenedor_tablero = tk.Frame(marco_mapa, bg=BG_MAPA)
        #Ubica el componente en una posición específica de la ventana
        contenedor_tablero.place(relx=0.5, rely=0.5, anchor="center")

        #Crea el lienzo donde se dibujará el tablero del juego
        self.canvas = tk.Canvas(
            contenedor_tablero,
            width=ancho_tablero,
            height=alto_tablero,
            bg=BG_MAPA,
            highlightthickness=2,
            highlightbackground=BORDE
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.canvas.pack()

        #Asocia el evento del usuario con la función que debe responder
        self.canvas.bind("<Button-1>", self.click_mapa)
        #Asocia el evento del usuario con la función que debe responder
        self.canvas.bind("<Button-3>", self.click_derecho)

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        panel_derecho = tk.Frame(cuerpo, bg=BG_PANEL, width=205)
        #Coloca el componente en la fila y columna indicadas de la interfaz
        panel_derecho.grid(row=0, column=2, sticky="ns", padx=(8, 0))
        panel_derecho.grid_propagate(False)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            panel_derecho,
            text="INFORMACIÓN",
            bg=BG_PANEL,
            fg=DORADO,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(14, 8))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            panel_derecho,
            textvariable=self.var_instruccion,
            bg=BG_PANEL,
            fg=TEXTO,
            wraplength=180,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(fill="x", padx=14, pady=(0, 10))

        #Guarda texto info como parte del estado que utilizará esta clase
        self.texto_info = tk.Text(
            panel_derecho,
            height=8,
            bg=BG_INPUT,
            fg=TEXTO,
            relief="flat",
            wrap="word",
            font=("Consolas", 8),
            state="disabled"
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.texto_info.pack(fill="x", padx=12, pady=6)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            panel_derecho,
            text="REGISTRO DE EVENTOS",
            bg=BG_PANEL,
            fg=DORADO,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(10, 5))

        #Guarda texto log como parte del estado que utilizará esta clase
        self.texto_log = tk.Text(
            panel_derecho,
            bg="#0D0C13",
            fg=TEXTO_SUAVE,
            relief="flat",
            wrap="word",
            font=("Consolas", 9),
            state="disabled"
        )
        #Coloca el componente dentro de la ventana con el administrador pack
        self.texto_log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    #Sincroniza el texto y los colores del botón con el estado real de la música.

    def actualizar_boton_musica(self):
        #Sincroniza el botón con el estado global del reproductor
        texto, fondo, color_texto = self.app.gestor_musica.estilo_boton()
        #Actualiza la apariencia o el estado actual del componente
        self.boton_musica.config(
            text=texto,
            bg=fondo,
            fg=color_texto,
            activebackground=VERDE,
            activeforeground="#001B1A"
        )

    #Pausa, reanuda o selecciona música y actualiza el botón correspondiente.

    def alternar_musica(self):
        #Cambia entre reproducir, pausar y reanudar la música
        _, mensaje = self.app.gestor_musica.alternar(self)
        #Actualiza los datos visibles después de este cambio
        self.actualizar_boton_musica()
        self.agregar_log(mensaje)

        #Avisa únicamente cuando falta la dependencia pygame
        if "Pygame no está instalado" in mensaje:
            messagebox.showwarning("Música", mensaje)

    #Desplaza verticalmente el lienzo cuando se utiliza la rueda del mouse.

    def rueda_mouse(self, evento):
        #El tablero completo cabe en pantalla
        return None

    #Desplaza horizontalmente el lienzo cuando se mantiene la tecla correspondiente.

    def rueda_horizontal(self, evento):
        #El tablero completo cabe en pantalla
        return None

    #Coloca la vista del Canvas en una posición adecuada para mostrar el tablero.

    def centrar_mapa(self):
        #El tablero completo ya está centrado y visible
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    #Actualiza textos, tienda, botones y tablero para reflejar el estado actual.

    def actualizar_interfaz(self):
        #Actualiza todos los textos y reconstruye la tienda
        nombres_fase = {
            "construccion": "Fase de construcción",
            "despliegue": "Fase de despliegue",
            "combate": "Combate automático",
            "fin_ronda": "Fin de ronda",
            "fin_partida": "Fin de partida"
        }

        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_ronda.set(f"Ronda {self.estado.ronda_actual}")
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_fase.set(nombres_fase[self.estado.fase])
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_dinero_def.set(f"Dinero: {self.estado.dinero_defensor}")
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_dinero_atk.set(f"Dinero: {self.estado.dinero_atacante}")
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_marcador.set(
            f"Defensor {self.estado.rondas_defensor} - "
            f"{self.estado.rondas_atacante} Atacante"
        )

        #Comprueba la fase actual antes de permitir esta acción
        if self.estado.fase == "construccion":
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.var_instruccion.set(
                "Selecciona una torre o un muro y colócalo en el lado derecho. "
                "La torre central ocupa el bloque fijo de 4 x 4 casillas. "
                "Haz clic derecho para retirar una estructura y recuperar su costo."
            )
            #Actualiza la apariencia o el estado actual del componente
            self.boton_fase.config(text="CONFIRMAR CONSTRUCCIÓN", state="normal")

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "despliegue":
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.var_instruccion.set(
                "Selecciona una unidad y colócala en las cuatro columnas del lado "
                "izquierdo. Haz clic derecho para retirarla."
            )
            #Actualiza la apariencia o el estado actual del componente
            self.boton_fase.config(text="CONFIRMAR DESPLIEGUE", state="normal")

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "combate":
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.var_instruccion.set(
                "Las torres atacan automáticamente y las unidades buscan un camino "
                "hacia la torre central."
            )
            #Actualiza la apariencia o el estado actual del componente
            self.boton_fase.config(text="COMBATE EN CURSO", state="disabled")

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "fin_ronda":
            #Actualiza el valor que se muestra dinámicamente en la interfaz
            self.var_instruccion.set(
                "La ronda terminó. Revisa las estadísticas y continúa a la siguiente."
            )
            #Actualiza la apariencia o el estado actual del componente
            self.boton_fase.config(text="SIGUIENTE RONDA", state="normal")

        self.construir_tienda()
        self.dibujar_mapa()

    #Genera las opciones de compra según la fase y el rol activo.

    def construir_tienda(self):
        #Elimina los botones anteriores de la tienda
        for widget in self.panel_tienda.winfo_children():
            #Cierra esta ventana o elimina el componente actual
            widget.destroy()

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            self.panel_tienda,
            text="TIENDA",
            bg=BG_PANEL,
            fg=DORADO,
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(15, 12))

        #Comprueba la fase actual antes de permitir esta acción
        if self.estado.fase == "construccion":
            #Recorre los elementos de esta colección para procesarlos uno por uno
            for nombre in listar_torres():
                #Crea una copia independiente del objeto seleccionado por el jugador
                torre = crear_torre(nombre, self.estado.faccion_defensor)
                self.crear_boton_tienda(
                    nombre,
                    torre.costo,
                    lambda n=nombre: self.seleccionar("torre", n),
                    f"Vida {torre.vida_maxima} | Daño {torre.daño}\n"
                    f"Alcance {torre.alcance} | {torre.habilidad}"
                )

            #Crea una copia independiente del objeto seleccionado por el jugador
            muro = crear_muro(self.estado.faccion_defensor)
            self.crear_boton_tienda(
                "Muro",
                muro.costo,
                lambda: self.seleccionar("muro", "Muro"),
                f"Vida {muro.vida_maxima} | Bloquea el paso"
            )

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "despliegue":
            #Obtiene los datos disponibles para construir esta parte de la interfaz
            faccion = obtener_faccion(self.estado.faccion_atacante)
            #Recorre los elementos de esta colección para procesarlos uno por uno
            for nombre in faccion.listar_unidades():
                unidad = faccion.obtener_plantilla(nombre)
                self.crear_boton_tienda(
                    nombre,
                    unidad.costo,
                    lambda n=nombre: self.seleccionar("unidad", n),
                    f"Vida {unidad.vida_maxima} | Daño {unidad.daño}\n"
                    f"Movimiento {unidad.movimiento} | {unidad.habilidad}"
                )

        else:
            #Coloca el componente dentro de la ventana con el administrador pack
            tk.Label(
                self.panel_tienda,
                text="La tienda no está disponible durante el combate.",
                bg=BG_PANEL,
                fg=TEXTO_SUAVE,
                wraplength=190,
                justify="center"
            ).pack(padx=15, pady=25)

    #Crea una tarjeta de compra con nombre, costo, descripción y acción.

    def crear_boton_tienda(self, nombre, costo, comando, detalle):
        #Crea una tarjeta de compra
        marco = tk.Frame(self.panel_tienda, bg=BG_INPUT, padx=9, pady=8)
        #Coloca el componente dentro de la ventana con el administrador pack
        marco.pack(fill="x", padx=10, pady=5)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            marco,
            text=f"{nombre} - {costo}",
            command=comando,
            bg=BORDE,
            fg=TEXTO,
            activebackground=DORADO,
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold")
        ).pack(fill="x")

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            marco,
            text=detalle,
            bg=BG_INPUT,
            fg=TEXTO_SUAVE,
            justify="left",
            wraplength=185,
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(5, 0))

    #Guarda el tipo de objeto que se colocará en el siguiente clic del tablero.

    def seleccionar(self, tipo, nombre):
        #Guarda el objeto que se colocará con el próximo clic
        self.seleccion_actual = (tipo, nombre)
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_seleccion.set(f"Seleccionado: {nombre}")

    #Anula la compra seleccionada antes de colocarla.

    def cancelar_seleccion(self):
        #Cancela una compra pendiente
        self.seleccion_actual = None
        #Actualiza el valor que se muestra dinámicamente en la interfaz
        self.var_seleccion.set("Sin selección")

    #Convierte las coordenadas del mouse en una fila y columna del tablero.

    def posicion_evento(self, evento):
        #Convierte las coordenadas del canvas en fila y columna
        x = self.canvas.canvasx(evento.x)
        y = self.canvas.canvasy(evento.y)
        columna = int(x // TAM_CELDA)
        fila = int(y // TAM_CELDA)
        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return fila, columna

    #Procesa selección, compra o consulta de información al hacer clic en una casilla.

    def click_mapa(self, evento):
        #Coloca el objeto seleccionado o muestra información de la casilla
        posicion = self.posicion_evento(evento)
        #Comprueba que la posición sea válida y esté disponible
        if not self.estado.dentro_mapa(posicion):
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Comprueba que el dato necesario exista antes de continuar
        if self.seleccion_actual is None:
            #Muestra en el panel la información del objeto seleccionado
            self.mostrar_info_objeto(self.estado.objeto_en(posicion))
            #Finaliza el método y devuelve el control al punto anterior
            return

        tipo, nombre = self.seleccion_actual
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if tipo == "torre":
            exito, mensaje = self.estado.comprar_torre(nombre, posicion)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        elif tipo == "muro":
            exito, mensaje = self.estado.comprar_muro(posicion)
        else:
            exito, mensaje = self.estado.comprar_unidad(nombre, posicion)

        self.agregar_log(mensaje)
        #Comprueba que se cumplan los requisitos antes de continuar
        if not exito:
            messagebox.showwarning("Colocación", mensaje)

        #Actualiza los datos visibles después de este cambio
        self.actualizar_interfaz()

    #Retira un objeto durante la preparación cuando se usa el botón derecho.

    def click_derecho(self, evento):
        #Retira un objeto durante construcción o despliegue
        posicion = self.posicion_evento(evento)
        exito, mensaje = self.estado.eliminar_objeto(posicion)
        self.agregar_log(mensaje)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if exito:
            #Actualiza los datos visibles después de este cambio
            self.actualizar_interfaz()

    #Presenta en el panel lateral los atributos del objeto seleccionado.

    def mostrar_info_objeto(self, objeto):
        #Muestra los atributos del objeto seleccionado
        self.texto_info.config(state="normal")
        #Elimina el contenido anterior antes de mostrar datos nuevos
        self.texto_info.delete("1.0", "end")

        #Comprueba que el dato necesario exista antes de continuar
        if objeto is None:
            #Inserta el contenido nuevo dentro del componente correspondiente
            self.texto_info.insert("end", "Casilla vacía.")
        else:
            #Usa obtener_informacion cuando la clase lo incluye
            if hasattr(objeto, "obtener_informacion"):
                datos = objeto.obtener_informacion()
            else:
                #Respaldo para evitar errores con versiones anteriores
                datos = {
                    "nombre": getattr(objeto, "nombre", "Objeto"),
                    "vida": getattr(objeto, "vida", "-"),
                    "vida_maxima": getattr(objeto, "vida_maxima", "-"),
                    "estado": getattr(objeto, "estado", "-"),
                    "posicion": getattr(objeto, "posicion", "-")
                }

            #Recorre los elementos de esta colección para procesarlos uno por uno
            for clave, valor in datos.items():
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if clave in ("sprites", "sprite_actual", "sprite_proyectil"):
                    #Omite este elemento y continúa con la siguiente repetición
                    continue
                nombre = clave.replace("_", " ").capitalize()
                #Inserta el contenido nuevo dentro del componente correspondiente
                self.texto_info.insert("end", f"{nombre}: {valor}\n")

        #Actualiza la apariencia o el estado actual del componente
        self.texto_info.config(state="disabled")

    #Añade un mensaje al registro visual de eventos y desplaza la vista al final.

    def agregar_log(self, mensaje):
        #Agrega una línea al registro de eventos
        self.texto_log.config(state="normal")
        #Inserta el contenido nuevo dentro del componente correspondiente
        self.texto_log.insert("end", mensaje + "\n")
        self.texto_log.see("end")
        #Actualiza la apariencia o el estado actual del componente
        self.texto_log.config(state="disabled")

    #Ejecuta la acción principal correspondiente a la fase actual.

    def accion_fase(self):
        #Ejecuta la acción principal según la fase actual
        if self.estado.fase == "construccion":
            exito, mensaje = self.estado.confirmar_construccion()
            #Comprueba que se cumplan los requisitos antes de continuar
            if not exito:
                messagebox.showwarning("Construcción", mensaje)
                #Finaliza el método y devuelve el control al punto anterior
                return
            self.cancelar_seleccion()
            self.agregar_log(mensaje)
            #Actualiza los datos visibles después de este cambio
            self.actualizar_interfaz()

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "despliegue":
            exito, mensaje = self.estado.confirmar_despliegue()
            #Comprueba que se cumplan los requisitos antes de continuar
            if not exito:
                messagebox.showwarning("Despliegue", mensaje)
                #Finaliza el método y devuelve el control al punto anterior
                return
            self.cancelar_seleccion()
            self.agregar_log(mensaje)
            #Actualiza los datos visibles después de este cambio
            self.actualizar_interfaz()
            self.iniciar_combate()

        #Comprueba la fase actual antes de permitir esta acción
        elif self.estado.fase == "fin_ronda":
            ganador = self.estado.ganador_partida()
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if ganador:
                self.finalizar_partida(ganador)
            else:
                self.estado.nueva_ronda()
                #Guarda ultimo resultado como parte del estado que utilizará esta clase
                self.ultimo_resultado = None
                self.agregar_log(f"Comienza la ronda {self.estado.ronda_actual}.")
                #Actualiza los datos visibles después de este cambio
                self.actualizar_interfaz()
                self.centrar_mapa()

    #Prepara el motor y programa el primer turno automático con un pequeño retardo.

    def iniciar_combate(self):
        #Crea el motor automático y programa el primer turno
        self.motor_combate = MotorCombate(self.estado)
        #Guarda combate activo como parte del estado que utilizará esta clase
        self.combate_activo = True
        #Programa la siguiente acción sin detener la interfaz gráfica
        self.after(RETARDO_INICIO_COMBATE, self.paso_combate)

    #Ejecuta un turno, actualiza la interfaz y programa el siguiente mientras no termine.

    def paso_combate(self):
        #Ejecuta un turno, actualiza el mapa y programa el siguiente
        if not self.combate_activo:
            #Finaliza el método y devuelve el control al punto anterior
            return

        resultado = self.motor_combate.ejecutar_turno()
        #Recorre los elementos de esta colección para procesarlos uno por uno
        for mensaje in self.motor_combate.logs_turno:
            self.agregar_log(mensaje)

        self.dibujar_mapa(self.motor_combate.eventos)

        #Comprueba que el dato necesario exista antes de continuar
        if resultado is not None:
            #Guarda combate activo como parte del estado que utilizará esta clase
            self.combate_activo = False
            self.terminar_ronda(resultado)
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Programa la siguiente acción sin detener la interfaz gráfica
        self.after(RETARDO_ENTRE_TURNOS, self.paso_combate)

    #Registra el resultado, muestra el resumen y habilita el avance a la siguiente ronda.

    def terminar_ronda(self, resultado):
        #Registra el marcador y muestra el resumen de la ronda
        self.ultimo_resultado = resultado
        self.estado.registrar_resultado(resultado)
        #Actualiza los datos visibles después de este cambio
        self.actualizar_interfaz()

        nombre_ganador = (
            self.app.jugador_1["nombre"]
            if resultado.ganador == "defensor"
            else self.app.jugador_2["nombre"]
        )

        resumen = (
            f"Ganador: {nombre_ganador}\n"
            f"Turnos: {resultado.turnos}\n"
            f"Unidades eliminadas: {resultado.unidades_eliminadas}\n"
            f"Daño a estructuras: {resultado.daño_a_estructuras}\n"
            f"Estructuras destruidas: {resultado.estructuras_destruidas}\n"
            f"Daño a la torre central: {resultado.daño_a_base}\n\n"
            f"Bono defensor siguiente ronda: {self.estado.bono_defensor}\n"
            f"Bono atacante siguiente ronda: {self.estado.bono_atacante}"
        )
        messagebox.showinfo("Resumen de ronda", resumen)

        #Si alguien alcanzó tres rondas, cambia el texto del botón
        if self.estado.ganador_partida():
            #Actualiza la apariencia o el estado actual del componente
            self.boton_fase.config(text="VER GANADOR")

    #Muestra la pantalla final y guarda la victoria del ganador.

    def finalizar_partida(self, rol_ganador):
        #Guarda la victoria y muestra la pantalla final
        self.estado.fase = "fin_partida"
        self.estado.guardar_victoria_final(rol_ganador)

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if rol_ganador == "defensor":
            datos = self.app.jugador_1
            marcador = self.estado.rondas_defensor
        else:
            datos = self.app.jugador_2
            marcador = self.estado.rondas_atacante

        #Recorre los elementos de esta colección para procesarlos uno por uno
        for widget in self.winfo_children():
            #Cierra esta ventana o elimina el componente actual
            widget.destroy()

        #Crea un contenedor para organizar los elementos de esta parte de la pantalla
        centro = tk.Frame(self, bg=BG)
        #Ubica el componente en una posición específica de la ventana
        centro.place(relx=0.5, rely=0.48, anchor="center")

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            text="PARTIDA TERMINADA",
            bg=BG,
            fg=DORADO,
            font=("Georgia", 34, "bold")
        ).pack(pady=(0, 10))

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            text=datos["nombre"],
            bg=BG,
            fg=COLOR_FACCION[datos["faccion"]],
            font=("Georgia", 45, "bold")
        ).pack()

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Label(
            centro,
            text=(
                f"Ganador como {rol_ganador}\n"
                f"Facción: {datos['faccion']}\n"
                f"Rondas ganadas: {marcador}"
            ),
            bg=BG,
            fg=TEXTO,
            font=("Segoe UI", 15),
            justify="center"
        ).pack(pady=20)

        #Coloca el componente dentro de la ventana con el administrador pack
        tk.Button(
            centro,
            text="VOLVER AL MENÚ",
            command=self.volver_menu,
            bg=DORADO,
            fg="#000000",
            relief="flat",
            cursor="hand2",
            width=22,
            pady=12,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=10)

    #Regresa al menú principal y descarta la partida actual.

    def volver_menu(self):
        #Restaura la ventana y regresa al menú principal
        self.app.state("normal")
        #Abre o actualiza la pantalla correspondiente a esta acción
        self.app.mostrar_menu()

    #Redibuja la cuadrícula, zonas, objetos, sprites y efectos temporales.

    def dibujar_mapa(self, eventos=None):
        #Redibuja el tablero y todos los objetos
        self.canvas.delete("all")
        eventos = eventos or []
        casillas_central = self.estado.casillas_torre_central()

        #Dibuja un tablero tipo ajedrez con zonas laterales
        for fila in range(FILAS_MAPA):
            #Recorre las casillas necesarias para dibujar o validar el tablero
            for columna in range(COLUMNAS_MAPA):
                x1 = columna * TAM_CELDA
                y1 = fila * TAM_CELDA
                x2 = x1 + TAM_CELDA
                y2 = y1 + TAM_CELDA

                es_clara = (fila + columna) % 2 == 0
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if columna < COLUMNAS_DESPLIEGUE:
                    relleno = "#18334A" if es_clara else "#11283B"
                #Evalúa esta condición para decidir qué acción debe ejecutarse
                elif columna >= COLUMNA_INICIO_DEFENSA:
                    relleno = "#16433E" if es_clara else "#10352F"
                else:
                    relleno = "#243642" if es_clara else "#1B2B35"

                #Evalúa esta condición para decidir qué acción debe ejecutarse
                if (fila, columna) in casillas_central:
                    relleno = "#6A432B" if es_clara else "#553420"

                #Dibuja este elemento dentro del lienzo del tablero
                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=relleno,
                    outline="#31505B",
                    width=1
                )

        #Marca el límite de despliegue y el inicio de construcción
        self.canvas.create_line(
            COLUMNAS_DESPLIEGUE * TAM_CELDA,
            0,
            COLUMNAS_DESPLIEGUE * TAM_CELDA,
            FILAS_MAPA * TAM_CELDA,
            fill="#C77DFF",
            width=3
        )
        #Dibuja este elemento dentro del lienzo del tablero
        self.canvas.create_line(
            COLUMNA_INICIO_DEFENSA * TAM_CELDA,
            0,
            COLUMNA_INICIO_DEFENSA * TAM_CELDA,
            FILAS_MAPA * TAM_CELDA,
            fill="#2EC4B6",
            width=3
        )

        #Dibuja primero estructuras y después unidades
        self.dibujar_objeto(self.estado.torre_central, "base")
        #Recorre las estructuras colocadas para procesar su estado
        for muro in self.estado.muros:
            self.dibujar_objeto(muro, "muro")
        #Recorre las estructuras colocadas para procesar su estado
        for torre in self.estado.torres:
            self.dibujar_objeto(torre, "torre")
        #Recorre las unidades para actualizar su comportamiento en el turno
        for unidad in self.estado.unidades:
            #Comprueba si el objeto continúa activo dentro de la partida
            if not unidad.esta_eliminada():
                self.dibujar_objeto(unidad, "unidad")

        #Dibuja eventos temporales de combate
        for evento in eventos:
            self.dibujar_evento(evento)

    #Recupera rutas de sprites guardadas con el formato antiguo de diccionarios.

    def obtener_ruta_estructura_antigua(self, opciones, estado):
        #Admite diccionarios antiguos con rutas utilizadas como claves
        if not isinstance(opciones, dict):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        #Primero intenta la estructura correcta: estado asociado a una ruta
        directa = opciones.get(estado)
        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if isinstance(directa, str):
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return directa

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if isinstance(directa, (list, tuple)) and directa:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return directa[0]

        #En versiones anteriores las rutas se guardaron como claves con valor None
        rutas = [
            clave for clave in opciones.keys()
            if isinstance(clave, str)
            and Path(clave).suffix.casefold() in {
                ".png", ".gif", ".jpg", ".jpeg", ".webp"
            }
        ]

        #Comprueba que se cumplan los requisitos antes de continuar
        if not rutas:
            #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
            return None

        palabras_estado = {
            "entero": ("full", "entero", "intact"),
            "dañado": ("damaged", "danado", "broken"),
            "destruido": ("destroyed", "destruido", "broken")
        }

        buscadas = palabras_estado.get(estado, ())
        #Recorre las rutas disponibles hasta encontrar el recurso correcto
        for ruta in rutas:
            normalizada = self.gestor_sprites.normalizar(ruta)
            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if any(palabra in normalizada for palabra in buscadas):
                #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
                return ruta

        #Devuelve el resultado obtenido para que pueda utilizarse fuera del método
        return rutas[0]

    #Dibuja una unidad o estructura con su sprite; usa una figura de respaldo si falta.

    def dibujar_objeto(self, objeto, tipo):
        #Dibuja un sprite o una figura alternativa
        if objeto is None or objeto.posicion is None:
            #Finaliza el método y devuelve el control al punto anterior
            return

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if tipo == "base":
            fila, columna = ORIGEN_TORRE_CENTRAL
            ancho_objeto = TORRE_CENTRAL_ANCHO * TAM_CELDA
            alto_objeto = TORRE_CENTRAL_ALTO * TAM_CELDA
        else:
            fila, columna = objeto.posicion
            ancho_objeto = TAM_CELDA
            alto_objeto = TAM_CELDA

        x1 = columna * TAM_CELDA
        y1 = fila * TAM_CELDA
        centro_x = x1 + ancho_objeto / 2
        centro_y = y1 + alto_objeto / 2

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if tipo == "unidad":
            #Obtiene el recurso gráfico que corresponde al objeto actual
            ruta = objeto.obtener_sprite_actual()
            faccion = objeto.faccion
        else:
            #Obtiene el recurso gráfico que corresponde al objeto actual
            ruta = objeto.obtener_sprite_actual()
            faccion = objeto.faccion_visual

            #Compatibilidad con versiones antiguas que guardaban la ruta como clave
            if not ruta and hasattr(objeto, "sprites_por_faccion"):
                opciones = objeto.sprites_por_faccion.get(faccion, {})
                ruta = self.obtener_ruta_estructura_antigua(
                    opciones,
                    getattr(objeto, "estado", "entero")
                )

        vida = objeto.vida
        vida_maxima = objeto.vida_maxima
        #Obtiene el recurso gráfico que corresponde al objeto actual
        imagen = self.gestor_sprites.cargar(
            ruta,
            ancho_objeto - 6,
            alto_objeto - 10
        )

        #Comprueba que el dato necesario exista antes de continuar
        if imagen is not None:
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_image(
                centro_x,
                centro_y - 2,
                image=imagen,
                anchor="center"
            )
        else:
            color = COLOR_FACCION.get(faccion, AZUL)
            abreviatura = ABREVIATURAS.get(objeto.nombre, objeto.nombre[:2])

            #Evalúa esta condición para decidir qué acción debe ejecutarse
            if tipo == "unidad":
                #Dibuja este elemento dentro del lienzo del tablero
                self.canvas.create_oval(
                    x1 + 7,
                    y1 + 6,
                    x1 + ancho_objeto - 7,
                    y1 + alto_objeto - 8,
                    fill=color,
                    outline="#FFFFFF",
                    width=2
                )
            else:
                #Dibuja este elemento dentro del lienzo del tablero
                self.canvas.create_rectangle(
                    x1 + 5,
                    y1 + 5,
                    x1 + ancho_objeto - 5,
                    y1 + alto_objeto - 8,
                    fill=color,
                    outline="#FFFFFF",
                    width=2
                )

            tamaño_texto = 18 if tipo == "base" else 9
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_text(
                centro_x,
                centro_y - 1,
                text=abreviatura,
                fill="#090909",
                font=("Segoe UI", tamaño_texto, "bold")
            )

        #Marca visualmente cualquier objeto destruido
        if hasattr(objeto, "esta_destruido") and objeto.esta_destruido():
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_line(
                x1 + 6,
                y1 + 6,
                x1 + ancho_objeto - 6,
                y1 + alto_objeto - 10,
                fill=ROJO,
                width=4
            )
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_line(
                x1 + ancho_objeto - 6,
                y1 + 6,
                x1 + 6,
                y1 + alto_objeto - 10,
                fill=ROJO,
                width=4
            )

        #Dibuja la barra de vida usando el ancho real del objeto
        proporcion = 0 if vida_maxima == 0 else max(0, min(1, vida / vida_maxima))
        #Dibuja este elemento dentro del lienzo del tablero
        self.canvas.create_rectangle(
            x1 + 4,
            y1 + alto_objeto - 7,
            x1 + ancho_objeto - 4,
            y1 + alto_objeto - 3,
            fill="#3A1C1C",
            outline=""
        )
        #Dibuja este elemento dentro del lienzo del tablero
        self.canvas.create_rectangle(
            x1 + 4,
            y1 + alto_objeto - 7,
            x1 + 4 + (ancho_objeto - 8) * proporcion,
            y1 + alto_objeto - 3,
            fill=VERDE,
            outline=""
        )

        #Avanza la animación de unidades con varios frames
        if tipo == "unidad" and not objeto.esta_eliminada():
            objeto.avanzar_frame()

    #Representa visualmente proyectiles, golpes y otros eventos del turno.

    def dibujar_evento(self, evento):
        #Representa un proyectil o golpe durante un turno de combate
        origen = evento.get("origen")
        destino = evento.get("destino")
        #Comprueba que el dato necesario exista antes de continuar
        if origen is None or destino is None:
            #Finaliza el método y devuelve el control al punto anterior
            return

        x1 = origen[1] * TAM_CELDA + TAM_CELDA / 2
        y1 = origen[0] * TAM_CELDA + TAM_CELDA / 2
        x2 = destino[1] * TAM_CELDA + TAM_CELDA / 2
        y2 = destino[0] * TAM_CELDA + TAM_CELDA / 2

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        if evento.get("tipo") == "proyectil":
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_line(x1, y1, x2, y2, fill=DORADO, width=3, arrow="last")
            ruta = evento.get("sprite")
            #Obtiene el recurso gráfico que corresponde al objeto actual
            imagen = self.gestor_sprites.cargar(ruta, 24, 24)
            #Comprueba que el dato necesario exista antes de continuar
            if imagen is not None:
                #Dibuja este elemento dentro del lienzo del tablero
                self.canvas.create_image((x1 + x2) / 2, (y1 + y2) / 2, image=imagen)
            else:
                #Dibuja este elemento dentro del lienzo del tablero
                self.canvas.create_oval(
                    (x1 + x2) / 2 - 5,
                    (y1 + y2) / 2 - 5,
                    (x1 + x2) / 2 + 5,
                    (y1 + y2) / 2 + 5,
                    fill=DORADO,
                    outline=""
                )

        #Evalúa esta condición para decidir qué acción debe ejecutarse
        elif evento.get("tipo") == "golpe":
            #Dibuja este elemento dentro del lienzo del tablero
            self.canvas.create_line(x1, y1, x2, y2, fill=ROJO, width=4)


#Inicia la aplicación solamente cuando este archivo se ejecuta directamente
if __name__ == "__main__":
    app = Aplicacion()
    #Mantiene la aplicación abierta y atendiendo los eventos del usuario
    app.mainloop()