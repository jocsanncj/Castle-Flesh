from copy import deepcopy


class Unidad:
    #Estados permitidos para una unidad dentro de la partida
    ESTADOS_VALIDOS = ("activa", "eliminada", "congelada", "protegida")

    def __init__(
        self,
        nombre,
        faccion,
        costo,
        vida,
        daño,
        movimiento,
        habilidad,
        tipo_habilidad,
        recarga_habilidad,
        sprites
    ):
        #Guarda el nombre de la unidad
        self.nombre = nombre
        #Guarda la facción a la que pertenece la unidad
        self.faccion = faccion
        #Guarda el costo de compra de la unidad
        self.costo = costo
        #Guarda la vida máxima de la unidad
        self.vida_maxima = vida
        #Guarda la vida actual de la unidad
        self.vida = vida
        #Guarda el daño básico que puede causar
        self.daño = daño
        #Guarda la cantidad de casillas que puede avanzar por turno
        self.movimiento = movimiento
        #Guarda el nombre visible de la habilidad
        self.habilidad = habilidad
        #Guarda el identificador interno de la habilidad
        self.tipo_habilidad = tipo_habilidad
        #Guarda la cantidad de turnos que deben pasar para reutilizar la habilidad
        self.recarga_habilidad = recarga_habilidad
        #Guarda los turnos restantes antes de volver a usar la habilidad
        self.turnos_recarga = 0
        #Guarda las rutas de los sprites organizadas por animación
        self.sprites = sprites

        #Guarda la animación que se está utilizando actualmente
        self.animacion_actual = "idle"

        #Guarda el índice del frame actual dentro de la animación
        self.indice_frame = 0
        #Guarda la posición actual de la unidad dentro del mapa
        self.posicion = None
        #Guarda el estado actual de la unidad
        self.estado = "activa"
        #Guarda la cantidad de turnos de protección restantes
        self.turnos_proteccion = 0
        #Guarda la cantidad de turnos de congelamiento restantes
        self.turnos_congelada = 0
        #Guarda el aumento temporal de movimiento
        self.movimiento_extra = 0
        #Guarda la cantidad de turnos durante los que aplica el movimiento extra
        self.turnos_movimiento_extra = 0

    def recibir_daño(self, cantidad):
        #Comprueba que el daño recibido sea numérico
        if not isinstance(cantidad, (int, float)):
            print("La cantidad de daño debe ser numérica")
            return False

        #Comprueba que el daño no sea negativo
        if cantidad < 0:
            print("El daño no puede ser negativo")
            return False

        #Reduce el daño a la mitad cuando la unidad está protegida
        if self.turnos_proteccion > 0:
            cantidad = cantidad / 2

        #Resta el daño a la vida actual
        self.vida -= cantidad

        #Evita que la vida quede en valores negativos
        if self.vida <= 0:
            self.vida = 0
            self.estado = "eliminada"

            #Cambia a la animación de muerte
            self.cambiar_animacion("dying")

        return True

    def curar(self, cantidad):
        #Comprueba que la curación sea numérica
        if not isinstance(cantidad, (int, float)):
            print("La cantidad de curación debe ser numérica")
            return False

        #Comprueba que la curación sea mayor que cero
        if cantidad <= 0:
            print("La curación debe ser mayor que cero")
            return False

        #Impide curar una unidad eliminada
        if self.esta_eliminada():
            print("No se puede curar una unidad eliminada")
            return False

        #Aumenta la vida sin superar la vida máxima
        self.vida = min(self.vida + cantidad, self.vida_maxima)
        return True

    def atacar(self, objetivo):
        #Comprueba que la unidad pueda actuar
        if not self.puede_actuar():
            print(f"{self.nombre} no puede atacar en este momento")
            return False

        #Comprueba que el objetivo tenga un método para recibir daño
        if not hasattr(objetivo, "recibir_daño"):
            print("El objetivo no puede recibir daño")
            return False

        #Cambia a la animación de ataque
        self.cambiar_animacion("slashing")

        #Aplica el daño básico al objetivo
        objetivo.recibir_daño(self.daño)
        return True

    def mover(self, nueva_posicion):
        #Comprueba que la unidad pueda actuar
        if not self.puede_actuar():
            print(f"{self.nombre} no puede moverse en este momento")
            return False

        #Comprueba que la posición tenga fila y columna
        if not isinstance(nueva_posicion, tuple) or len(nueva_posicion) != 2:
            print("La posición debe tener el formato (fila, columna)")
            return False

        #Cambia a la animación de movimiento
        self.cambiar_animacion("walking")

        #Guarda la nueva posición de la unidad
        self.posicion = nueva_posicion
        return True

    def obtener_movimiento_actual(self):
        #Retorna el movimiento básico más cualquier aumento temporal
        return self.movimiento + self.movimiento_extra

    def puede_actuar(self):
        #Comprueba que la unidad esté activa y no esté congelada
        return not self.esta_eliminada() and self.turnos_congelada == 0

    def habilidad_disponible(self):
        #Comprueba si la habilidad está fuera de recarga
        return self.turnos_recarga == 0 and not self.esta_eliminada()

    def usar_habilidad(self, objetivo=None):
        #Comprueba que la unidad pueda utilizar su habilidad
        if not self.habilidad_disponible():
            print(f"La habilidad de {self.nombre} todavía no está disponible")
            return False

        #Ejecuta la habilidad de ataque doble
        if self.tipo_habilidad == "ataque_doble":
            if objetivo is None or not hasattr(objetivo, "recibir_daño"):
                print("La habilidad necesita un objetivo válido")
                return False
            objetivo.recibir_daño(self.daño * 2)

        #Ejecuta la habilidad de escudo temporal
        elif self.tipo_habilidad == "escudo":
            self.turnos_proteccion = 2
            self.estado = "protegida"

        #Ejecuta la habilidad de curación
        elif self.tipo_habilidad == "curacion":
            self.curar(self.vida_maxima * 0.35)

        #Ejecuta la habilidad de velocidad
        elif self.tipo_habilidad == "velocidad":
            self.movimiento_extra = 2
            self.turnos_movimiento_extra = 2

        #Ejecuta la habilidad de daño extra contra edificios
        elif self.tipo_habilidad == "daño_edificios":
            if objetivo is None or not hasattr(objetivo, "recibir_daño"):
                print("La habilidad necesita un objetivo válido")
                return False
            objetivo.recibir_daño(self.daño * 1.5)

        #Ejecuta la habilidad de daño en área
        elif self.tipo_habilidad == "daño_area":
            if not isinstance(objetivo, list):
                print("La habilidad necesita una lista de objetivos")
                return False
            for elemento in objetivo:
                if hasattr(elemento, "recibir_daño"):
                    elemento.recibir_daño(self.daño)

        #Ejecuta la habilidad de regeneración
        elif self.tipo_habilidad == "regeneracion":
            self.curar(self.vida_maxima * 0.25)

        #Ejecuta la habilidad de intangibilidad
        elif self.tipo_habilidad == "intangibilidad":
            self.turnos_proteccion = 1
            self.estado = "protegida"

        #Evita ejecutar habilidades no reconocidas
        else:
            print("La habilidad no está implementada")
            return False

        #Activa la recarga de la habilidad
        self.turnos_recarga = self.recarga_habilidad
        return True

    def avanzar_turno(self):
        #Reduce la recarga de la habilidad
        if self.turnos_recarga > 0:
            self.turnos_recarga -= 1

        #Reduce los turnos restantes de protección
        if self.turnos_proteccion > 0:
            self.turnos_proteccion -= 1
            if self.turnos_proteccion == 0 and not self.esta_eliminada():
                self.estado = "activa"

        #Reduce los turnos restantes de congelamiento
        if self.turnos_congelada > 0:
            self.turnos_congelada -= 1
            if self.turnos_congelada == 0 and not self.esta_eliminada():
                self.estado = "activa"

        #Reduce los turnos restantes del aumento de movimiento
        if self.turnos_movimiento_extra > 0:
            self.turnos_movimiento_extra -= 1
            if self.turnos_movimiento_extra == 0:
                self.movimiento_extra = 0

    def congelar(self, turnos=1):
        #Comprueba que la cantidad de turnos sea válida
        if not isinstance(turnos, int) or turnos <= 0:
            print("Los turnos de congelamiento deben ser enteros positivos")
            return False

        #Impide congelar una unidad eliminada
        if self.esta_eliminada():
            return False

        #Aplica el estado de congelamiento
        self.turnos_congelada = turnos
        self.estado = "congelada"
        return True

    def esta_eliminada(self):
        #Retorna verdadero cuando la unidad no tiene vida
        return self.vida <= 0

    def cambiar_animacion(self, animacion):
        #Comprueba que la animación exista dentro del diccionario de sprites
        if animacion not in self.sprites:
            print(f"La animación {animacion} no existe para {self.nombre}")
            return False

        #Cambia la animación actual
        self.animacion_actual = animacion

        #Reinicia el índice para comenzar desde el primer frame
        self.indice_frame = 0
        return True

    def obtener_sprite_actual(self):
        #Obtiene la lista de frames de la animación actual
        frames = self.sprites.get(self.animacion_actual, [])

        #Comprueba que la animación tenga imágenes disponibles
        if not frames:
            return None

        #Retorna la ruta correspondiente al frame actual
        return frames[self.indice_frame]

    def avanzar_frame(self):
        #Obtiene la lista de frames de la animación actual
        frames = self.sprites.get(self.animacion_actual, [])

        #Comprueba que existan frames para avanzar
        if not frames:
            return None

        #Avanza al siguiente frame de la animación
        self.indice_frame += 1

        #Reinicia la animación cuando llega al último frame
        if self.indice_frame >= len(frames):
            self.indice_frame = 0

        #Retorna la ruta del nuevo frame
        return frames[self.indice_frame]

    def obtener_frames(self, animacion=None):
        #Usa la animación actual cuando no se especifica otra
        if animacion is None:
            animacion = self.animacion_actual

        #Retorna una copia de la lista para evitar modificaciones externas
        return self.sprites.get(animacion, []).copy()

    def reiniciar(self):
        #Restaura la vida completa de la unidad
        self.vida = self.vida_maxima
        #Elimina todos los efectos temporales
        self.turnos_recarga = 0
        self.turnos_proteccion = 0
        self.turnos_congelada = 0
        self.movimiento_extra = 0
        self.turnos_movimiento_extra = 0
        #Elimina la posición anterior
        self.posicion = None
        #Restaura el estado activo
        self.estado = "activa"

        #Regresa a la animación de espera
        self.animacion_actual = "idle"

        #Reinicia el frame actual
        self.indice_frame = 0

    def crear_copia(self):
        #Crea una unidad nueva e independiente usando esta unidad como plantilla
        copia = deepcopy(self)
        copia.reiniciar()
        return copia

    def obtener_informacion(self):
        #Retorna los datos actuales de la unidad
        return {
            "nombre": self.nombre,
            "faccion": self.faccion,
            "costo": self.costo,
            "vida": self.vida,
            "vida_maxima": self.vida_maxima,
            "daño": self.daño,
            "movimiento": self.movimiento,
            "movimiento_actual": self.obtener_movimiento_actual(),
            "habilidad": self.habilidad,
            "recarga_habilidad": self.recarga_habilidad,
            "turnos_recarga": self.turnos_recarga,
            "sprites": deepcopy(self.sprites),
            "animacion_actual": self.animacion_actual,
            "sprite_actual": self.obtener_sprite_actual(),
            "posicion": self.posicion,
            "estado": self.estado
        }

    def __str__(self):
        #Retorna una representación legible de la unidad
        return (
            f"{self.nombre} | Facción: {self.faccion} | "
            f"Vida: {self.vida}/{self.vida_maxima} | "
            f"Daño: {self.daño} | Movimiento: {self.obtener_movimiento_actual()}"
        )


