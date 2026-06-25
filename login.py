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

    def registrar_usuario(self, usuario, contraseña): #Función que registra un nuevo jugador en el sistema
        
        usuario = usuario.strip() #Elimina espacios innecesarios al inicio y al final del usuario

        if usuario == "" or contraseña == "": #Verifica que el usuario y la contraseña tengan contenido
            print("Coloque un nombre de usuario y contraseña válidos")
            return False
        
        if usuario in self.jugadores: #Comprueba que el nombre de usuario no esté registrado
            print("Este usuario ya se encuentra registrado")
            return False
        
        self.jugadores[usuario] = { #Guarda la contraseña y establece las victorias iniciales en cero
            "contraseña": contraseña,
            "victorias_defensor": 0,
            "victorias_atacante": 0
        }

#Actualiza el archivo .json con el nuevo jugador
        self.guardar_jugador()
        print("Usuario registrado correctamente")
        return True
    
    def iniciar_sesion(self, usuario, contraseña): #Función que verifica los datos para iniciar sesión
        usuario = usuario.strip()

        if usuario not in self.jugadores:
            print("El usuario no se encuentra registrado")
            return False
        
        #Compara la contraseña ingresada con la contraseña guardada
        if self.jugadores[usuario]["contraseña"] != contraseña:
            print("Contraseña incorrecta. Inténtelo de nuevo.")
            return False
        
        print("Sesión iniciada correctamente")  #Si los datos son correctos, permite iniciar sesión
        return True
    
    def info_jugador(self, usuario):
        if usuario not in self.jugadores:
            return None
            
        return self.jugadores[usuario]
    
    def sumar_victorias(self, usuario, rol): #Función que aumenta las victorias del jugador según su rol
        if usuario not in self.jugadores:
            print("Jugador no existente")
            return False
        
        rol = rol.lower().strip() #Convierte el rol a minúscula y elimina espacios innecesarios

        if rol == "defensor":
            self.jugadores[usuario]["victorias_defensor"] += 1 

        elif rol == "atacante":
            self.jugadores[usuario]["victoias_atacante"] += 1

        else:
            print("El rol no es válido") #Evita guardar un rol distinto de defensor o atacante
            return False
        
        self.guardar_jugador() #Guarda la nueva cantidad de victorias en el archivo
        print(f"Victoria como {rol} agregada a {usuario} correctamente")
    
    def top_defensores(self): #Función que obtiene los cinco jugadores con más victorias como defensor
        lista = list(self.jugadores.items())

        lista.sort( #Ordena a los jugadores de mayor a menor según sus victorias
            key=lambda jugador: jugador[1]["victorias_defensor"],
            reverse=True
            )

        return lista[:5]
    
    def top_atacantes(self): #Función que obtiene los cinco jugadores con más victorias como atacante
        lista = list(self.jugadores.items())

        lista.sort(
            key=lambda jugador: jugador[1]["victorias_atacante"],
            reverse=True
        )

        return lista[:5] #Retorna únicamente los primeros cinco jugadores
