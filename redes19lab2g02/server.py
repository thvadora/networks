#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
from constants import *
import os
from _thread import *
import threading


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """
    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))
        # Creación de socket
        sockserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockserver.bind((addr, port))
        self.server_connection = sockserver
        self.directory = directory
        # Si no existe el directorio, lo creo
        if not(os.path.isdir(directory)):
            os.mkdir(directory)

    def thread(self, conn, addr):
        # Creo el objeto connection
        conexion = connection.Connection(conn, self.directory, addr)
        print('Conectado con el cliente: %s' % str(addr))
        # Handleo la conexión
        conexion.handle()
        # Cierro el socket
        conn.close()

    def serve(self):
        """
        Loop principal del servidor. Se aceptan todas las conexiones entrantes,
        y se las atiende con un nuevo hilo por parte del servidor
        """
        while True:
            # Escucho conexiones entrantes con límite 0
            self.server_connection.listen()
            # Acepto la conexión
            conn, addr = self.server_connection.accept()
            # Creo un nuevo thread para atender la conexión
            start_new_thread(self.thread, (conn, addr))
        self.server_connection.close()


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
