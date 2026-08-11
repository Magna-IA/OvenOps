from ventas import *
from datos import *
from produccion import *
from inventario import *
from reparto import *

ahora = datetime.now()
fecha = ahora.date()
hora = ahora.time().strftime("%H:%M:%S")

ventas = []

ventas_piezas_hoy = 0
ventas_cajas_hoy = 0


#Programa corriendo

    # --- SISTEMA DE RECUPERACIÓN ANTI-ERRORES ---
print("Verificando integridad del turno anterior...")

# Cargamos lo que esté como "abierta" en el CSV
ventas_pendientes = recuperar_ventas_pendientes()

if ventas_pendientes:
    
    # Si hay algo, lo metemos a la lista 'ventas' que usa el programa en RAM
    ventas.extend(ventas_pendientes)
    
    print(f"✅ Se han recuperado {len(ventas_pendientes)} ventas no contabilizadas.")
    
    # Mostramos de una vez cuánto dinero hay recuperado
    piezas_rec, cajas_rec, monto_rec = calcular_resumen_piezas(ventas)
    ventas_piezas_hoy += piezas_rec
    ventas_cajas_hoy += cajas_rec
    print(f"Monto recuperado: ${monto_rec:.2f} ({piezas_rec} piezas) ({cajas_rec} cajas)\n")
    
else:
    
    print("Caja limpia. Iniciando nuevo turno sin pendientes.\n")
    
