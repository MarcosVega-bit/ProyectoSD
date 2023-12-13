import socket
import threading
import sqlite3
import time

bd = sqlite3.connect('/home/marcos_25/base.sqlite', check_same_thread=False)
cur = bd.cursor()

# Configuración de los servidores en cada máquina virtual
hosts = [
    "192.168.159.130",
    "192.168.159.134",
    "192.168.153.130",
    "192.168.153.131"
]
port = [      # Puerto para la comunicación entre las máquinas
    1111,
    2222,
    3333,
    4444
]

names = [    # Nombres dehost de las máquinas
    "VM1",
    "VM2",
    "VM3",
    "VM4"
]

maestro = False  # Indica si el nodo actual es el maestro

def cliente(conn, addr):    # Función de cliente, detecta cuando llega un mensaje al servidor desde cualquiera de las 4 máquinas virtuales
     global maestro
     hn = socket.gethostname()
     print(f'Conectado por {addr}')
     while True:
        data = conn.recv(1024)
        if not data:
            break
        received_message = data.decode()
        str = received_message.split(sep=' ')
        
        if str[1] == 'cliente':    # Detección del comando cliente para agregar un nuevo cliente a la base
            id = str[2]
            n = str[3]
            p = str[4]
            m = str[5]
            bd.execute('BEGIN EXCLUSIVE TRANSACTION')
            cur.execute('INSERT INTO CLIENTE (idCliente, nombre, apPaterno, apMaterno) VALUES (?,?,?,?)',(id,n,p,m)) # Inserción del nuevo ciente 
            bd.commit()
            print("Se agrego el cliente ",n," ",p," ",m," correctamente")
            
        elif str[1] == 'articulo':    # Detección del comando articulo para agregar un nuevo articulo en general
            w = getSucId(hn)
            id = str[2]
            a = str[3]
            b = str[4]
            n = int(b)
            m = len(hosts)
            t = [n//m]*m
            r = n % m
            for z in range(r): # Distribución del total de articulos entre las 4 sucursales
                t[z] += 1
            bd.execute('BEGIN EXCLUSIVE TRANSACTION')
            cur.execute('INSERT INTO ARTICULO (idArticulo, nombre, total) VALUES (?,?,?)',(id,a,b))    # Inserción del articulo en el inventario general
            cur.execute('INSERT INTO INVENTARIO (idSucursal, idArticulo, cantidad) VALUES (?,?,?)',(w,id,t[w-1])) # Inserción de los articulos correspondientes a una sucursal
            bd.commit()
            print("Se agrego el articulo ",a," correctamente.")
            
        elif str[1] == 'compra':    # Detección del comando compra para realizar la compra de un articulo en una sucursal
            id = str[2]
            c = str[3]
            h = str[4]
            cl = str[5]
            cn = int(c)
            suc = getSucId(h)
            cur.execute('SELECT total FROM ARTICULO WHERE idArticulo = ?',(id, ))
            a = cur.fetchone()
            t = a[0]
            cur.execute('SELECT cantidad FROM INVENTARIO WHERE idArticulo = ?',(id, ))
            a = cur.fetchone()
            tl = a[0]
            if (h == hn) and ((tl - cn) < 0):
                print("\nEn el inventario de este nodo no es suficiente para tu compra. Intenta en otro nodo o reduce el numero de articulos de tu compra")
            elif (h == hn) and ((tl - cn) >= 0):
                bd.execute('BEGIN EXCLUSIVE TRANSACTION')
                cur.execute('UPDATE ARTICULO SET total = ? WHERE idArticulo = ?',(t-cn,id))    # Actualización del inventario general
                cur.execute('UPDATE INVENTARIO SET cantidad = ? WHERE idArticulo = ?',(tl-cn,id))    # Actualización del inventario de la sucursal
                cur.execute('INSERT INTO ENVIO (idArticulo, idSucursal, idCliente) VALUES (?,?,?)',(id,suc,cl))
                bd.commit()
                print("La compra se realizo correctamente.")
            elif (h != hn) and ((tl - cn) >= 0):
                bd.execute('BEGIN EXCLUSIVE TRANSACTION')
                cur.execute('UPDATE ARTICULO SET total = ? WHERE idArticulo = ?',(t-cn,id))
                cur.execute('INSERT INTO ENVIO (idArticulo, idSucursal, idCliente) VALUES (?,?,?)',(id,suc,cl))
                bd.commit()
        
        # Almacenar mensaje recibido en un archivo
        with open(f"/home/marcos_25/msgs.txt", "a") as file:
            file.write(f"[Recibido] {time.strftime('%Y-%m-%d_%H:%M:%S')} - {received_message}\n")
        
        # Enviar un mensaje de confirmación al cliente
        confirmation_message = "El mensaje fue recibido"
        conn.sendall(confirmation_message.encode())
        print(f'Mensaje de confirmación enviado a {addr}: {confirmation_message}')
        if maestro:
            print("¡Alerta! El maestro actual ha fallado. Iniciando proceso de elección de maestro...")
        # Lógica para elegir el nuevo maestro, basada en el hostname en este ejemplo
        nuevo_maestro = names[0]  # Elige siempre el primer nodo como nuevo maestro (ajusta según necesites)
        if nuevo_maestro == hn:
            maestro = True
            print(f"Soy el nuevo maestro en {hn}")
        else:
            print(f"{nuevo_maestro} se convirtió en el nuevo maestro.")
    
        conn.close()

def servidor(host, port):        # Función para levantar el servidor
    global maestro
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(5)
        print(f"Servidor escuchando en {host}:{port}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=cliente, args=(conn, addr))
            client_thread.start()
        if maestro == 0:
        iniciar_eleccion()

def mensaje(server_ip, server_port, message):        # Función para mandar mensajes 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        t = time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
        mt = f"[{t}] {message}"
        s.sendall(mt.encode())
        print(f"Mensaje enviado a {server_ip}:{server_port}: {mt}")
        
        # Almacenar mensaje enviado en un archivo
        with open(f"/home/marcos_25/msgs.txt", "a") as file:
            file.write(f"[Enviado] {t} - {message}\n")
        
        response = s.recv(1024)
        decoded_response = response.decode()
        print(f"Respuesta del servidor {server_ip}:{server_port}: {decoded_response}")
        
        # Almacenar mensaje de confirmación recibido en un archivo
        with open(f"/home/eduardo/msgs.txt", "a") as file:
            file.write(f"[Recibido] {time.strftime('%Y-%m-%d_%H:%M:%S')} - {decoded_response}\n")

def getSucId(hn):    # Funcion para obtener el idSucursal a partir del hostname de la máquina virtual
    n = -1
    if (hn == names[0]):
        n = 1
    elif (hn == names[1]):
        n = 2
    elif (hn == names[2]):
        n = 3
    elif (hn == names[3]):
        n = 4
    return n

# Lógica para iniciar el servidor según la máquina virtual
if __name__ == "__main__":
    hn = socket.gethostname()
    if hn == names[0]:
        maestro = True
    servidor_thread = threading.Thread(target=servidor, args=(hosts[0], port[0]))
    servidor_thread.start()
