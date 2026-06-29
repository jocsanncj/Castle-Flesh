from copy import deepcopy


class Edificio:
    #Facciones disponibles para la apariencia visual
    FACCIONES_VALIDAS = ("Humano", "No muerto", "Leyenda")

    def __init__(self, nombre, costo, vida, sprites_por_faccion):
        #Guarda los datos generales del edificio
        self.nombre = nombre
        self.costo = costo
        self.vida_maxima = vida
        self.vida = vida
        self.posicion = None
        self.estado = "entero"
        self.faccion_visual = None
        self.sprites_por_faccion = sprites_por_faccion

    def seleccionar_faccion_visual(self, faccion):
        #Comprueba que la facción exista
        if faccion not in self.FACCIONES_VALIDAS:
            print("La facción debe ser Humano, No muerto o Leyenda")
            return False

        #Comprueba que existan sprites para esa facción
        if faccion not in self.sprites_por_faccion:
            print(f"No existen sprites para la facción {faccion}")
            return False

        self.faccion_visual = faccion
        return True

    def colocar(self, posicion):
        #Comprueba que la posición tenga el formato correcto
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            print("La posición debe tener el formato (fila, columna)")
            return False

        self.posicion = posicion
        return True

    def recibir_daño(self, cantidad):
        #Comprueba que el daño sea válido
        if not isinstance(cantidad, (int, float)) or cantidad < 0:
            print("El daño debe ser un número positivo")
            return False

        #Evita dañar una estructura destruida
        if self.esta_destruido():
            return False

        self.vida -= cantidad
        self.actualizar_estado()
        return True

    def actualizar_estado(self):
        #Actualiza el estado general del edificio
        if self.vida <= 0:
            self.vida = 0
            self.estado = "destruido"
        else:
            self.estado = "entero"

    def obtener_sprite_actual(self):
        #Retorna el sprite correspondiente a la facción y al estado
        if self.faccion_visual is None:
            return None

        sprites = self.sprites_por_faccion.get(self.faccion_visual, {})
        return sprites.get(self.estado)

    def esta_destruido(self):
        #Retorna verdadero cuando la vida llega a cero
        return self.vida <= 0

    def reiniciar(self):
        #Restaura los datos principales
        self.vida = self.vida_maxima
        self.posicion = None
        self.estado = "entero"

    def crear_copia(self):
        #Crea una copia independiente de la plantilla
        copia = deepcopy(self)
        copia.reiniciar()
        return copia


class Torre(Edificio):
    def __init__(
        self,
        nombre,
        costo,
        vida,
        daño,
        alcance,
        velocidad_ataque,
        habilidad,
        tipo_habilidad,
        recarga_habilidad,
        sprites_por_faccion,
        sprite_proyectil
    ):
        #Inicializa los atributos generales
        super().__init__(nombre, costo, vida, sprites_por_faccion)

        #Guarda los atributos propios de una torre
        self.daño = daño
        self.alcance = alcance
        self.velocidad_ataque = velocidad_ataque
        self.ataques_restantes = velocidad_ataque
        self.habilidad = habilidad
        self.tipo_habilidad = tipo_habilidad
        self.recarga_habilidad = recarga_habilidad
        self.turnos_recarga = 0

        #Guarda un único sprite de proyectil
        self.sprite_proyectil = sprite_proyectil

    def atacar(self, objetivo):
        #Comprueba que la torre pueda atacar
        if self.esta_destruido() or self.ataques_restantes <= 0:
            return False

        #Comprueba que el objetivo pueda recibir daño
        if not hasattr(objetivo, "recibir_daño"):
            return False

        objetivo.recibir_daño(self.daño)
        self.ataques_restantes -= 1
        return True

    def usar_habilidad(self, objetivo):
        #Comprueba que la habilidad esté disponible
        if self.turnos_recarga > 0 or self.esta_destruido():
            return False

        #Comprueba que el objetivo pueda recibir daño
        if not hasattr(objetivo, "recibir_daño"):
            return False

        #Habilidad de la torre de magos
        if self.tipo_habilidad == "daño_magico":
            objetivo.recibir_daño(self.daño * 1.5)

        #Habilidad de la torre de arqueras
        elif self.tipo_habilidad == "rafaga_flechas":
            for _ in range(3):
                objetivo.recibir_daño(self.daño * 0.6)

        #Habilidad del cañón
        elif self.tipo_habilidad == "disparo_explosivo":
            objetivo.recibir_daño(self.daño * 1.75)

        else:
            return False

        self.turnos_recarga = self.recarga_habilidad
        return True

    def avanzar_turno(self):
        #Reduce la recarga
        if self.turnos_recarga > 0:
            self.turnos_recarga -= 1

        #Restaura los ataques disponibles
        self.ataques_restantes = self.velocidad_ataque

    def reiniciar(self):
        #Reinicia los datos generales y ofensivos
        super().reiniciar()
        self.ataques_restantes = self.velocidad_ataque
        self.turnos_recarga = 0


