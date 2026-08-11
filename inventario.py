import os
import csv


def leer_inventario():
    archivo = "inventario.csv"

    if not os.path.exists(archivo):
        return {"piezas": 0, "cajas": 0}

    with open(archivo, "r", encoding="utf-8") as f:
        lector = list(csv.DictReader(f))

        if not lector:
            return {"piezas": 0, "cajas": 0}

        ultimo = lector[-1]

        return {
            "piezas": int(ultimo["inventario_piezas"]),
            "cajas": int(ultimo["inventario_cajas"]),
        }


def calcular_inventario(
    piezas_actuales,
    cajas_actuales,
    produccion_piezas=0,
    produccion_cajas=0,
    merma_piezas=0,
    merma_cajas=0,
    ventas_piezas=0,
    ventas_cajas=0,
):

    nuevas_piezas = piezas_actuales + produccion_piezas - merma_piezas - ventas_piezas
    nuevas_cajas = cajas_actuales + produccion_cajas - merma_cajas - ventas_cajas

    if nuevas_piezas < 0 or nuevas_cajas < 0:
        raise ValueError("Inventario no puede ser negativo")

    return nuevas_piezas, nuevas_cajas


def guardar_snapshot_diario(
    fecha,
    piezas_anteriores,
    cajas_anteriores,
    produccion_piezas,
    produccion_cajas,
    merma_piezas,
    merma_cajas,
    ventas_piezas,
    ventas_cajas,
    inventario_piezas,
    inventario_cajas,
):

    archivo = "inventario.csv"
    existe = os.path.exists(archivo)

    with open(archivo, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        if not existe:
            escritor.writerow(
                [
                    "fecha",
                    "piezas_anteriores",
                    "cajas_anteriores",
                    "produccion_piezas",
                    "produccion_cajas",
                    "merma_piezas",
                    "merma_cajas",
                    "ventas_piezas",
                    "ventas_cajas",
                    "inventario_piezas",
                    "inventario_cajas",
                ]
            )

        escritor.writerow(
            [
                fecha,
                piezas_anteriores,
                cajas_anteriores,
                produccion_piezas,
                produccion_cajas,
                merma_piezas,
                merma_cajas,
                ventas_piezas,
                ventas_cajas,
                inventario_piezas,
                inventario_cajas,
            ]
        )


def registrar_movimiento_inventario(
    fecha,
    produccion_piezas,
    produccion_cajas,
    merma_piezas=0,
    merma_cajas=0,
    ventas_piezas_hoy=0,
    ventas_cajas_hoy=0,
):
    """
    Calcula y guarda el snapshot diario al registrar producción y merma.
    Resta las ventas acumuladas del día.
    """
    inventario_actual = leer_inventario()

    nuevas_piezas, nuevas_cajas = calcular_inventario(
        inventario_actual["piezas"],
        inventario_actual["cajas"],
        produccion_piezas=produccion_piezas,
        produccion_cajas=produccion_cajas,
        merma_piezas=merma_piezas,
        merma_cajas=merma_cajas,
        ventas_piezas=ventas_piezas_hoy,
        ventas_cajas=ventas_cajas_hoy,
    )

    guardar_snapshot_diario(
        fecha,
        inventario_actual["piezas"],
        inventario_actual["cajas"],
        produccion_piezas,
        produccion_cajas,
        merma_piezas,
        merma_cajas,
        ventas_piezas_hoy,
        ventas_cajas_hoy,
        nuevas_piezas,
        nuevas_cajas,
    )
    
    guardar_movimiento_historico(fecha, "produccion", produccion_piezas, produccion_cajas, merma_piezas, merma_cajas)
    
    if ventas_piezas_hoy or ventas_cajas_hoy:
        guardar_movimiento_historico(fecha, "venta_publico", ventas_piezas_hoy, ventas_cajas_hoy)

    return {"inventario_piezas": nuevas_piezas, "inventario_cajas": nuevas_cajas}


#============================   
# REGISTROS PARA FORECASTING    
#============================   

ARCHIVO_HISTORICO = "historial_movimientos.csv"

def guardar_movimiento_historico(fecha,tipo_movimiento, piezas, cajas, merma_piezas=0, merma_cajas=0):
    """
    Guarda un registro histórico de movimientos para análisis y forecasting.
    """
    existe = os.path.exists(ARCHIVO_HISTORICO)

    with open(ARCHIVO_HISTORICO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        if not existe:
            escritor.writerow(
                [
                    "fecha",
                    "tipo_movimiento",
                    "piezas",
                    "cajas",
                    "merma_piezas",
                    "merma_cajas"
                ])

        escritor.writerow(
            [
                fecha,
                tipo_movimiento,
                piezas,
                cajas,
                merma_piezas,
                merma_cajas
            ])