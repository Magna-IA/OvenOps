# 🥖 OvenOps

**Sistema de gestión operativa para panificadora artesanal**  
Desarrollado por René Magaña Vega

---

## ¿Qué es OvenOps?

OvenOps es un sistema de gestión diseñado para cubrir las operaciones diarias de una panificadora artesanal en Tangancícuaro, Michoacán. Nació de una necesidad real: llevar un control confiable de ventas, producción, inventario y pagos sin depender de hojas de cálculo o registros a mano.

El sistema persiste toda la información en archivos CSV, lo que lo hace portable, ligero y sin dependencias externas más allá de Python (y, para la interfaz gráfica, `customtkinter`).

Existen dos formas de correr OvenOps:
- **`interfaz.py`** — interfaz gráfica de escritorio, la forma recomendada de uso diario.
- **`Main.py`** — versión de terminal original, se conserva como alternativa ligera sin dependencias.

---

## Funcionalidades actuales

- **Interfaz gráfica de escritorio** — pantalla de Caja para venta rápida sin pop-ups, y pantalla de Administración con Producción, Reparto e Históricos
- **Registro de ventas** — por pieza y por caja, con cálculo automático de cambio
- **Cierre de caja** — resumen del turno con total acumulado y conteo de unidades
- **Recuperación ante fallos** — si el programa se cierra inesperadamente, las ventas no contabilizadas se recuperan automáticamente al reiniciar
- **Control de inventario** — snapshot diario que registra producción, merma y ventas para calcular el inventario real al cierre
- **Registro de producción** — cantidad de piezas y cajas producidas por día con estado de pago
- **Pago semanal de producción** — calcula automáticamente el pago de la semana anterior descontando merma
- **Módulo de reparto** — registro de salida de repartidores (por charola), liquidación con devoluciones y merma, integrado al inventario y al sistema de pagos
- **Espejo de datos para forecasting** — cada movimiento (producción, venta pública, salida y devolución de reparto) se registra también en `historial_movimientos.csv`, etiquetado por tipo, sin tocar la estructura de `inventario.csv`
- **Histórico de cortes y pagos** — consulta de todos los cierres contables y pagos de producción anteriores

---

## Estructura del proyecto

```
OvenOps/
│
├── interfaz.py        # Interfaz gráfica de escritorio (customtkinter)
├── Main.py             # Versión de terminal, punto de entrada alternativo
├── ventas.py           # Lógica de ventas: registro, cálculo de precio y cambio
├── datos.py            # Persistencia: lectura y escritura de CSV
├── produccion.py       # Gestión de producción y cálculo de pago semanal
├── inventario.py       # Control de inventario con snapshots diarios y espejo histórico
├── reparto.py          # Salida y liquidación de repartidores
├── utils.py            # Funciones puras de cálculo compartidas
├── config.py            # Precios y constantes centralizadas (única fuente de verdad)
│
├── test_panificadora.py  # Suite de tests con pytest
│
├── ventas_individuales.csv   # Generado automáticamente
├── cortes.csv                # Generado automáticamente
├── produccion.csv            # Generado automáticamente
├── inventario.csv            # Generado automáticamente
├── reparto.csv                # Generado automáticamente
├── pagos.csv                  # Generado automáticamente
└── historial_movimientos.csv  # Generado automáticamente (espejo para forecasting)
```

---

## Instalación y uso

**Requisitos**
- Python 3.10 o superior
- Windows 10/11
- `customtkinter` (solo para la interfaz gráfica)

**Pasos**

1. Clona o descarga el repositorio
```bash
git clone https://github.com/tu-usuario/ovenops.git
cd ovenops
```

2. Instala la dependencia de la interfaz gráfica
```bash
pip install customtkinter
```
Los CSV se generan automáticamente en el primer uso — no requieren configuración adicional.

3. Ejecuta el programa
```bash
python interfaz.py     # interfaz gráfica (recomendado)
python Main.py          # versión de terminal
```

