from netifaces import interfaces, ifaddresses, AF_INET
import socket
import threading
import sqlite3
import random
import MWf

bd = sqlite3.connect('/home/marcos_25/base.sqlite')
cur = bd.cursor()
idP = 1
idC = 1

if __name__ == "__main__":
    # Configuración de los servidores en cada máquina virtual
    hosts = [
        "192.168.153.128",
        "192.168.153.129",
        "192.168.153.130",
        "192.168.153.131"
    ]
    port = 12345  # Puerto para la comunicación entre las máquinas

    maestro = 0  # Bandera que indica qué nodo es el maestro
    espera = True  # Bandera que espera respuesta

    cur.execute('DROP TABLE IF EXISTS PRODUCTO')
    cur.execute('DROP TABLE IF EXISTS CLIENTE')
    cur.execute('DROP TABLE IF EXISTS INVENTARIO')
    
    # Creacion de tablas
    cur.execute('CREATE TABLE PRODUCTO (idProducto INTEGER, nombre TEXT, total INTEGER)')
    cur.execute('CREATE TABLE CLIENTE (idCliente INTEGER, nombre TEXT, apPaterno TEXT, apMaterno TEXT)')
    cur.execute('CREATE TABLE INVENTARIO (idSucursal, producto INTEGER, cantidad INTEGER)')

    cur.execute('INSERT INTO PRODUCTO (idProducto, nombre, total) VALUES (?, ?, ?)', (idP, 'Zapatos', 20))
    idP += 1
    cur.execute('INSERT INTO PRODUCTO (idProducto, nombre, total) VALUES (?, ?, ?)', (idP, 'Gorra', 16))
    idP += 1
    cur.execute('INSERT INTO PRODUCTO (idProducto, nombre, total) VALUES (?, ?, ?)', (idP, 'Hoodie', 12))
    idP += 1
    cur.execute('INSERT INTO CLIENTE (idCliente, nombre, apPaterno, apMaterno) VALUES (?, ?, ?, ?)', (idC, 'Brayan', 'Ambriz', 'Zuloaga'))
    idC += 1
    cur.execute('INSERT INTO CLIENTE (idCliente, nombre, apPaterno, apMaterno) VALUES (?, ?, ?, ?)', (idC, 'Eduardo', 'Fajardo', 'Tellez'))
    idC += 1
    cur.execute('INSERT INTO CLIENTE (idCliente, nombre, apPaterno, apMaterno) VALUES (?, ?, ?, ?)', (idC, 'Marcos', 'Vega', 'Alvarez'))
    idC += 1

    i = 1
    j = -1
    while i < idP:
        cur.execute('SELECT total FROM PRODUCTO WHERE idProducto = ?', (i, ))
        a = cur.fetchone()
        n = a[0]
        m = len(hosts)
        t = [n//m] * m
        r = n % m
        hn = socket.gethostname()
        ipl = socket.gethostbyname(hn)
        if ipl == hosts[0]:
            j = 1
        elif ipl == hosts[1]:
            j = 2
        elif ipl == hosts[2]:
            j = 3
        elif ipl == hosts[3]:
            j = 4
        cur.execute('INSERT INTO INVENTARIO (idSucursal, producto, cantidad) VALUES (?, ?, ?)', (j, i, t[j-1]))
        i += 1
    bd.commit()

    # Iniciar los servidores en cada máquina virtual
    for host in hosts:
        server_thread = threading.Thread(target=MWf.servidor, args=(host, port))
        server_thread.start()

    while True:
        # Menú de selección
        print("\nBienvenido al sistema de inventarios, ¿qué deseas hacer?:")
        print("\n1. Consultar clientes")
        print("\n2. Agregar nuevo cliente")
        print("\n3. Comprar artículo")
        print("\n4. Agregar artículo\n")

        choice = input("Ingrese el número de opción correspondiente o '0' para salir: ")
        if choice == '0':
            break
        try:
            if choice == '1':
                cur.execute('SELECT * FROM CLIENTE')
                print("(idCliente, nombre, apPaterno, apMaterno)")
                for fila in cur:
                    print(fila)
            elif choice == '2':
                n = input("\nCuál es el nombre del cliente?: ")
                p = input("\nCuál es el apellido paterno del cliente?: ")
                m = input("\nCuál es el apellido materno del cliente?: ")
                cur.execute('INSERT INTO CLIENTE (idCliente, nombre, apPaterno, apMaterno) VALUES (?, ?, ?, ?)', (idC, n, p, m))
                idC += 1
                bd.commit()
                print("Se agregó el cliente", n, p, m, "correctamente")
            elif choice == '3':
                print("")  # Aquí deberías implementar la lógica para comprar artículo
            elif choice == '4':
                a = input("\nCuál es el nombre del nuevo artículo?: ")
                p = input("\nCuál es la cantidad total del producto?: ")
                cur.execute('INSERT INTO PRODUCTO (idProducto, nombre, total) VALUES (?, ?, ?)', (idP, a, p))
                idP += 1

                x = 0
                n = int(p)
                m = len(hosts)
                t = [n//m] * m
                r = n % m
                for z in range(r):
                    t[z] += 1
                while x < len(hosts):
                    cur.execute('INSERT INTO INVENTARIO (idSucursal, producto, cantidad) VALUES (?, ?, ?)', (x+1, idP-1, t[x]))
                    x += 1
                bd.commit()
                print("Se agregó el artículo", a, "correctamente.")
            elif choice == '5':
                cur.execute('SELECT * FROM INVENTARIO')
                print("(idSucursal, producto, cantidad)")
                for fila in cur:
                    print(fila)
            elif choice == '6':
                cur.execute('SELECT * FROM PRODUCTO')
                print("(idProducto, nombre, total)")
                for fila in cur:
                    print(fila)
        except ValueError:
            print("Entrada inválida. Ingrese un número válido o '0' para salir.")
