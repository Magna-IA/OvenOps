def calcular_resumen_piezas(ventas):
    """Solo suma piezas y total de la lista de ventas de piezas"""
    piezas_vendidas = sum(v["piezas"] for v in ventas)
    total_dia_piezas = sum(v["total"] for v in ventas)
    cajas_vendidas = sum(v["cajas"] for v in ventas)
    return piezas_vendidas, cajas_vendidas, total_dia_piezas 