from copy import deepcopy #Librería para crear copias de una tropa

ESTADOS = ("activa", "eliminaada", "congelada", "protegida")

class Unidad:
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
        recarga,
        sprite
    ):
        self.nombre = nombre
        self.faccion = faccion
        self.costo = costo
        self.vida_maxima = vida
        self.vida = vida
        self.daño = daño
        self.movimiento = movimiento
        self.habilidad = habilidad
        self.tipo_habilidad = tipo_habilidad
        self.recarga = recarga
        self.sprite = sprite
        self.turnos_recarga = 0
        self.estado = "activa"
        self.posicion = None
        self.mov_extra = 0
        self.turnos_mov_extra = 0
        self.turnos_protecc = 0
        self.turnos_congelada = 0

    def recibir_daño(self, cantidad):
        if not isinstance(cantidad, (int, float)):
            print("La cantidad de daño debe ser numérica")
            return False
        
        if cantidad < 0:
            print("El daño no puede ser negativo")
            return False
        

        if self.turnos_protecc > 0:
            cantidad = cantidad / 2
        
        self.vida -= cantidad

        if self.vida <= 0:
            self.vida = 0
            self.estado = "eliminado"

        return True
    
    def curar (self, cantidad):
        if not isinstance(cantidad, (int, float)):
            print("La cantidad de curación debe ser numérica")
            return False
        
        if cantidad <= 0:
            print("La curación debe ser mayor que cero")
            return False
        
        if self.esta_eliminada():
            print("No se puede curar una tropa eliminada")
            return False
        
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
