import os
import csv
from datetime import datetime
from inventario import registrar_movimiento_inventario, leer_inventario, calcular_inventario, guardar_snapshot_diario,guardar_movimiento_historico
from config import precio_pieza_reparto, precio_caja_reparto
 
ARCHIVO_REPARTO = "reparto.csv"
 
DIAS_SEMANA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}
 
# ===========================================================================
# GUARDAR SALIDA DE REPARTIDOR
# ===========================================================================
 
def registrar_salida_repartidor(fecha, nombre, id_repartidor, piezas_salida, cajas_salida):
    """
    Registra la salida de un repartidor.
    Descuenta del inventario y guarda el registro con estado 'pendiente'.
    Devuelve True si tuvo éxito, False si el inventario no alcanza.
    """
 
    # Verificar que hay suficiente inventario
    inventario_actual = leer_inventario()
 
    try:
        calcular_inventario(
            inventario_actual["piezas"],
            inventario_actual["cajas"],
            ventas_piezas=piezas_salida,
            ventas_cajas=cajas_salida
        )
    except ValueError:
        return False, "Inventario insuficiente para esta salida."
 
    # Descontar del inventario
    guardar_snapshot_diario(
        fecha,
        inventario_actual["piezas"],
        inventario_actual["cajas"],
        produccion_piezas=0,
        produccion_cajas=0,
        merma_piezas=0,
        merma_cajas=0,
        ventas_piezas=piezas_salida,
        ventas_cajas=cajas_salida,
        inventario_piezas=inventario_actual["piezas"] - piezas_salida,
        inventario_cajas=inventario_actual["cajas"] - cajas_salida
    )
    
    # Guardar registro histórico de salida
    guardar_movimiento_historico(fecha, "salida_repartidor", piezas_salida, cajas_salida)
    
    # Guardar registro en reparto.csv
    dia_semana = DIAS_SEMANA[datetime.strptime(str(fecha), "%Y-%m-%d").weekday()]
    existe = os.path.exists(ARCHIVO_REPARTO)
 
    with open(ARCHIVO_REPARTO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
 
        if not existe:
            escritor.writerow([
                "nombre", "fecha", "id_repartidor", "dia_semana",
                "piezas_salida", "cajas_salida",
                "piezas_devueltas", "cajas_devueltas",
                "merma_piezas", "merma_cajas",
                "piezas_vendidas", "cajas_vendidas",
                "total", "estado"
            ])
 
        escritor.writerow([
            nombre, fecha, id_repartidor, dia_semana,
            piezas_salida, cajas_salida,
            "", "", "", "", "", "", "", "pendiente"
        ])
 
    return True, "Salida registrada correctamente."
 
 
# ===========================================================================
# LEER REPARTIDORES PENDIENTES
# ===========================================================================
 
def leer_repartidores_pendientes():
    """
    Devuelve una lista de registros con estado 'pendiente'.
    Cada registro es un dict con todos los campos del CSV.
    """
    if not os.path.exists(ARCHIVO_REPARTO):
        return []
 
    pendientes = []
 
    try:
        with open(ARCHIVO_REPARTO, "r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                if fila["estado"].strip() == "pendiente":
                    pendientes.append(fila)
    except Exception as e:
        print(f"Error al leer repartidores pendientes: {e}")
 
    return pendientes
 
 
# ===========================================================================
# LIQUIDAR REPARTIDOR
# ===========================================================================
 
def liquidar_repartidor(nombre, id_repartidor, fecha, piezas_devueltas, cajas_devueltas, merma_piezas, merma_cajas):
    """
    Liquida un repartidor pendiente:
    - Reintegra devoluciones al inventario
    - Calcula lo realmente vendido y el total a cobrar
    - Actualiza el registro en el CSV a 'liquidado'
    Devuelve el resumen del pago o None si no encontró el registro.
    """
    if not os.path.exists(ARCHIVO_REPARTO):
        return None
 
    registros_actualizados = []
    resumen = None
 
    try:
        with open(ARCHIVO_REPARTO, "r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            columnas = lector.fieldnames
 
            for fila in lector:
                if (
                    fila["estado"].strip() == "pendiente"
                    and fila["nombre"].strip() == nombre
                    and fila["id_repartidor"].strip() == str(id_repartidor)
                    and fila["fecha"].strip() == str(fecha)
                    and resumen is None  # solo liquidamos el primero que coincida
                ):
                    piezas_salida = int(fila["piezas_salida"])
                    cajas_salida = int(fila["cajas_salida"])
 
                    piezas_vendidas = piezas_salida - piezas_devueltas - merma_piezas
                    cajas_vendidas = cajas_salida - cajas_devueltas - merma_cajas
 
                    total = (piezas_vendidas * precio_pieza_reparto) + (cajas_vendidas * precio_caja_reparto)
 
                    fila["piezas_devueltas"] = piezas_devueltas
                    fila["cajas_devueltas"] = cajas_devueltas
                    fila["merma_piezas"] = merma_piezas
                    fila["merma_cajas"] = merma_cajas
                    fila["piezas_vendidas"] = piezas_vendidas
                    fila["cajas_vendidas"] = cajas_vendidas
                    fila["total"] = round(total, 2)
                    fila["estado"] = "liquidado"
 
                    resumen = {
                        "nombre": nombre,
                        "id_repartidor": id_repartidor,
                        "fecha": fecha,
                        "piezas_vendidas": piezas_vendidas,
                        "cajas_vendidas": cajas_vendidas,
                        "piezas_devueltas": piezas_devueltas,
                        "cajas_devueltas": cajas_devueltas,
                        "merma_piezas": merma_piezas,
                        "merma_cajas": merma_cajas,
                        "total": total
                    }
 
                    # Reintegrar devoluciones al inventario
                    inventario_actual = leer_inventario()
                    nuevas_piezas = inventario_actual["piezas"] + piezas_devueltas
                    nuevas_cajas = inventario_actual["cajas"] + cajas_devueltas
 
                    guardar_snapshot_diario(
                        fecha,
                        inventario_actual["piezas"],
                        inventario_actual["cajas"],
                        produccion_piezas=piezas_devueltas,
                        produccion_cajas=cajas_devueltas,
                        merma_piezas=merma_piezas,
                        merma_cajas=merma_cajas,
                        ventas_piezas=0,
                        ventas_cajas=0,
                        inventario_piezas=nuevas_piezas,
                        inventario_cajas=nuevas_cajas
                    )
                    guardar_movimiento_historico(fecha, "devolucion_repartidor", piezas_devueltas, cajas_devueltas, merma_piezas, merma_cajas)
 
                registros_actualizados.append(fila)
 
        with open(ARCHIVO_REPARTO, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=columnas)
            escritor.writeheader()
            escritor.writerows(registros_actualizados)
 
    except Exception as e:
        print(f"Error al liquidar repartidor: {e}")
        return None
    return resumen