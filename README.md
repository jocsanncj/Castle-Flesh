# Castle Flesh

Castle Flesh es un juego local para dos jugadores desarrollado en Python con Tkinter.

El defensor construye torres y muros para proteger la Torre Central. El atacante compra y despliega unidades para destruirla. La partida se juega por rondas y gana quien alcance primero tres victorias.

## Funciones principales

- Registro e inicio de sesión para dos jugadores.
- Guardado de usuarios y victorias en `jugadores.json`.
- Ranking de los cinco mejores defensores y atacantes.
- Tres facciones: Humano, No muerto y Leyenda.
- Los jugadores no pueden usar la misma facción.
- Fases de construcción, despliegue y combate automático.
- Sistema de dinero, costos y recompensas.
- Sprites, animaciones y música de fondo.

## Requerimientos

Se recomienda usar Python 3.10 o superior.

Librerías utilizadas:

- Tkinter para la interfaz gráfica.
- Pillow para cargar y redimensionar imágenes.
- Pygame para reproducir música.

Instalación:

```bash
python -m pip install pillow pygame
```

En Windows también puedes usar:

```bash
py -m pip install pillow pygame
```

Tkinter normalmente viene incluido con Python en Windows. En Linux puede instalarse con:

```bash
sudo apt install python3-tk
```

## Archivos necesarios

```text
Castle-Flesh/
├── main.py
├── gestion.py
├── edificios.py
├── unidades.py
├── jugadores.json
├── Sprites/
└── Musica/
```

Todos los archivos deben permanecer dentro de la misma carpeta.

## Ejecución

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
python main.py
```

En Windows también puedes usar `py main.py`.

## Sprites

La carpeta `Sprites` debe estar junto a `main.py`. Las rutas se definen en `edificios.py` y `unidades.py`.

Se recomienda utilizar imágenes PNG con transparencia. Las unidades pueden incluir animaciones `idle`, `walking`, `slashing` y `dying`.

Si una imagen no se encuentra, el juego muestra una figura de respaldo para que la partida pueda continuar.

## Música

Coloca un archivo `.mp3`, `.ogg` o `.wav` dentro de la carpeta `Musica`.

La música intenta reproducirse automáticamente al iniciar el programa. El botón de música permite pausar, reanudar o seleccionar otro archivo.

## Flujo del juego

1. El Jugador 1 inicia sesión como defensor.
2. El Jugador 2 inicia sesión como atacante.
3. Ambos seleccionan facciones diferentes.
4. El defensor coloca torres y muros.
5. El atacante coloca unidades.
6. Inicia el combate automático.
7. La ronda termina al destruirse la Torre Central, eliminarse todas las unidades o alcanzarse el límite de turnos.
8. El primer jugador en ganar tres rondas vence la partida.

## Controles

- Clic izquierdo en la tienda: selecciona un objeto.
- Clic izquierdo en el tablero: coloca el objeto.
- Clic derecho: elimina un objeto durante la preparación y devuelve su costo.
- Botón principal: confirma construcción, despliegue o siguiente ronda.
- Botón de música: pausa o reanuda el audio.

## Usuarios y estadísticas

Los usuarios se guardan en `jugadores.json` con su contraseña y victorias como defensor y atacante.

Ejemplo:

```json
{
    "Usuario": {
        "contraseña": "clave",
        "victorias_defensor": 0,
        "victorias_atacante": 0
    }
}
```

Las contraseñas se guardan como texto porque es un proyecto local.

# Solución de problemas

# Los sprites no aparecen

Verifica que `Sprites` esté junto a `main.py`, que Pillow esté instalado y que las rutas y nombres coincidan.

# La música no suena

Verifica que Pygame esté instalado, que exista un archivo compatible y que esté dentro de `Musica`.

 `jugadores.json` está dañado

Reemplaza su contenido por:

```json
{}
```

# Créditos
Jocsan Calvo Jiménez
Ismael Mora Alvarado
