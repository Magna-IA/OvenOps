from datetime import datetime, timedelta, date
from datos import *
from ventas import *
from config import *

def guardar_produccion(fecha, produccion, cajas):
    archivo_produccion = "produccion.csv"
    existe = os.path.exists(archivo_produccion)
    
    with open(archivo_produccion, "a", newline="", encoding='utf-8') as f:
        escritor = csv.writer(f)
     
        #Generador de CSV    
        if not existe:
            escritor.writerow(["fecha","produccion","cajas","estado"])
        
        escritor.writerow([
            fecha,
            produccion,
            cajas,
            "pendiente"
        ])

def obtener_rango_semana_anterior():
    
    hoy = date.today()
    # weekday(): lunes=0 ... domingo=6
    
    dias_desde_domingo = (hoy.weekday() + 1) % 7
    
    domingo = hoy - timedelta(days=dias_desde_domingo + 7)
    
    viernes = domingo + timedelta(days=5)
    
    return domingo, viernes

def generar_pago():
    archivo_produccion = "produccion.csv"
    archivo_pagos = "pagos.csv"
    domingo, viernes = obtener_rango_semana_anterior()


    if not os.path.exists(archivo_produccion):
        print("No existe el archivo de producción.")
        return

    registros_actualizados = []
    registros_para_pago = []

    # Leer producción y separar lo saldado
    with open(archivo_produccion, "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        columnas = lector.fieldnames

        for fila in lector:
            try:
                # Usamos .strip() por si hay espacios invisibles
                
                fecha_fila = datetime.strptime(fila["fecha"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                print(f"Error al procesar la fila: {fila}")
                registros_actualizados.append(fila)
                continue
            
            if(
                fila["estado"].strip() == "pendiente"
                and domingo <= fecha_fila <= viernes
                ):
                      
                fila['estado'] = "saldado" 
                registros_para_pago.append(fila)
 
            registros_actualizados.append(fila)
                
    if not registros_para_pago:
        return None

    # Calcular pago (función pura)
    
    #piezas_merma, cajas_merma = merma()
    
    resumen_pago = generar_pago_produccion(registros_para_pago,precio_pieza_produccion,precio_caja_produccion)

    fecha_pago = date.today().isoformat()

    # Guardar pago
    existe_pagos = os.path.exists(archivo_pagos)
    
    with open(archivo_pagos, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        
        if not existe_pagos:
            escritor.writerow([
                "fecha_pago",
                "piezas",
                "cajas",
                "subtotal_piezas",
                "subtotal_cajas",
                "total_pago"
            ])

        escritor.writerow([
            fecha_pago,
            resumen_pago["piezas"],
            resumen_pago["cajas"],
            resumen_pago["subtotal_piezas"],
            resumen_pago["subtotal_cajas"],
            resumen_pago["total_pago"]
        ])

    # Sobrescribir producción con estados actualizados
    
    with open(archivo_produccion, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(registros_actualizados)

    return {
        "fecha_pago": fecha_pago,
        **resumen_pago
    }
    
    
def generar_pago_produccion(
    registros,
    precio_pieza,
    precio_caja,
):
    
    domingo, viernes = obtener_rango_semana_anterior()
    merma_total_piezas = 0
    merma_total_cajas = 0

    with open("inventario.csv", "r", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        
        for fila in lector:
            
            try:
                fecha_fila = datetime.strptime(fila["fecha"], "%Y-%m-%d").date()
                
                if domingo <= fecha_fila <= viernes:
                    merma_total_piezas += int(fila.get("merma_piezas", 0))
                    merma_total_cajas += int(fila.get("merma_cajas", 0))
                    
            except (ValueError, KeyError):
                continue

    total_piezas = 0
    total_cajas = 0

    for r in registros:
        total_piezas += int(r['produccion'])
        total_cajas += int(r['cajas'])

    subtotal_piezas = max(0, (total_piezas - merma_total_piezas) * precio_pieza)
    subtotal_cajas = max(0, (total_cajas - merma_total_cajas) * precio_caja)

    total_pago = subtotal_piezas + subtotal_cajas

    return {
        "piezas": total_piezas,
        "cajas": total_cajas,
        "subtotal_piezas": subtotal_piezas,
        "subtotal_cajas": subtotal_cajas,
        "total_pago": total_pago
    }