while True:
    print("\n")
    print("--- PANEL DE CONTROL DE VENTAS ---")
    print("1. Registrar nueva venta")
    print("2. Registrar venta de cajas")
    print("3. Resumen del turno actual")
    print("4. Ejecutar cierre de caja y guardar")
    print("5. Consultar histórico de cortes")
    print("6. Registrar la producción del día")
    print("7. Pagar producción de la semana")
    print("8. Finalizar sesión")
    print("9. Cancelar venta")
    print("10. Registrar salida de repartidor")
    print("11. Liquidar repartidor")

    
    #Clausula Try / Except
    try:
        
        accion = int(input("Seleccione una acción: "))
        
    except ValueError:
        
        print("\nEntrada no válida. Por favor, seleccione una opción del menú.\n")        
        continue
    
    #Registrar venta
    if accion == 1:
    
        while True:
            
            venta = str(input("¿Cuantas piezas comprarán?: "))
            if venta.isdigit():
                venta = int(venta)
                
                if venta <= 0:
                    print("La cantidad debe ser mayor a cero.")
                    continue
                
                print(f'Cantidad a cobrar: {calcular_precio(venta,precio_pieza)}')
                break
            print("Cantidad inválida. Intente de nuevo.")
            
        while True:
            
            pago = str(input("¿Con cuánto pagan?: "))
            if pago.isdigit():
                pago = int(pago)
                break
            print("Monto inválido. Intente de nuevo.")
        
        confirmar = input("¿Confirmar? (S/N) ").strip().lower()
        if confirmar_venta(confirmar):
            exito, resultado = registrar_venta(
                venta,
                pago,
                ventas,
                precio_pieza,
                "piezas",
                fecha,
                hora
            )

            if exito:
                ventas_piezas_hoy += venta
                if resultado == 0:
                    print("Pago exacto. Gracias.\n")
                else:
                    print(f'\n>>>Cambio: {resultado:.2f}\n')
                
            else:
                print(resultado)
    
    elif accion == 2:
        
        while True:
            
            venta_caja_str = input("¿Cuántas cajas comprarán?: ").strip()
            if venta_caja_str.isdigit():
                
                venta_caja = int(venta_caja_str)
                if venta_caja <= 0:
                    
                    print("La cantidad debe ser mayor a cero.")
                    continue
                
                total = calcular_precio(venta_caja, precio_caja_publico)
                print(f'Cantidad a cobrar: ${total}')
                break
            
            print("Cantidad inválida.")

        while True:
            
            pago_str = input("¿Con cuánto pagan?: ").strip()
            
            if pago_str.isdigit():
                pago = int(pago_str)
                break
            print("Monto inválido.")

        confirmar = input("¿Confirmar? (S/N) ").strip().lower()
        
        if confirmar_venta(confirmar):
            exito, resultado = registrar_venta(
                venta_caja,
                pago,
                ventas,
                precio_caja_publico,
                "cajas",
                fecha,
                hora
            )
            if exito:
                ventas_cajas_hoy += venta_caja
                if resultado == 0:
                    print("Pago exacto. Gracias.\n")
                else:
                    print(f'\n>>> Cambio: ${resultado:.2f}\n')
    
    elif accion == 3:
        
        if ventas:
            mostrar_estado_caja(ventas, tipo="consulta")
            
        else:
            print("Aviso: No existen movimientos contables para visualizar el estado actual del resumen.\n")
    
    elif accion == 4:
        
        if ventas:
                              
            print(f"Iniciando proceso de cierre...")          
            mostrar_estado_caja(ventas, tipo="cierre")
            guardar_corte(fecha, ventas)
            marcar_ventas_como_cerradas()
            
            ventas.clear()
            print("Turno finalizado. Valores reiniciados para nueva jornada.\n")
            
        else:
            print("Aviso: No existen movimientos contables para realizar el corte.\n")
            
            
    elif accion == 5:
        leer_cortes()
    
    elif accion == 6:
        
        while True:
            produccion = input("Piezas producidas: ")
            if produccion.isdigit():
                produccion = int(produccion)
                break
        
        while True:
            cajas = input("Cajas producidas: ")
            if cajas.isdigit():
                cajas = int(cajas)
                break
        
        while True:
            merma_piezas = input("Merma en piezas (0 si no hubo): ")
            if merma_piezas.isdigit():
                merma_piezas = int(merma_piezas)
                break

        while True:
            merma_cajas = input("Merma en cajas (0 si no hubo): ")
            if merma_cajas.isdigit():
                merma_cajas = int(merma_cajas)
                break
        
        guardar_produccion(fecha, produccion, cajas)

        registrar_movimiento_inventario(
            fecha.isoformat(),
            produccion,
            cajas,
            merma_piezas,
            merma_cajas,
            ventas_piezas_hoy, 
            ventas_cajas_hoy
        )
        
        ventas_piezas_hoy = 0
        ventas_cajas_hoy = 0
        
        print("Inventario actualizado")
        
    elif accion == 7:
        
        resultado = generar_pago()

        if resultado is None:
            print("No hay producción pendiente para pagar.")
        else:
            print("\nPago generado correctamente")
            print(f"Fecha: {resultado['fecha_pago']}")
            print(f"Piezas: {resultado['piezas']}")
            print(f"Cajas: {resultado['cajas']}")
            print(f"Total a pagar: ${resultado['total_pago']}")

            print("El pago de producción se ha realizado con éxito.")
    
    elif accion == 8:
        print("Cerrando sistema de gestión. Hasta pronto") 
        break
        
    elif accion == 9:
        if not ventas:
            print("No hay ventas en el turno actual para cancelar.\n")
        else:
            # Mostrar lista
            print("\n--- VENTAS DEL TURNO ACTUAL ---")
            for i, v in enumerate(ventas):
                tipo = "piezas" if v["piezas"] > 0 else "cajas"
                cantidad = v["piezas"] if tipo == "piezas" else v["cajas"]
                print(f"  [{i + 1}] {cantidad} {tipo} — ${v['total']:.2f}")
            print("  [0] Cancelar (no borrar nada)")

            # Elegir
            while True:
                seleccion = input("\n¿Cuál venta desea cancelar?: ").strip()
                if seleccion.isdigit():
                    seleccion = int(seleccion)
                    if seleccion == 0:
                        print("Operación cancelada.\n")
                        break
                    if 1 <= seleccion <= len(ventas):
                        # Confirmación
                        indice = seleccion - 1
                        v = ventas[indice]
                        tipo = "piezas" if v["piezas"] > 0 else "cajas"
                        cantidad = v["piezas"] if tipo == "piezas" else v["cajas"]
                        confirmar = input(
                            f"¿Confirma cancelar {cantidad} {tipo} por ${v['total']:.2f}? (S/N): "
                        ).strip().lower()

                        if confirmar.startswith("s"):
                            exito = cancelar_venta(ventas, indice)
                            if exito:
                                print(f"✅ Venta cancelada correctamente.\n")
                            else:
                                print("Error al cancelar la venta.\n")
                        else:
                            print("Operación cancelada.\n")
                        break
                print("Selección inválida. Intente de nuevo.")
    
    elif accion == 10:
        nombre = input("Nombre del repartidor: ").strip()
        id_repartidor = input("ID del repartidor: ").strip()
        
        while True:
            charolas = input("Charolas que se lleva: ").strip()
            if charolas.isdigit():
                piezas = int(charolas) * piezas_por_charola
                break
            print("Ingresa un número válido.")
        
        while True:
            cajas = input("Cajas que se lleva (0 si ninguna): ").strip()
            if cajas.isdigit():
                cajas = int(cajas)
                break
            print("Ingresa un número válido.")
            
        if piezas == 0 and cajas == 0:
            print("Debes registrar al menos una pieza o caja.\n")
        else:
            from datetime import date
            exito, mensaje = registrar_salida_repartidor(date.today(), nombre, id_repartidor, piezas, cajas)
            print(f"{'✅' if exito else '❌'} {mensaje}\n")

    elif accion == 11:
        pendientes = leer_repartidores_pendientes()
        
        if not pendientes:
            print("No hay repartidores pendientes de liquidar.\n")
        else:
            print("\n--- REPARTIDORES PENDIENTES ---")
            for i, r in enumerate(pendientes):
                print(f"  [{i + 1}] {r['nombre']} — {r['fecha']} — "
                    f"{r['piezas_salida']} piezas, {r['cajas_salida']} cajas")
            print("  [0] Cancelar")
            
            while True:
                seleccion = input("\n¿Cuál repartidor va a liquidar?: ").strip()
                if seleccion.isdigit():
                    seleccion = int(seleccion)
                    if seleccion == 0:
                        print("Operación cancelada.\n")
                        break
                    if 1 <= seleccion <= len(pendientes):
                        r = pendientes[seleccion - 1]
                        
                        while True:
                            pd = input("Piezas que devuelve (0 si ninguna): ").strip()
                            if pd.isdigit():
                                pd = int(pd)
                                break
                            print("Ingresa un número válido.")
                        
                        while True:
                            cd = input("Cajas que devuelve (0 si ninguna): ").strip()
                            if cd.isdigit():
                                cd = int(cd)
                                break
                            print("Ingresa un número válido.")
                        
                        while True:
                            mp = input("Merma de piezas (0 si ninguna): ").strip()
                            if mp.isdigit():
                                mp = int(mp)
                                break
                            print("Ingresa un número válido.")
                        
                        while True:
                            mc = input("Merma de cajas (0 si ninguna): ").strip()
                            if mc.isdigit():
                                mc = int(mc)
                                break
                            print("Ingresa un número válido.")
                        
                        resumen = liquidar_repartidor(
                            r["nombre"], r["id_repartidor"], r["fecha"], pd, cd, mp, mc
                        )
                        
                        if resumen:
                            print(f"\n✅ Liquidación de {resumen['nombre']}:")
                            print(f"   Piezas vendidas:   {resumen['piezas_vendidas']}")
                            print(f"   Cajas vendidas:    {resumen['cajas_vendidas']}")
                            print(f"   Piezas devueltas:  {resumen['piezas_devueltas']}")
                            print(f"   Cajas devueltas:   {resumen['cajas_devueltas']}")
                            print(f"   Merma piezas:      {resumen['merma_piezas']}")
                            print(f"   Merma cajas:       {resumen['merma_cajas']}")
                            print(f"   💰 Total a cobrar: ${resumen['total']:.2f}\n")
                        else:
                            print("❌ Error al liquidar el repartidor.\n")
                        break
                print("Selección inválida. Intente de nuevo.")
    
    else:               
        print("Opción no reconocida. Intente de nuevo.\n")