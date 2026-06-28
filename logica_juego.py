# Logica Castle-FLesh

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional
import os

#  INTEGRACIÓN CON gestion.py

try:
    from gestion import Gestion
    _gestion = Gestion()          # instancia compartida del módulo
except ImportError:
    _gestion = None               # permite pruebas sin el archivo


#  FACCIONES VÁLIDAS Y SUS UNIDADES

FACCIONES_VALIDAS = {
    "Humano":    ["Bandido", "Matón", "Valquiria"],
    "Leyenda":   ["Goblin", "Golem", "Minotauro"],
    "No Muerto": ["Espectro", "Esqueleto", "Zombie"],
}

# Ruta base de sprites
def ruta_sprite(faccion: str, unidad: str, animacion: str, frame: int) -> str:
    return f"Sprites/{faccion}/{unidad}/{animacion}/{animacion}{frame}.png"


#  ECONOMÍA

DINERO_INICIAL_DEFENSOR = 200
DINERO_INICIAL_ATACANTE = 200
DINERO_BONO_POR_RONDA   = 50    # extra por cada ronda adicional
RONDAS_PARA_GANAR       = 3

# Recompensas de combate
RECOMPENSA_UNIDAD_ELIMINADA  = 15   # monedas que gana el defensor por kill
RECOMPENSA_DAÑO_TORRE        = 5    # monedas atacante por daño a torre
RECOMPENSA_TORRE_DESTRUIDA   = 20   # monedas atacante por destruir torre
RECOMPENSA_DAÑO_BASE         = 10   # monedas atacante por daño a base
BONO_DAÑO_DIVISOR            = 10   # cada N puntos de daño anterior → 5 monedas extra
BONO_DAÑO_VALOR              = 5
BONO_DAÑO_TOPE               = 100


#  ENUMS

class Fase(Enum):
    CONSTRUCCION = auto()   # defensor coloca torres y muros
    DESPLIEGUE   = auto()   # atacante coloca unidades
    COMBATE      = auto()   # fase automática de batalla
    FIN_RONDA    = auto()   # resumen de ronda
    FIN_PARTIDA  = auto()   # alguien ganó 3 rondas

class ResultadoRonda(Enum):
    DEFENSOR_GANA = auto()
    ATACANTE_GANA = auto()

class Rol(Enum):
    DEFENSOR = "defensor"
    ATACANTE  = "atacante"


#  DATOS DE RESULTADO DE COMBATE
#  (lo llena el módulo de combate de Jocsan)

@dataclass
class ResultadoCombate:
    unidades_eliminadas: int  = 0
    daño_a_torres:       int  = 0
    torres_destruidas:   int  = 0
    daño_a_base:         int  = 0
    base_destruida:      bool = False
    log:                 list = field(default_factory=list)


#  RESUMEN DE RONDA (para callbacks de UI)

@dataclass
class ResumenRonda:
    numero:           int
    resultado:        ResultadoRonda
    ganador_nombre:   str
    dinero_def_inicio: int
    dinero_atk_inicio: int
    dinero_def_fin:    int
    dinero_atk_fin:    int
    combate:          Optional[ResultadoCombate] = None


#  JUGADOR EN PARTIDA

class JugadorPartida:
    """
    Representa a un jugador dentro de una partida activa.
    Se construye con los datos devueltos por Gestion.info_jugador().
    """

    def __init__(self, nombre: str, faccion: str, rol: Rol):
        self.nombre          = nombre
        self.faccion         = faccion     # "Humano" | "Leyenda" | "No Muerto"
        self.rol             = rol
        self.dinero          = 0
        self.rondas_ganadas  = 0
        self.daño_ronda_ant  = 0           # daño hecho en ronda anterior (atacante)

        # Listas que llenará el módulo de estructuras/unidades del compañero
        self.torres:   list = []
        self.muros:    list = []
        self.unidades: list = []           # instancias de Unidad activas

    #  Economía 
    def puede_comprar(self, costo: int) -> bool:
        return self.dinero >= costo

    def gastar(self, costo: int) -> bool:
        if not self.puede_comprar(costo):
            return False
        self.dinero -= costo
        return True

    def recibir_monedas(self, cantidad: int):
        self.dinero += max(0, int(cantidad))

    #  Unidades vivas 
    def unidades_vivas(self) -> list:
        """
        Usa el método esta_eliminada() de la clase Unidad del compañero.
        Si las unidades no tienen ese método, filtra por vida > 0.
        """
        resultado = []
        for u in self.unidades:
            if hasattr(u, "esta_eliminada"):
                if not u.esta_eliminada():
                    resultado.append(u)
            elif hasattr(u, "vida"):
                if u.vida > 0:
                    resultado.append(u)
        return resultado

    def __str__(self):
        return (
            f"{self.nombre} [{self.rol.value.upper()}] "
            f"| {self.faccion} "
            f"| 💰 {self.dinero} "
            f"| Rondas: {self.rondas_ganadas}"
        )


