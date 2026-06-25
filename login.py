import json #Librería para guardar a los usuarios y otra información
import os #Librería que comprueba la existencia de archivos

class Gestion:
    def __init__(self, archivo = "jugadores.json"): #Crea el archivo que guarda la info de inicio de sesión
        self.archivo = archivo
        self.jugadores = self.cargar_jugadores()
