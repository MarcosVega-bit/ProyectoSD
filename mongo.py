import socket
import threading
import random
from pymongo import MongoClient

# Conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mi_base_de_datos']  

idP = 1
idC = 1

if __name__ == "__main__":
    # Configuración de los servidores en cada máquina virtual
    hosts = [
        "192.168.159.130",
        "192.168.153.129",
        "192.168.153.130",
        "192.168.153.131"
    ]
    port = 12345  # Puerto para la comunicación entre las máquinas

    maestro = 0  # Bandera que indica qué nodo es el maestro
    espera = True  # Bandera que espera respuesta

    # Eliminar colecciones existentes
    db['PRODUCTO'].drop()
    db['CLIENTE'].drop()
    db['INVENTARIO'].drop()

    # Crear colecciones
    producto_col = db['PRODUCTO']
    cliente_col = db['CLIENTE']
    inventario_col = db['INVENTARIO']

    # Insertar datos iniciales
    producto_col.insert_many([
        {"idProducto": idP, "nombre": "Zapatos", "total": 20},
        {"idProducto": idP + 1, "nombre": "Gorra", "total": 16},
        {"idProducto": idP + 2, "nombre": "Hoodie", "total": 12}
    ])
    idP += 3

    cliente_col.insert_many([
        {"idCliente": idC, "nombre": "Brayan", "apPaterno": "Ambriz", "apMaterno": "Zuloaga"},
        {"idCliente": idC + 1, "nombre": "Eduardo", "apPaterno": "Fajardo", "apMaterno": "Tellez"},
        {"idCliente": idC + 2, "nombre": "Marcos", "apPaterno": "Vega", "apMaterno": "Alvarez"}
    ])
    idC += 3

    i = 1
    j = -1
    while i < idP:
        producto = producto_col.find_one({"idProducto": i})
        n = producto["total"]
        m = len(hosts)
        t = [n // m] * m
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
        inventario_col.insert_one({"idSucursal": j, "producto": i, "cantidad": t[j - 1]})
        i += 1

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
                for cliente in cliente_col.find():
                    print(cliente)
            elif choice == '2':
                n = input("\nCuál es el nombre del cliente?: ")
                p = input("\nCuál es el apellido paterno del cliente?: ")
                m = input("\nCuál es el apellido materno del cliente?: ")
                cliente_col.insert_one({"idCliente": idC, "nombre": n, "apPaterno": p, "apMaterno": m})
                idC += 1
                print(f"Se agregó el cliente {n} {p} {m} correctamente")
            elif choice == '3':
                print("")  # Aquí deberías implementar la lógica para comprar artículo
            elif choice == '4':
                a = input("\nCuál es el nombre del nuevo artículo?: ")
                p = input("\nCuál es la cantidad total del producto?: ")
                producto_col.insert_one({"idProducto": idP, "nombre": a, "total": p})
                idP += 1

                x = 0
                n = int(p)
                m = len(hosts)
                t = [n // m] * m
                r = n % m
                for z in range(r):
                    t[z] += 1
                while x < len(hosts):
                    inventario_col.insert_one({"idSucursal": x + 1, "producto": idP - 1, "cantidad": t[x]})
                    x += 1
                print(f"Se agregó el artículo {a} correctamente.")
            elif choice == '5':
                for inventario in inventario_col.find():
                    print(inventario)
            elif choice == '6':
                for producto in producto_col.find():
                    print(producto)
        except ValueError:
            print("Entrada inválida. Ingrese un número válido o '0' para salir.")