class Muro(Edificio):
    #El muro utiliza únicamente la lógica general de Edificio
    pass


class TorreCentral(Edificio):
    def __init__(self, nombre, vida, posicion_fija, sprites_por_faccion):
        #Inicializa la torre central sin costo
        super().__init__(nombre, 0, vida, sprites_por_faccion)

        self.posicion_fija = posicion_fija
        self.posicion = posicion_fija

    def actualizar_estado(self):
        #La torre central tiene tres estados visuales
        if self.vida <= 0:
            self.vida = 0
            self.estado = "destruido"
        elif self.vida <= self.vida_maxima * 0.5:
            self.estado = "dañado"
        else:
            self.estado = "entero"

    def colocar(self, posicion):
        #Impide mover la torre central
        if posicion != self.posicion_fija:
            print("La torre central tiene una posición fija")
            return False

        self.posicion = self.posicion_fija
        return True

    def reiniciar(self):
        #Restaura la torre central
        super().reiniciar()
        self.posicion = self.posicion_fija


#Sprites de la Torre de Magos
SPRITES_TORRE_MAGOS = {
    "Humano": {
        "Sprites/Defensas/Humano/Torre de magos/full.png": None
    },
    "No muerto": {
        "Sprites/Defensas/No muerto/Torre de magos/full.png": None
    },
    "Leyenda": {
        "Sprites/Defensas/Leyenda/Torre de magos/full.png": None
    }
}


#Sprites de la Torre de Arqueras
SPRITES_TORRE_ARQUERAS = {
    "Humano": {
        "Sprites/Defensas/Humano/Torre de arqueros/full.png": None
        
    },
    "No muerto": {
        "Sprites/Defensas/No muerto/Torre de arqueros/full.png": None
        
    },
    "Leyenda": {
        "Sprites/Defensas/Leyenda/Torre de arqueros/full.png": None
        
    }
}


#Sprites del Cañón
SPRITES_CANON = {
    "Humano": {
        "Sprites/Defensas/Humano/Cañón/full.png": None,
        "Sprites/Defensas/Humano/Cañón/destroyed.png": None
    },
    "No muerto": {
        "Sprites/Defensas/No muerto/Cañón/full.png": None,
        "Sprites/Defensas/No muerto/Cañón/destroyed.png": None
    },
    "Leyenda": {
        "Sprites/Defensas/Leyenda/Cañón/full.png": None,
        "Sprites/Defensas/Leyenda/Cañón/destroyed.png": None
    }
}


#Sprites del Muro
SPRITES_MURO = {
    "Humano": {
        "Sprites/Defensas/Humano/Muro/full.png": None,
        "Sprites/Defensas/Humano/Muro/broken.png": None
    },
    "No muerto": {
        "Sprites/Defensas/Humano/Muro/full.png": None,
        "Sprites/Defensas/Humano/Muro/broken.png": None
    },
    "Leyenda": {
        "Sprites/Defensas/Humano/Muro/full.png": None,
        "Sprites/Defensas/Humano/Muro/broken.png": None
    }
}


