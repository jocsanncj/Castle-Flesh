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
    daño=35,
    movimiento=3,
    habilidad="Golpe doble",
    tipo_habilidad="ataque_doble",
    recarga_habilidad=3,
    sprites={