**Para correr los tests**
```bash
python -m pip install pytest
python -m pytest test_panificadora.py -v
```

**Para generar un ejecutable de escritorio (.exe)**
```bash
pip install pyinstaller
pyinstaller --name OvenOps --windowed --collect-all customtkinter interfaz.py
```
El resultado queda en `dist/OvenOps/` — el `.exe` y sus archivos de soporte deben mantenerse juntos en esa carpeta.

---

## Configuración de precios

Todos los precios están centralizados en `config.py`. Si los precios cambian, solo hay que modificar ese archivo:

```python
precio_pieza            = 11      # Precio unitario al público
precio_pieza_reparto    = 8       # Precio para repartidores
precio_caja_publico     = 140     # Caja al público
precio_caja_reparto     = 130     # Caja para repartidores
precio_pieza_produccion = 2.5     # Pago al productor por pieza
precio_caja_produccion  = 25      # Pago al productor por caja
piezas_por_charola      = 24      # Piezas que contiene cada charola de reparto
```

---

## Decisiones técnicas

**¿Por qué CSV y no una base de datos?**  
El sistema está pensado para correr en una computadora sin configuración adicional. SQLite habría sido la siguiente opción, pero requería conocimiento técnico del operador para hacer respaldos o consultas directas. Los CSV son legibles, editables en Excel si se necesita una corrección manual, y no requieren servidor.

**¿Por qué la separación en módulos?**  
Desde el inicio se pensó en una transición futura a una interfaz gráfica. Por esa razón toda la lógica de negocio vive separada de la presentación: `interfaz.py` y `Main.py` son dos capas de presentación intercambiables sobre el mismo backend, sin duplicar lógica de cálculo ni de persistencia.

**Sistema de recuperación anti-fallos**  
Cada venta se guarda en CSV con estado `abierta` en el momento de registrarse. Al ejecutar el cierre de caja, las ventas pasan a `cerrada`. Si el programa se interrumpe antes del cierre, al reiniciar detecta las ventas `abiertas` y las recupera automáticamente a la sesión activa.

**Separación entre inventario real y datos para forecasting**  
`inventario.csv` es la fuente de verdad del inventario físico y del cálculo de pago semanal al panadero (lee merma por rango de fechas) — su estructura no se modifica. Cada movimiento que la actualiza también se copia a `historial_movimientos.csv`, etiquetado por tipo (`produccion`, `venta_publico`, `salida_repartidor`, `devolucion_repartidor`), pensado para un futuro análisis de series de tiempo sin mezclar señales de distinto origen.

---

## Roadmap — mejoras planeadas

- [ ] **Exportación de reportes** — generación de tablas y resúmenes para análisis externo
- [ ] **Análisis de datos y forecasting** — entrenar modelos de series de tiempo para predicción de demanda usando `historial_movimientos.csv` como fuente de datos estructurada

---

## Tests

El proyecto incluye una suite de tests unitarios que cubren las funciones de lógica de negocio más críticas:

| Módulo | Casos cubiertos |
|---|---|
| `utils.py` | Resumen de ventas piezas, cajas, mixto y lista vacía |
| `inventario.py` | Producción, ventas, merma, inventario en cero, inventario negativo |
| `ventas.py` | Cálculo de precio, cambio, pago exacto y cero unidades |
| `produccion.py` | Pago sin merma, con merma parcial y semana completa |

Los tests de funciones que interactúan con el sistema de archivos (lectura/escritura de CSV) están fuera del alcance de esta suite por diseño, ya que requieren técnicas de mocking que se implementarán en una versión futura.

---

## Autor

**René Magaña Vega**  
Estudiante de ingeniería — área ML / Data Science  
Proyecto personal iniciado en enero de 2026

---

> *Este proyecto fue construido para resolver un problema real. La panificadora existe, el operador existe, y los datos que genera este sistema serán la base para futuros experimentos de análisis y predicción de demanda.*