class Faccion:
    def __init__(self, nombre, descripcion, unidades):
        #Guarda el nombre de la facción
        self.nombre = nombre
        #Guarda una descripción breve de la facción
        self.descripcion = descripcion
        #Guarda las plantillas de unidades disponibles
        self.unidades = unidades

    def listar_unidades(self):
        #Retorna los nombres de las unidades disponibles
        return list(self.unidades.keys())

    def obtener_plantilla(self, nombre_unidad):
        #Comprueba que la unidad exista dentro de la facción
        if nombre_unidad not in self.unidades:
            return None
        #Retorna la plantilla sin modificarla
        return self.unidades[nombre_unidad]

    def crear_unidad(self, nombre_unidad):
        #Busca la plantilla correspondiente
        plantilla = self.obtener_plantilla(nombre_unidad)

        #Comprueba que la unidad exista
        if plantilla is None:
            print(f"La unidad {nombre_unidad} no pertenece a {self.nombre}")
            return None

        #Retorna una copia nueva e independiente
        return plantilla.crear_copia()

    def obtener_informacion(self):
        #Retorna la información general de la facción
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "unidades": self.listar_unidades()
        }

    def __str__(self):
        #Retorna una representación legible de la facción
        return f"{self.nombre}: {', '.join(self.listar_unidades())}"


