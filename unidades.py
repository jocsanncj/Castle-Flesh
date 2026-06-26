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