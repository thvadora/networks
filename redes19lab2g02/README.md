# Laboratorio 2 - Redes y Sistemas Distribuidos 2019
- Federico Gonzalez Kriegel
- Mariano Piatti
- Thomas Vadora


El servidor del laboratorio consta de dos grandes partes: server.py y connection.py: el primero
inicia el socket y queda escuchando las conexiones entrantes de los clientes, dejando el manejo de la comunicación al segundo mediante su metodo "handle", el cual responde ante las peticiones de la conexión cliente.

El manejo de la comunicación, la interacción y los comandos disponibles ante los cuales el servidor responde quedan resumidos en la siguiente imagen:

![](/img/esquema.png = 230x)


###PREGUNTA 1 y Punto Estrella:
También realizamos el punto estrella, el cual consiste en aceptar múltiples conexiones de clientes por parte del servidor. Para ello, realizamos multithreading para atender las conexiones entrantes de la siguiente forma:

Incluimos las librerias:
```python
from _thread import *
import threading 
```
Incluimos la siguiente linea en server.py, el cual crea el nuevo thread, el cual va a ejecutar la función thread:
```python
start_new_thread(self.thread,(conn,addr,))
```

la cual va a dejar a cargo al objeto Connection (connection.py) el manejo de la comunicación con el cliente y luego cierra el socket de la conexión:
```python
    def thread(self, conn, addr):
        conexion= connection.Connection(conn,self.directory,addr)
        print('Conectado con el cliente: %s' % str(addr))   
        conexion.handle()               
        conn.close()                    
```

###PREGUNTA 2
La dirección IP 127.0.0.1 (también conocida como localhost) es una dirección designada para crear una red dentro de la misma computadora, es decir, sin importar la configuración de la red exterior, todo lo que se envía a 127.0.0.1 es recibido inmediatamente por la misma computadora.

Mientras tanto, la dirección 0.0.0.0 en un servidor significa que el servicio escuchará conexiones en todas las direcciones IP disponibles de la computadora, es decir, el cliente podrá conectarse a cualquiera de las direcciones IP disponibles del servidor.