#Plantillas de la facción Humano
VALQUIRIA = Unidad(
    nombre="Valquiria",
    faccion="Humano",
    costo=180,
    vida=140,
    daño=55,
    movimiento=3,
    habilidad="Golpe doble",
    tipo_habilidad="ataque_doble",
    recarga_habilidad=1,
    sprites = {
        "idle": [
            "Sprites/Unidades/Humano/Valquiria/idle/idle1.png", 
            "Sprites/Unidades/Humano/Valquiria/idle/idle2.png",
            "Sprites/Unidades/Humano/Valquiria/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Humano/Valquiria/walking/walking1.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking2.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking3.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking4.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking5.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking6.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking7.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking8.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking9.png",
            "Sprites/Unidades/Humano/Valquiria/walking/walking10.png"
        ],
        "dying": [
            "Sprites/Unidades/Humano/Valquiria/dying/dying1.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying2.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying3.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying4.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying5.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying6.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying7.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying8.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying9.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying10.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying11.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying12.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying13.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying14.png",
            "Sprites/Unidades/Humano/Valquiria/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing1.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing2.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing3.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing4.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing5.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing6.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing7.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing8.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing9.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing10.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing11.png",
            "Sprites/Unidades/Humano/Valquiria/slashing/slashing12.png"
        ]
    }
)

