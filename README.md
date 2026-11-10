# MediaHub - Gestor Presupuestario (Desktop Standalone) 💎

Aplicación de escritorio 100% autónoma y nativa con **PyQt6** para la gestión de presupuestos, cuentas, liquidez y seguimiento de compras en cuotas.

## 🚀 Requisitos e Instalación

1. Tener Python 3.10+ instalado.
2. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Ejecución Directa

```bash
python main.py
```

## 📦 Compilación a Ejecutable (.exe)

```bash
pyinstaller --noconfirm GestorPresupuestario.spec
```
El archivo ejecutable compilado se generará en `dist/GestorPresupuestario.exe`.

## 📦 Características de la App Independiente
* **Sin dependencias externas:** Posee sus propios módulos internos (`core`, `db`, `models`, `schemas`, `services`, `ui`).
* **Base de datos local propia:** Crea y lee directamente su base de datos SQLite en `data/budget.db` de manera independiente del servidor web.
* **Módulos incluidos:**
  * 📊 **Dashboard y Liquidez:** Saldo total, liquidez real, movimientos del mes y metas de presupuesto.
  * 💳 **Seguimiento de Cuotas:** Deudas diferidas, registro de cuotas acumuladas por meses o dinero, y botón de abono rápido de cuotas.
  * 📥 **Pendientes:** Clasificación rápida con 1 clic (`Fijo`, `Personal`, `Ahorro`, `Depósito`).
  * 💸 **Cargos y Gastos:** Registro y visualización detallada.
  * 💰 **Abonos e Ingresos:** Historial y creación de ingresos.
  * 🏦 **Cuentas y Saldos:** Control de saldos y tipos de cuentas.
