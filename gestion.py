import json
import os

class Gestion:
    def __init__(self, archivo="jugadores.json"):
        self.archivo = archivo
        self.jugadores = self.cargar_jugadores()

    def cargar_jugadores(self):
        if not os.path.exists(self.archivo):
            return {}                                    # FIX: retornaba None

        try:
            with open(self.archivo, "r", encoding="utf-8") as archivo:   # FIX: "uft-8" → "utf-8"
                return json.load(archivo)

        except json.JSONDecodeError:
            print("El archivo .json está vacío")
            return {}

        except OSError:
            print("No es posible ejecutar el archivo")
            return {}

    def guardar_jugador(self):
        try:
            with open(self.archivo, "w", encoding="utf-8") as archivo:
                json.dump(self.jugadores, archivo, indent=4, ensure_ascii=False)
        except OSError:
            print("No fue posible guardar a los jugadores")

    def registrar_usuario(self, usuario, contraseña):
        usuario = usuario.strip()

        if usuario == "" or contraseña == "":
            print("Coloque un nombre de usuario y contraseña válidos")
            return False

        if usuario in self.jugadores:
            print("Este usuario ya se encuentra registrado")
            return False

        self.jugadores[usuario] = {
            "contraseña": contraseña,
            "victorias_defensor": 0,
            "victorias_atacante": 0
        }
        self.guardar_jugador()
        print("Usuario registrado correctamente")
        return True

    def iniciar_sesion(self, usuario, contraseña):
        usuario = usuario.strip()

        if usuario not in self.jugadores:
            print("El usuario no se encuentra registrado")
            return False

        if self.jugadores[usuario]["contraseña"] != contraseña:
            print("Contraseña incorrecta. Inténtelo de nuevo.")
            return False

        print("Sesión iniciada correctamente")
        return True

    def info_jugador(self, usuario):
        if usuario not in self.jugadores:
            return None
        return self.jugadores[usuario]

    def sumar_victorias(self, usuario, rol):
        if usuario not in self.jugadores:
            print("Jugador no existente")
            return False

        rol = rol.lower().strip()

        if rol == "defensor":
            self.jugadores[usuario]["victorias_defensor"] += 1

        elif rol == "atacante":
            self.jugadores[usuario]["victorias_atacante"] += 1   # FIX: "victoias" → "victorias"

        else:
            print("El rol no es válido")
            return False

        self.guardar_jugador()
        print(f"Victoria como {rol} agregada a {usuario} correctamente")
        return True                                               # FIX: faltaba return True

    def top_defensores(self):
        lista = list(self.jugadores.items())
        lista.sort(key=lambda j: j[1]["victorias_defensor"], reverse=True)
        return lista[:5]

    def top_atacantes(self):
        lista = list(self.jugadores.items())
        lista.sort(key=lambda j: j[1]["victorias_atacante"], reverse=True)  # FIX: clave correcta
        return lista[:5]