MATON = Unidad(
    nombre="Matón",
    faccion="Humano",
    costo=220,
    vida=300,
    daño=80,
    movimiento=2,
    habilidad="Escudo resistente",
    tipo_habilidad="escudo",
    recarga_habilidad=2,
    sprites={
        "idle": [
            "Sprites/Unidades/Humano/Maton/idle/idle1.png",
            "Sprites/Unidades/Humano/Maton/idle/idle2.png",
            "Sprites/Unidades/Humano/Maton/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Humano/Maton/walking/walking1.png",
            "Sprites/Unidades/Humano/Maton/walking/walking2.png",
            "Sprites/Unidades/Humano/Maton/walking/walking3.png",
            "Sprites/Unidades/Humano/Maton/walking/walking4.png",
            "Sprites/Unidades/Humano/Maton/walking/walking5.png",
            "Sprites/Unidades/Humano/Maton/walking/walking6.png",
            "Sprites/Unidades/Humano/Maton/walking/walking7.png",
            "Sprites/Unidades/Humano/Maton/walking/walking8.png",
            "Sprites/Unidades/Humano/Maton/walking/walking9.png",
            "Sprites/Unidades/Humano/Maton/walking/walking10.png",
            "Sprites/Unidades/Humano/Maton/walking/walking11.png",
            "Sprites/Unidades/Humano/Maton/walking/walking12.png",
            "Sprites/Unidades/Humano/Maton/walking/walking13.png",
            "Sprites/Unidades/Humano/Maton/walking/walking14.png",
            "Sprites/Unidades/Humano/Maton/walking/walking15.png",
            "Sprites/Unidades/Humano/Maton/walking/walking16.png",
            "Sprites/Unidades/Humano/Maton/walking/walking17.png",
            "Sprites/Unidades/Humano/Maton/walking/walking18.png",
            "Sprites/Unidades/Humano/Maton/walking/walking19.png",
            "Sprites/Unidades/Humano/Maton/walking/walking20.png"
        ],
        "dying": [
            "Sprites/Unidades/Humano/Maton/dying/dying1.png",
            "Sprites/Unidades/Humano/Maton/dying/dying2.png",
            "Sprites/Unidades/Humano/Maton/dying/dying3.png",
            "Sprites/Unidades/Humano/Maton/dying/dying4.png",
            "Sprites/Unidades/Humano/Maton/dying/dying5.png",
            "Sprites/Unidades/Humano/Maton/dying/dying6.png",
            "Sprites/Unidades/Humano/Maton/dying/dying7.png",
            "Sprites/Unidades/Humano/Maton/dying/dying8.png",
            "Sprites/Unidades/Humano/Maton/dying/dying9.png",
            "Sprites/Unidades/Humano/Maton/dying/dying10.png"
        ],
        "slashing": [
            "Sprites/Unidades/Humano/Maton/slashing/slashing1.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing2.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing3.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing4.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing5.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing6.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing7.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing8.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing9.png",
            "Sprites/Unidades/Humano/Maton/slashing/slashing10.png"
        ]
    }
)

