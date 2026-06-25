import json #Librería para guardar a los usuarios y otra información
import os #Librería que comprueba la existencia de archivos

class Gestion:
    def __init__(self, archivo = "jugadores.json"): #Crea el archivo que guarda la info de inicio de sesión
        self.archivo = archivo
        self.jugadores = self.cargar_jugadores()

    def cargar_jugadores(self): #Función que carga la info del archivo .json para cargar los jugadores

        if not os.path.exists(self.archivo): #Si el archivo no existe, no retorna nada
            return

        try:
            with open(self.archivo, "r", encoding= "uft-8") as archivo: #Si el archivo existe, lo ejecuta
                return json.load(archivo)

        except json.JSONDecodeError: #Genera un error si el archivo existe pero está vacío o dañado
            print("El archivo .json está vacío")

            return {}

        except OSError: #Genera un error si el sistema no puede abrir el archivo
            print("No es posible ejecutar el archivo")

    def guardar_jugador(self): #Función que guarda la información de todos los jugadores

        try:
            with open(self.archivo, "w", encoding= "utf-8") as archivo: #Guarda en el archivo .json los usuarios con ese formato
                json.dump(
                    self.jugadores,
                    archivo,
                    indent= 4,
                    ensure_ascii= False
                    )
                
        except OSError: #Si el archivo está dañado, da un error
            print("No fue posible guardar a los jugadores")
