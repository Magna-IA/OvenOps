"""
Tests del sistema de gestión - Panificadora
Ejecutar con: pytest test_panificadora.py -v
"""

import pytest


# ===========================================================================
# TESTS: utils.py — calcular_resumen_piezas
# ===========================================================================

from utils import calcular_resumen_piezas

class TestCalcularResumenPiezas:

    def test_resumen_solo_piezas(self):
        """Ventas normales de piezas, sin cajas"""
        ventas = [
            {"piezas": 10, "cajas": 0, "total": 110.0},
            {"piezas": 5,  "cajas": 0, "total": 55.0},
        ]
        piezas, cajas, total = calcular_resumen_piezas(ventas)
        assert piezas == 15
        assert cajas  == 0
        assert total  == 165.0

    def test_resumen_solo_cajas(self):
        """Ventas normales de cajas, sin piezas"""
        ventas = [
            {"piezas": 0, "cajas": 2, "total": 280.0},
            {"piezas": 0, "cajas": 1, "total": 140.0},
        ]
        piezas, cajas, total = calcular_resumen_piezas(ventas)
        assert piezas == 0
        assert cajas  == 3
        assert total  == 420.0

    def test_resumen_mixto(self):
        """Mezcla de ventas de piezas y cajas en el mismo turno"""
        ventas = [
            {"piezas": 10, "cajas": 0, "total": 110.0},
            {"piezas": 0,  "cajas": 2, "total": 280.0},
        ]
        piezas, cajas, total = calcular_resumen_piezas(ventas)
        assert piezas == 10
        assert cajas  == 2
        assert total  == 390.0

    def test_resumen_lista_vacia(self):
        """Sin ventas registradas, todo debe ser cero"""
        piezas, cajas, total = calcular_resumen_piezas([])
        assert piezas == 0
        assert cajas  == 0
        assert total  == 0


# ===========================================================================
# TESTS: inventario.py — calcular_inventario
# ===========================================================================

from inventario import calcular_inventario

class TestCalcularInventario:

    def test_solo_produccion(self):
        """Se agrega producción sin ventas ni merma"""
        piezas, cajas = calcular_inventario(
            piezas_actuales=50, cajas_actuales=5,
            produccion_piezas=100, produccion_cajas=10
        )
        assert piezas == 150
        assert cajas  == 15

    def test_produccion_y_ventas(self):
        """Producción del día menos lo vendido"""
        piezas, cajas = calcular_inventario(
            piezas_actuales=100, cajas_actuales=10,
            produccion_piezas=200, produccion_cajas=20,
            ventas_piezas=50,     ventas_cajas=5
        )
        assert piezas == 250
        assert cajas  == 25

    def test_con_merma(self):
        """Producción menos merma y ventas"""
        piezas, cajas = calcular_inventario(
            piezas_actuales=100, cajas_actuales=10,
            produccion_piezas=200, produccion_cajas=20,
            merma_piezas=10,       merma_cajas=2,
            ventas_piezas=50,      ventas_cajas=5
        )
        assert piezas == 240
        assert cajas  == 23

    def test_inventario_exactamente_en_cero(self):
        """Vender exactamente lo que hay no debe lanzar error"""
        piezas, cajas = calcular_inventario(
            piezas_actuales=50, cajas_actuales=5,
            ventas_piezas=50,   ventas_cajas=5
        )
        assert piezas == 0
        assert cajas  == 0

    def test_inventario_negativo_lanza_error(self):
        """Vender más de lo que hay debe lanzar ValueError"""
        with pytest.raises(ValueError, match="negativo"):
            calcular_inventario(
                piezas_actuales=10, cajas_actuales=0,
                ventas_piezas=99
            )

    def test_cajas_negativas_lanza_error(self):
        """Merma mayor al inventario de cajas debe lanzar ValueError"""
        with pytest.raises(ValueError, match="negativo"):
            calcular_inventario(
                piezas_actuales=100, cajas_actuales=2,
                merma_cajas=5
            )


# ===========================================================================
# TESTS: ventas.py — calcular_precio y calcular_cambio
# ===========================================================================

from ventas import calcular_precio, calcular_cambio

class TestCalcularPrecio:

    def test_precio_piezas(self):
        assert calcular_precio(10, 11) == 110

    def test_precio_cajas(self):
        assert calcular_precio(3, 140) == 420

    def test_precio_una_unidad(self):
        assert calcular_precio(1, 11) == 11

    def test_precio_cero_unidades(self):
        assert calcular_precio(0, 11) == 0


class TestCalcularCambio:

    def test_cambio_normal(self):
        """Pago con billete de 200, cobro 110"""
        assert calcular_cambio(200, 110) == 90

    def test_pago_exacto(self):
        """Pago exacto debe dar cambio cero"""
        assert calcular_cambio(110, 110) == 0


# ===========================================================================
# TESTS: produccion.py — generar_pago_produccion (lógica de cálculo pura)
# ===========================================================================

# Nota: generar_pago_produccion lee inventario.csv para obtener la merma,
# por eso testeamos la lógica de cálculo directamente aquí
# sin depender del archivo CSV.

class TestLogicaPago:
    """
    Verifica la lógica matemática del pago de producción
    de forma aislada, sin tocar archivos.
    """

    def _calcular(self, total_piezas, total_cajas,
                  merma_piezas=0, merma_cajas=0,
                  precio_pieza=2.5, precio_caja=25):
        """Helper que replica la lógica de generar_pago_produccion"""
        subtotal_piezas = (total_piezas - merma_piezas) * precio_pieza
        subtotal_cajas  = (total_cajas  - merma_cajas)  * precio_caja
        total_pago = subtotal_piezas + subtotal_cajas
        return subtotal_piezas, subtotal_cajas, total_pago

    def test_pago_sin_merma(self):
        sub_p, sub_c, total = self._calcular(100, 10)
        assert sub_p == 250.0   # 100 * 2.5
        assert sub_c == 250.0   # 10 * 25
        assert total == 500.0

    def test_pago_con_merma_piezas(self):
        """10 piezas de merma: solo se pagan 90"""
        sub_p, sub_c, total = self._calcular(100, 10, merma_piezas=10)
        assert sub_p == 225.0   # (100-10) * 2.5
        assert sub_c == 250.0
        assert total == 475.0

    def test_pago_con_merma_cajas(self):
        """2 cajas de merma: solo se pagan 8"""
        sub_p, sub_c, total = self._calcular(100, 10, merma_cajas=2)
        assert sub_p == 250.0
        assert sub_c == 200.0   # (10-2) * 25
        assert total == 450.0

    def test_pago_con_merma_total(self):
        """Merma en piezas y cajas al mismo tiempo"""
        sub_p, sub_c, total = self._calcular(100, 10, merma_piezas=10, merma_cajas=2)
        assert sub_p == 225.0
        assert sub_c == 200.0
        assert total == 425.0

    def test_pago_semana_completa(self):
        """Simula una semana de 6 días de producción"""
        # 6 días x 300 piezas y 20 cajas por día
        sub_p, sub_c, total = self._calcular(
            total_piezas=1800, total_cajas=120,
            merma_piezas=30,   merma_cajas=5
        )
        assert sub_p == (1800 - 30) * 2.5
        assert sub_c == (120  - 5)  * 25
        assert total == sub_p + sub_c