BANDIDO = Unidad(
    nombre="Bandido",
    faccion="Humano",
    costo=140,
    vida=95,
    daño=24,
    movimiento=5,
    habilidad="Huida veloz",
    tipo_habilidad="velocidad",
    recarga_habilidad=3,
    sprites={
        "idle": [
            "Sprites/Unidades/Humano/Bandido/idle/idle1.png",
            "Sprites/Unidades/Humano/Bandido/idle/idle2.png",
            "Sprites/Unidades/Humano/Bandido/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Humano/Bandido/walking/walking1.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking2.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking3.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking4.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking5.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking6.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking7.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking8.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking9.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking10.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking11.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking12.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking13.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking14.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking15.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking16.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking17.png",
            "Sprites/Unidades/Humano/Bandido/walking/walking18.png"
        ],
        "dying": [
            "Sprites/Unidades/Humano/Bandido/dying/dying1.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying2.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying3.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying4.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying5.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying6.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying7.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying8.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying9.png",
            "Sprites/Unidades/Humano/Bandido/dying/dying10.png"
        ],
        "slashing": [
            "Sprites/Unidades/Humano/Bandido/slashing/slashing1.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing2.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing3.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing4.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing5.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing6.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing7.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing8.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing9.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing10.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing11.png",
            "Sprites/Unidades/Humano/Bandido/slashing/slashing12.png"
        ]
    }
)

#Plantillas de la facción No muerto
ESQUELETO = Unidad(
    nombre="Esqueleto",
    faccion="No muerto",
    costo=130,
    vida=85,
    daño=30,
    movimiento=4,
    habilidad="Ataque doble",
    tipo_habilidad="ataque_doble",
    recarga_habilidad=3,
    sprites={
        "idle": [
            "Sprites/Unidades/No muerto/Esqueleto/idle/idle1.png",
            "Sprites/Unidades/No muerto/Esqueleto/idle/idle2.png",
            "Sprites/Unidades/No muerto/Esqueleto/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking1.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking2.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking3.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking4.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking5.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking6.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking7.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking8.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking9.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking10.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking11.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking12.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking13.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking14.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking15.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking16.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking17.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking18.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking19.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking20.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking21.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking22.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking23.png",
            "Sprites/Unidades/No muerto/Esqueleto/walking/walking24.png"
        ],
        "dying": [
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying1.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying2.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying3.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying4.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying5.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying6.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying7.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying8.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying9.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying10.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying11.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying12.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying13.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying14.png",
            "Sprites/Unidades/No muerto/Esqueleto/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing1.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing2.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing3.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing4.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing5.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing6.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing7.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing8.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing9.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing10.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing11.png",
            "Sprites/Unidades/No muerto/Esqueleto/slashing/slashing12.png"
        ]
    }
)