#  MOTOR DE JUEGO

class MotorJuego:
    """
    Controla: rondas, fases, economía, condiciones de victoria
    y persistencia de victorias en jugadores.json via Gestion.

    Callbacks que recibe la GUI:
      fn_cambio_fase(fase: Fase)
      fn_fin_ronda(resumen: ResumenRonda)
      fn_fin_partida(ganador: JugadorPartida)
      fn_actualizar_dinero(defensor_dinero, atacante_dinero)
    """

    def __init__(
        self,
        defensor: JugadorPartida,
        atacante:  JugadorPartida,
        fn_combate:          Callable[[JugadorPartida, JugadorPartida], ResultadoCombate],
        fn_cambio_fase:      Optional[Callable] = None,
        fn_fin_ronda:        Optional[Callable] = None,
        fn_fin_partida:      Optional[Callable] = None,
        fn_actualizar_dinero:Optional[Callable] = None,
    ):
        self.defensor = defensor
        self.atacante  = atacante

        self._fn_combate       = fn_combate
        self._cb_fase          = fn_cambio_fase       or (lambda f: None)
        self._cb_fin_ronda     = fn_fin_ronda         or (lambda r: None)
        self._cb_fin_partida   = fn_fin_partida       or (lambda g: None)
        self._cb_dinero        = fn_actualizar_dinero or (lambda d, a: None)

        self.ronda_actual = 0
        self.fase_actual: Optional[Fase] = None
        self.historial:   list[ResumenRonda] = []
        self.ganador:     Optional[JugadorPartida] = None
        self._activo      = False

    #  Arranque 
    def iniciar_partida(self):
        self._activo = True
        self._nueva_ronda()

    #  Ronda 
    def _nueva_ronda(self):
        self.ronda_actual += 1

        # Limpiar unidades y estructuras de la ronda anterior
        self.defensor.torres   = []
        self.defensor.muros    = []
        self.atacante.unidades = []

        self._distribuir_dinero()
        self._cambiar_fase(Fase.CONSTRUCCION)

    def _distribuir_dinero(self):
        bono = (self.ronda_actual - 1) * DINERO_BONO_POR_RONDA

        # Bono extra atacante por daño de ronda anterior
        bono_daño = min(
            (self.atacante.daño_ronda_ant // BONO_DAÑO_DIVISOR) * BONO_DAÑO_VALOR,
            BONO_DAÑO_TOPE
        )

        self.defensor.dinero = DINERO_INICIAL_DEFENSOR + bono
        self.atacante.dinero  = DINERO_INICIAL_ATACANTE  + bono + bono_daño

        self._cb_dinero(self.defensor.dinero, self.atacante.dinero)

    def _cambiar_fase(self, fase: Fase):
        self.fase_actual = fase
        self._cb_fase(fase)

    #  Avances de fase (llamados por la GUI) 
    def confirmar_construccion(self):
        """Defensor terminó de construir → pasa al despliegue."""
        if self.fase_actual != Fase.CONSTRUCCION:
            return False
        self._cambiar_fase(Fase.DESPLIEGUE)
        return True

    def confirmar_despliegue(self):
        """Atacante terminó de colocar unidades → ejecuta combate."""
        if self.fase_actual != Fase.DESPLIEGUE:
            return False
        self._cambiar_fase(Fase.COMBATE)
        self._ejecutar_combate()
        return True

    def siguiente_ronda(self):
        """Llamado por la GUI tras mostrar el resumen de ronda."""
        if self.fase_actual != Fase.FIN_RONDA:
            return False
        ganador = self._verificar_ganador()
        if ganador:
            self.ganador = ganador
            self._activo = False
            self._cambiar_fase(Fase.FIN_PARTIDA)
            self._guardar_victoria(ganador)
            self._cb_fin_partida(ganador)
        else:
            self._nueva_ronda()
        return True

    #  Combate 
    def _ejecutar_combate(self):
        combate = self._fn_combate(self.defensor, self.atacante)
        self._procesar_combate(combate)

    def _procesar_combate(self, c: ResultadoCombate):
        # Monedas para el defensor por kills
        mon_def = c.unidades_eliminadas * RECOMPENSA_UNIDAD_ELIMINADA
        # Monedas para el atacante por daño
        mon_atk = (
            c.daño_a_torres      // RECOMPENSA_DAÑO_TORRE     +
            c.torres_destruidas  *  RECOMPENSA_TORRE_DESTRUIDA +
            c.daño_a_base        // RECOMPENSA_DAÑO_BASE
        )

        self.defensor.recibir_monedas(mon_def)
        self.atacante.recibir_monedas(mon_atk)
        self._cb_dinero(self.defensor.dinero, self.atacante.dinero)

        # Guardar daño para bono de próxima ronda
        self.atacante.daño_ronda_ant = c.daño_a_base + c.daño_a_torres

        resultado = self._determinar_resultado(c)
        self._registrar_ronda(resultado, c, mon_def, mon_atk)
        self._cambiar_fase(Fase.FIN_RONDA)

    def _determinar_resultado(self, c: ResultadoCombate) -> ResultadoRonda:
        if c.base_destruida:
            return ResultadoRonda.ATACANTE_GANA

        vivas = self.atacante.unidades_vivas()
        sin_recursos = self.atacante.dinero <= 0 and len(vivas) == 0

        if len(vivas) == 0 or sin_recursos:
            return ResultadoRonda.DEFENSOR_GANA

        return ResultadoRonda.DEFENSOR_GANA   # tiempo agotado → defensor gana

    def _registrar_ronda(
        self, resultado: ResultadoRonda, c: ResultadoCombate,
        mon_def: int, mon_atk: int
    ):
        if resultado == ResultadoRonda.DEFENSOR_GANA:
            self.defensor.rondas_ganadas += 1
            nombre_ganador = self.defensor.nombre
        else:
            self.atacante.rondas_ganadas += 1
            nombre_ganador = self.atacante.nombre

        resumen = ResumenRonda(
            numero=self.ronda_actual,
            resultado=resultado,
            ganador_nombre=nombre_ganador,
            dinero_def_inicio=DINERO_INICIAL_DEFENSOR,
            dinero_atk_inicio=DINERO_INICIAL_ATACANTE,
            dinero_def_fin=self.defensor.dinero,
            dinero_atk_fin=self.atacante.dinero,
            combate=c,
        )
        self.historial.append(resumen)
        self._cb_fin_ronda(resumen)

    #  Victoria 
    def _verificar_ganador(self) -> Optional[JugadorPartida]:
        if self.defensor.rondas_ganadas >= RONDAS_PARA_GANAR:
            return self.defensor
        if self.atacante.rondas_ganadas >= RONDAS_PARA_GANAR:
            return self.atacante
        return None

    def _guardar_victoria(self, ganador: JugadorPartida):
        """Usa Gestion.sumar_victorias() para actualizar jugadores.json."""
        if _gestion is None:
            return
        try:
            _gestion.sumar_victorias(ganador.nombre, ganador.rol.value)
        except Exception as e:
            print(f"[Motor] Error guardando victoria: {e}")

    #Compras (llamadas por la GUI en tiempo real) 
    def comprar_torre(self, costo: int) -> bool:
        if self.fase_actual != Fase.CONSTRUCCION:
            return False
        ok = self.defensor.gastar(costo)
        if ok:
            self._cb_dinero(self.defensor.dinero, self.atacante.dinero)
        return ok

    def comprar_muro(self, costo: int) -> bool:
        if self.fase_actual != Fase.CONSTRUCCION:
            return False
        ok = self.defensor.gastar(costo)
        if ok:
            self._cb_dinero(self.defensor.dinero, self.atacante.dinero)
        return ok

    def comprar_unidad(self, costo: int) -> bool:
        if self.fase_actual != Fase.DESPLIEGUE:
            return False
        ok = self.atacante.gastar(costo)
        if ok:
            self._cb_dinero(self.defensor.dinero, self.atacante.dinero)
        return ok

    #  Estado para la GUI 
    @property
    def estado(self) -> dict:
        return {
            "ronda":           self.ronda_actual,
            "fase":            self.fase_actual.name if self.fase_actual else None,
            "defensor": {
                "nombre":      self.defensor.nombre,
                "faccion":     self.defensor.faccion,
                "dinero":      self.defensor.dinero,
                "victorias":   self.defensor.rondas_ganadas,
            },
            "atacante": {
                "nombre":      self.atacante.nombre,
                "faccion":     self.atacante.faccion,
                "dinero":      self.atacante.dinero,
                "victorias":   self.atacante.rondas_ganadas,
            },
            "rondas_para_ganar": RONDAS_PARA_GANAR,
            "historial": [
                {"ronda": r.numero, "ganador": r.ganador_nombre}
                for r in self.historial
            ],
        }

    def __str__(self):
        e = self.estado
        return (
            f"Ronda {e['ronda']} | {e['fase']}\n"
            f"  {self.defensor}\n"
            f"  {self.atacante}"
        )



#  FÁBRICA  (conecta login con la partida)

def crear_partida(
    datos_j1: dict,
    datos_j2: dict,
    fn_combate: Callable,
    **callbacks
) -> MotorJuego:
    """
    datos_j1 / datos_j2:
        dict con claves 'nombre' y 'faccion'
        (los mismos que maneja menu_gui.py tras el login)

    Ejemplo en menu_gui.py:
        from logica_juego import crear_partida, ResultadoCombate

        def mi_combate(defensor, atacante):
            return ResultadoCombate(base_destruida=False, ...)

        motor = crear_partida(
            jugador1, jugador2,
            fn_combate=mi_combate,
            fn_cambio_fase=actualizar_fase_ui,
            fn_fin_ronda=mostrar_resumen,
            fn_fin_partida=mostrar_ganador,
            fn_actualizar_dinero=actualizar_hud,
        )
        motor.iniciar_partida()
    """
    defensor = JugadorPartida(
        nombre  = datos_j1["nombre"],
        faccion = datos_j1["faccion"],
        rol     = Rol.DEFENSOR,
    )
    atacante = JugadorPartida(
        nombre  = datos_j2["nombre"],
        faccion = datos_j2["faccion"],
        rol     = Rol.ATACANTE,
    )
    return MotorJuego(defensor, atacante, fn_combate, **callbacks)



#  PRUEBA RÁPIDA

if __name__ == "__main__":
    turno = 0

    def combate_demo(defensor, atacante):
        global turno
        turno += 1
        if turno < 3:
            return ResultadoCombate(unidades_eliminadas=2, daño_a_torres=10)
        return ResultadoCombate(base_destruida=True, daño_a_base=50)

    motor = crear_partida(
        {"nombre": "Ana",   "faccion": "Humano"},
        {"nombre": "Bruno", "faccion": "No Muerto"},
        fn_combate      = combate_demo,
        fn_cambio_fase  = lambda f: print(f"  ▶ {f.name}"),
        fn_fin_ronda    = lambda r: print(f"  ✔ Ronda {r.numero} → {r.ganador_nombre}"),
        fn_fin_partida  = lambda g: print(f"\n🏆 Ganador: {g.nombre} ({g.rol.value})"),
    )

    motor.iniciar_partida()
    for _ in range(12):
        if   motor.fase_actual == Fase.CONSTRUCCION: motor.confirmar_construccion()
        elif motor.fase_actual == Fase.DESPLIEGUE:   motor.confirmar_despliegue()
        elif motor.fase_actual == Fase.FIN_RONDA:    motor.siguiente_ronda()
        elif motor.fase_actual == Fase.FIN_PARTIDA:  break
