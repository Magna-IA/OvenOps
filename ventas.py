from datetime import datetime
from config import *
from datos import *

def calcular_precio(piezas, precio):
    return piezas * precio

def calcular_cambio(total, pago):
    return pago - total 

def confirmar_venta(confirmar):
        
    if confirmar.startswith("s"):       
        return True
            
    elif confirmar.startswith("n"):
        print("Venta cancelada")
        return False
    else:
        print("Entrada no válida, por favor seleccione una opción del menú")
        return False
    
def generar_id(nueva_venta):

    #Claves de tiempo para generador de id
    ahora = datetime.now()
    anio_corto = ahora.strftime("%y")       # '26'
    mes = ahora.strftime("%m")              # '02'
    hora_corta = ahora.strftime("%H")       # '18'
    minuto = ahora.strftime("%M")           # '55'
    segundo = ahora.strftime("%S")          # '12'
    
    # Tomamos el último dígito de las piezas (ej: de 12 piezas, toma el 2)
    ultimo_digito_piezas = nueva_venta["piezas"] % 10
    
    # Generador de ID
    id_venta = f"{anio_corto}{mes}{hora_corta}{minuto}{ultimo_digito_piezas}{segundo}"
    return id_venta

def mostrar_estado_caja(ventas, tipo = "consulta"): 
    
    piezas_vendidas, cajas_vendidas, total_dia = calcular_resumen_piezas(ventas)
    
    #Título que se adapte a cada situación
    
    titulos = {
        "registro": "[SISTEMA] Actualización de ventas:",
        "consulta": "--- BALANCE PARCIAL DEL TURNO ---",
        "cierre":   "=== RESUMEN FINAL DE CIERRE DE CAJA ==="
    }
    
    prefijo = titulos.get(tipo, "Estado actual:")
    
    print(f"\n{prefijo}")
    print(f"Piezas vendidas: {piezas_vendidas} | Cajas vendidas: {cajas_vendidas} | Monto acumulado: ${total_dia:.2f}")
    
    if tipo == "cierre":
        print("Estado: Contabilizado y listo para archivo.\n")
        
    else:
        print("Estado: Caja abierta.\n")
                    #venta, pago, ventas, precio_pieza, fecha, hora
def registrar_venta(cantidad: int,
                    pago: int,
                    lista_ventas: list,           # ventas o cajas (lista donde se append el dict)
                    precio_unitario: float,
                    tipo: str,                    # "piezas" o "cajas" – para diferenciar en CSV y acumulador
                    fecha,
                    hora
                    ):
    
        total_venta = calcular_precio(cantidad, precio_unitario)      
                          
        #Método para calcular el cambio
                    
        if pago < total_venta:
            return False, "\nPago insuficiente\n"
            
        elif pago >= total_venta:
            cambio = calcular_cambio(pago, total_venta)
            
            #Creacion de Diccionario
            nueva_venta = {
                    "tipo": tipo,
                    "piezas": cantidad if tipo == "piezas" else 0,
                    "cajas": cantidad if tipo == "cajas" else 0,
                    "total": total_venta
                }
        
            lista_ventas.append(nueva_venta)
                        
            id_venta = generar_id(nueva_venta)
                    
            #Guardamos la venta individualmente
            guardar_ventas(nueva_venta, fecha, hora, id_venta, tipo=tipo)   
                                 
            mostrar_estado_caja(lista_ventas, tipo="registro")
            
            return True, cambio
        