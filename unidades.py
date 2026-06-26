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
    
    