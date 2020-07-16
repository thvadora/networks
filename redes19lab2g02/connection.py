# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import logging
from constants import *
from base64 import b64encode
import os
import threading


# Lista de errores descriptivos
error_messages = {
    0: "OK",
    100: "Se encontro un caracter \n fuera de un terminador de pedido \r\n.",
    101: "Alguna malformacion del pedido impidio procesarlo.",
    199: "El servidor fallo internamente al intentar procesar el pedido.",
    200: "El comando no esta en la lista de comandos aceptados.",
    201: "La cantidad de argumentos no corresponde o no tienen la forma correcta.",
    202: "El pedido se refiere a un archivo inexistente.",
    203: "El pedido se refiere a una posicion inexistente en un archivo.",
}


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket, directory, addr):
        # FALTA: Inicializar atributos de Connection
        self.socket_connection = socket
        self.file_directory = directory
        self.connected = True
        self.client_ip = addr[0]
        self.client_port = addr[1]
        self.buffer = ''
        self.lock = threading.Lock()

    def send(self, message, timeout=None):
        """
        Envía el mensaje 'message' al server, seguido por el terminador de
        línea del protocolo.

        Si se da un timeout, puede abortar con una excepción socket.timeout.

        También puede fallar con otras excepciones de socket.
        """
        self.socket_connection.settimeout(timeout)
        message += EOL  # Completar el mensaje con un fin de línea
        while message:
            bytes_sent = self.socket_connection.send(message.encode("ascii"))
            assert bytes_sent > 0
            message = message[bytes_sent:]

    def _recv(self, timeout=None):
        """
        Recibe datos y acumula en el buffer interno.

        Para uso privado del cliente.
        """

        self.socket_connection.settimeout(timeout)
        data = self.socket_connection.recv(4096).decode("ascii")
        self.buffer += data

        if len(data) == 0:
            self.connected = False

    def read_line(self, timeout=None):
        """
        Espera datos hasta obtener una línea completa delimitada por el
        terminador del protocolo.

        Devuelve la línea, eliminando el terminaodr y los espacios en blanco
        al principio y al final.
        """
        while EOL not in self.buffer and self.connected:
            if timeout is not None:
                t1 = time.clock()
            self._recv(timeout)
            if timeout is not None:
                t2 = time.clock()
                timeout -= t2 - t1
                t1 = t2
        if EOL in self.buffer:
            response, self.buffer = self.buffer.split(EOL, 1)
            return response.strip()
        else:
            self.send_status_message(BAD_EOL)
            return ""

    def send_status_message(self, code):
        """
        Crea el mensaje para las respuestas
        """
        if fatal_status(code):
            self.connected = False
            self.send(str(code) + " " + error_messages[code])
            return -1
        else:
            self.send(str(code) + " " + error_messages[code])
            return 0

    def get_file_listing(self):
        """
        Define el código resultante de hacer "get_file_listing" y,
        en caso de éxito, prepara los nombres de los archivos para
        ser enviados
        """
        self.files = []
        try:
            files = os.listdir(self.file_directory)
            for x in files:
                self.files.append(x)
            return CODE_OK
        except Exception:
            return FILE_NOT_FOUND

    def send_file_listing(self, status):
        """
        Envía los archivos del directorio solicitado
        """
        if(status == CODE_OK):
            self.send_status_message(status)
            for x in self.files:
                self.send(x)
            self.send('')
        else:
            self.send_status_message(status)

    def get_metadata(self, filename):
        """
        Define el código resultante de hacer "get_metadata" y,
        en caso de éxito, obtiene el tamaño del archivo.
        """
        try:
            file = os.stat(self.file_directory+'/'+filename)
            self.metadata = str(file.st_size)
            return CODE_OK
        except Exception:
            return FILE_NOT_FOUND

    def send_metadata(self, status):
        """
        Envía el tamaño del archivo solicitado por "get_metadata"
        """
        if(status == CODE_OK):
            self.send_status_message(status)
            self.send(self.metadata)
        else:
            self.send_status_message(status)

    def get_slice(self, filename, offset, size):
        """
        Define el código resultante de hacer "get_metadata" y,
        en caso de éxito, obtiene el archivo en base64.
        """
        try:
            path = self.file_directory + "/" + filename
            filesize = os.stat(path).st_size
            file = open(path, 'rb')
            if(filesize < offset + size):
                return BAD_OFFSET
            file.seek(offset)
        except Exception:
            return FILE_NOT_FOUND

        try:
            inforead = file.read(size)
            self.sendinfo = b64encode(inforead).decode("ascii")
            return CODE_OK
        except Exception:
            return INTERNAL_ERROR

    def send_slice(self, status):
        """
        Envía el bloque de archivo solicitado por "get_slice"
        """
        if(status == CODE_OK):
            self.send_status_message(status)
            self.send(self.sendinfo)
        else:
            self.send_status_message(status)

    def print_request(self, args):
        while not self.lock.acquire():
            pass

        args = args.split()
        if args[0] == "quit":
            print("Closing connection...")
        else:
            msg = "Request: "
            for x in args:
                msg = msg + " " + str(x)
            print(msg)
        self.lock.release()

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while self.connected:
            try:
                data = self.read_line()
                if "\n" in data:
                    self.send_status_message(BAD_EOL)

                argv = data.split()
                option = argv[0]

                argc = len(argv)
                if option == 'get_file_listing':
                    if argc == 1:
                        self.print_request(data)
                        print(option)
                        status = self.get_file_listing()
                        self.send_file_listing(status)
                    else:
                        self.send_status_message(INVALID_ARGUMENTS)

                elif option == 'get_metadata':
                    if(argc == 2):
                        filename = data.split()[1]
                        self.print_request(data)
                        status = self.get_metadata(filename)
                        self.send_metadata(status)
                    else:
                        self.send_status_message(INVALID_ARGUMENTS)

                elif option == 'get_slice':
                    if argc == 4:
                        try:
                            filename = argv[1]
                            offset = int(argv[2])
                            size = int(argv[3])
                        except Exception:
                            self.send_status_message(INVALID_ARGUMENTS)
                            # Si no se pudo parsear los argumentos,
                            # enviar el mensaje y código correspondiente.
                            continue
                        self.print_request(data)
                        status = self.get_slice(filename, offset, size)
                        self.send_slice(status)
                    else:
                        self.send_status_message(INVALID_ARGUMENTS)
                elif option == 'quit':
                    if argc == 1:
                        self.print_request(data)
                        self.send_status_message(CODE_OK)
                        break
                    else:
                        self.send_status_message(INVALID_ARGUMENTS)
                else:
                    self.send_status_message(INVALID_COMMAND)
            except:
                pass
                # Si el comando recibido no pertenece a ninguno de la lista,
                # enviar el mensaje y código correspondiente.