#Sprites de la Torre Central
SPRITES_TORRE_CENTRAL = {
    "Humano": {
        "Sprites/Torres/Humano/full.png": None,
        "Sprites/Torres/Humano/damaged.png": None,
        "Sprites/Torres/Humano/destroyed.png": None
    },
    "No muerto": {
        "entero": None,
        "dañado": None,
        "destruido": None
    },
    "Leyenda": {
        "Sprites/Torres/No muerto/full.png": None,
        "Sprites/Torres/No muerto/damaged.png": None,
        "Sprites/Torres/No muerto/destroyed.png": None
    }
}


#Plantilla de la Torre de Magos
TORRE_MAGOS = Torre(
    nombre="Torre de Magos",
    costo=230,
    vida=180,
    daño=48,
    alcance=5,
    velocidad_ataque=1,
    habilidad="Ataque mágico",
    tipo_habilidad="daño_magico",
    recarga_habilidad=3,
    sprites_por_faccion=SPRITES_TORRE_MAGOS,
    sprite_proyectil="Sprites/Defensas/Humano/Torre de magos/fireball.png"

)


#Plantilla de la Torre de Arqueras
TORRE_ARQUERAS = Torre(
    nombre="Torre de Arqueras",
    costo=170,
    vida=150,
    daño=24,
    alcance=5,
    velocidad_ataque=2,
    habilidad="Ráfaga de flechas",
    tipo_habilidad="rafaga_flechas",
    recarga_habilidad=3,
    sprites_por_faccion=SPRITES_TORRE_ARQUERAS,
    sprite_proyectil= "Sprites/Defensas/Humano/Torre de arqueros/arrow.png"
    
)


#Plantilla del Cañón
CANON = Torre(
    nombre="Cañón",
    costo=220,
    vida=220,
    daño=60,
    alcance=4,
    velocidad_ataque=1,
    habilidad="Disparo explosivo",
    tipo_habilidad="disparo_explosivo",
    recarga_habilidad=3,
    sprites_por_faccion=SPRITES_CANON,
    sprite_proyectil="Sprites/Defensas/Humano/Cañón/cannonball.png"
)


#Plantilla del Muro
MURO = Muro(
    nombre="Muro",
    costo=80,
    vida=280,
    sprites_por_faccion=SPRITES_MURO
)


#Plantilla de la Torre Central
TORRE_CENTRAL = TorreCentral(
    nombre="Torre Central",
    vida=1000,
    posicion_fija=(5, 5),
    sprites_por_faccion=SPRITES_TORRE_CENTRAL
)


#Catálogo de las tres defensas
TORRES = {
    "Torre de Magos": TORRE_MAGOS,
    "Torre de Arqueras": TORRE_ARQUERAS,
    "Cañón": CANON
}


def listar_torres():
    #Retorna los nombres de las defensas
    return list(TORRES.keys())


def crear_torre(nombre_torre, faccion):
    #Busca la plantilla
    plantilla = TORRES.get(nombre_torre)

    if plantilla is None:
        print(f"La torre {nombre_torre} no existe")
        return None

    #Crea una copia independiente
    torre = plantilla.crear_copia()

    #Asigna la apariencia de la facción
    if not torre.seleccionar_faccion_visual(faccion):
        return None

    return torre


def crear_muro(faccion):
    #Crea un muro independiente
    muro = MURO.crear_copia()

    if not muro.seleccionar_faccion_visual(faccion):
        return None

    return muro


def crear_torre_central(faccion):
    #Crea una torre central independiente
    torre = TORRE_CENTRAL.crear_copia()

    if not torre.seleccionar_faccion_visual(faccion):
        return None

    return torre