ZOMBIE = Unidad(
    nombre="Zombie",
    faccion="No muerto",
    costo=190,
    vida=240,
    daño=22,
    movimiento=2,
    habilidad="Regeneración",
    tipo_habilidad="regeneracion",
    recarga_habilidad=4,
    sprites={
        "idle": [
            "Sprites/Unidades/No muerto/Zombie/idle/idle1.png",
            "Sprites/Unidades/No muerto/Zombie/idle/idle2.png",
            "Sprites/Unidades/No muerto/Zombie/idle/idle3.png"
        ],
        "walking": [
           "Sprites/Unidades/No muerto/Zombie/walking/walking1.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking2.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking3.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking4.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking5.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking6.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking7.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking8.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking9.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking10.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking11.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking12.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking13.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking14.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking15.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking16.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking17.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking18.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking19.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking20.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking21.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking22.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking23.png",
            "Sprites/Unidades/No muerto/Zombie/walking/walking24.png"
        ],
        "dying": [
            "Sprites/Unidades/No muerto/Zombie/dying/dying1.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying2.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying3.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying4.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying5.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying6.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying7.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying8.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying9.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying10.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying11.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying12.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying13.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying14.png",
            "Sprites/Unidades/No muerto/Zombie/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing1.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing2.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing3.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing4.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing5.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing6.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing7.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing8.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing9.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing10.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing11.png",
            "Sprites/Unidades/No muerto/Zombie/slashing/slashing12.png"
        ]
    }
)

ESPECTRO = Unidad(
    nombre="Espectro",
    faccion="No muerto",
    costo=210,
    vida=110,
    daño=32,
    movimiento=5,
    habilidad="Intangibilidad",
    tipo_habilidad="intangibilidad",
    recarga_habilidad=4,
    sprites={
        "idle": [
            "Sprites/Unidades/No muerto/Espectro/idle/idle1.png",
            "Sprites/Unidades/No muerto/Espectro/idle/idle2.png",
            "Sprites/Unidades/No muerto/Espectro/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/No muerto/Espectro/walking/walking1.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking2.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking3.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking4.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking5.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking6.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking7.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking8.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking9.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking10.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking11.png",
            "Sprites/Unidades/No muerto/Espectro/walking/walking12.png"
        ],
        "dying": [
            "Sprites/Unidades/No muerto/Espectro/dying/dying1.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying2.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying3.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying4.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying5.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying6.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying7.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying8.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying9.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying10.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying11.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying12.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying13.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying14.png",
            "Sprites/Unidades/No muerto/Espectro/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing1.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing2.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing3.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing4.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing5.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing6.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing7.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing8.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing9.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing10.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing11.png",
            "Sprites/Unidades/No muerto/Espectro/slashing/slashing12.png"
        ]
    }
)

#Plantillas de la facción Leyenda
GOBLIN = Unidad(
    nombre="Goblin",
    faccion="Leyenda",
    costo=120,
    vida=80,
    daño=20,
    movimiento=6,
    habilidad="Carrera salvaje",
    tipo_habilidad="velocidad",
    recarga_habilidad=3,
    sprites={
        "idle": [
            "Sprites/Unidades/Leyenda/Goblin/idle/idle1.png",
            "Sprites/Unidades/Leyenda/Goblin/idle/idle2.png",
            "Sprites/Unidades/Leyenda/Goblin/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Leyenda/Goblin/walking/walking1.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking2.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking3.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking4.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking5.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking6.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking7.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking8.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking9.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking10.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking11.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking12.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking13.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking14.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking15.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking16.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking17.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking18.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking19.png",
            "Sprites/Unidades/Leyenda/Goblin/walking/walking20.png"
        ],
        "dying": [
            "Sprites/Unidades/Leyenda/Goblin/dying/dying1.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying2.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying3.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying4.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying5.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying6.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying7.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying8.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying9.png",
            "Sprites/Unidades/Leyenda/Goblin/dying/dying10.png"
        ],
        "slashing": [
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing1.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing2.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing3.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing4.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing5.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing6.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing7.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing8.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing9.png",
            "Sprites/Unidades/Leyenda/Goblin/slashing/slashing10.png"
        ]
    }
)

