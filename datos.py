import os
import csv
from utils import *
from config import *

def guardar_ventas(nueva_venta, fecha, hora, id_venta, tipo = "piezas"):
    archivo_ventas = "ventas_individuales.csv"
    existe = os.path.exists(archivo_ventas)
       
    with open(archivo_ventas, "a", newline="", encoding='utf-8') as f:
        escritor = csv.writer(f)
        
        # Generador de encabezados: solo si el archivo es nuevo
        if not existe:
            escritor.writerow(["id_venta", "fecha", "hora", "piezas","cajas", "total", "estado","tipo"])

        escritor.writerow([
            id_venta,
            fecha, 
            hora, 
            nueva_venta["piezas"],
            nueva_venta["cajas"], 
            nueva_venta["total"],
            "abierta",  # Marcamos la venta como pendiente de corte
            tipo
        ])
        
def guardar_corte(fecha,ventas):
    
    piezas_vendidas, cajas_vendidas, total_dia = calcular_resumen_piezas(ventas)

    total_dia = total_dia
    archivo = 'cortes.csv'
    
    # Verificamos si es la primera vez que creamos el archivo
    
    existe = os.path.exists(archivo)
    
    with open(archivo, 'a') as f:
        
        # Si no existe, escribimos los encabezados primero
        if not existe:
            f.write("Fecha,Piezas Vendidas,Cajas Vendidas,Total Dia\n")
            
        f.write(f"{fecha},{piezas_vendidas},{cajas_vendidas},{total_dia}\n")
    
    if existe:
        print("El cierre contable ha sido actualizado correctamente.\n")
    else:
        print("El archivo de cierres ha sido creado y el primer registro guardado.\n")
        
def recuperar_ventas_pendientes():
    ventas_recuperadas = []
    archivo = 'ventas_individuales.csv'
    
    if not os.path.exists(archivo):
        return []

    try:
        with open(archivo, mode="r", encoding="utf-8") as f:
            # Usamos DictReader para leer por nombres de columna
            lector = csv.DictReader(f)
            
            for fila in lector:
                # Verificamos que la fila no esté vacía y tenga la llave 'estado'
                if fila and 'estado' in fila:
                    if fila['estado'].strip() == "abierta":
                        ventas_recuperadas.append({
                            "piezas": int(fila['piezas']),
                            "cajas" :int(fila['cajas']),
                            "total": float(fila['total'])
                        })
    except Exception as e:
        print(f"Aviso: No se pudo recuperar alguna venta del historial: {e}")
        
    return ventas_recuperadas

def marcar_ventas_como_cerradas():
    archivo = 'ventas_individuales.csv'
    
    if not os.path.exists(archivo): 
        print("Error: El archivo no existe.")
        return

    registros_actualizados = []
    
    # Leemos todo el contenido y lo guardamos en memoria
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            columnas = lector.fieldnames
            for fila in lector:
                # Usamos .strip() por si hay espacios invisibles
                if fila['estado'].strip() == "abierta":
                    fila['estado'] = "cerrada"
                registros_actualizados.append(fila)
        
        # Sobrescribimos el archivo con los datos modificados
        with open(archivo, 'w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=columnas)
            escritor.writeheader()
            escritor.writerows(registros_actualizados)
            
        print("Ventas marcadas como cerradas en el historial.")

    except Exception as e:
        print(f"Error al cerrar ventas: {e}")
        
def leer_cortes():
    
    print("\n" + "="*49)
    print(f"{'HISTÓRICO DE CIERRES CONTABLES':^49}")
    print("="*49)
    
    if not os.path.exists('cortes.csv'):
        print("Aviso: No se encontró el archivo de registros históricos.")
        return
    
    try:
        with open('cortes.csv', mode="r", encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            
            next(lector)  # CORREGIDO: salta la fila de encabezados para evitar crash en float()
            
            header = f"{'Fecha':<12} | {'Piezas':>8} | {'Cajas':>8} | {'Total':>12}"
            print(header)
            
            for fila in lector:
                    # <12 (alineado a la izquierda, 12 espacios)
                    # >8  (alineado a la derecha, 8 espacios)
                    # >12 (alineado a la derecha, 12 espacios)
                    fecha = fila[0]
                    piezas = fila[1]
                    cajas = fila[2]
                    total = f"${float(fila[3]):.2f}"
                    
                    print(f"{fecha:<12} | {piezas:>8} | {cajas:>8} | {total:>12}")
                    
    except FileNotFoundError:
        print("Aviso: No se encontró el archivo de registros históricos.")
    print("="*49 + "\n")