MINOTAURO = Unidad(
    nombre="Minotauro",
    faccion="Leyenda",
    costo=250,
    vida=210,
    daño=45,
    movimiento=3,
    habilidad="Embate en área",
    tipo_habilidad="daño_area",
    recarga_habilidad=4,
    sprites={
        "idle": [
            "Sprites/Unidades/Leyenda/Minotauro/idle/idle1.png",
            "Sprites/Unidades/Leyenda/Minotauro/idle/idle2.png",
            "Sprites/Unidades/Leyenda/Minotauro/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking1.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking2.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking3.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking4.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking5.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking6.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking7.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking8.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking9.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking10.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking11.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking12.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking13.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking14.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking15.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking16.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking17.png",
            "Sprites/Unidades/Leyenda/Minotauro/walking/walking18.png"
        ],
        "dying": [
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying1.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying2.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying3.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying4.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying5.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying6.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying7.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying8.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying9.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying10.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying11.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying12.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying13.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying14.png",
            "Sprites/Unidades/Leyenda/Minotauro/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing1.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing2.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing3.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing4.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing5.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing6.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing7.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing8.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing9.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing10.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing11.png",
            "Sprites/Unidades/Leyenda/Minotauro/slashing/slashing12.png"
        ]
    }
)

GOLEM = Unidad(
    nombre="Golem",
    faccion="Leyenda",
    costo=280,
    vida=300,
    daño=30,
    movimiento=1,
    habilidad="Armadura de piedra",
    tipo_habilidad="escudo",
    recarga_habilidad=4,
    sprites={
        "idle": [
            "Sprites/Unidades/Leyenda/Golem/idle/idle1.png",
            "Sprites/Unidades/Leyenda/Golem/idle/idle2.png",
            "Sprites/Unidades/Leyenda/Golem/idle/idle3.png"
        ],
        "walking": [
            "Sprites/Unidades/Leyenda/Golem/walking/walking1.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking2.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking3.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking4.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking5.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking6.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking7.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking8.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking9.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking10.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking11.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking12.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking13.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking14.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking15.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking16.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking17.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking18.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking19.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking20.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking21.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking22.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking23.png",
            "Sprites/Unidades/Leyenda/Golem/walking/walking24.png"
        ],
        "dying": [
            "Sprites/Unidades/Leyenda/Golem/dying/dying1.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying2.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying3.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying4.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying5.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying6.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying7.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying8.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying9.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying10.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying11.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying12.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying13.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying14.png",
            "Sprites/Unidades/Leyenda/Golem/dying/dying15.png"
        ],
        "slashing": [
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing1.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing2.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing3.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing4.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing5.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing6.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing7.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing8.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing9.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing10.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing11.png",
            "Sprites/Unidades/Leyenda/Golem/slashing/slashing12.png"
        ]
    }
)

#Catálogo general de facciones disponibles
FACCIONES = {
    "Humano": Faccion(
        nombre="Humano",
        descripcion="Unidades equilibradas con buena resistencia y velocidad.",
        unidades={
            "Valquiria": VALQUIRIA,
            "Matón": MATON,
            "Bandido": BANDIDO
        }
    ),
    "No muerto": Faccion(
        nombre="No muerto",
        descripcion="Unidades resistentes con habilidades de recuperación y evasión.",
        unidades={
            "Esqueleto": ESQUELETO,
            "Zombie": ZOMBIE,
            "Espectro": ESPECTRO
        }
    ),
    "Leyenda": Faccion(
        nombre="Leyenda",
        descripcion="Criaturas fantásticas con características muy marcadas.",
        unidades={
            "Goblin": GOBLIN,
            "Minotauro": MINOTAURO,
            "Golem": GOLEM
        }
    )
}


def obtener_faccion(nombre_faccion):
    #Busca una facción por su nombre exacto
    return FACCIONES.get(nombre_faccion)


def listar_facciones():
    #Retorna los nombres de todas las facciones disponibles
    return list(FACCIONES.keys())