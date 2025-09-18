# Paquete de Análisis para ChatGPT - Problema de Backtest RSI

## Resumen del Problema

Has obtenido resultados de backtest imposibles con una estrategia RSI de 30 minutos:
- **Total Return**: -$999,999.00 (-139,269.32%)
- **Win Rate**: 11.9% (1,269/10,666 trades)
- **Max Drawdown**: -$153,302.37 (-153.30%)

## Archivos del Motor de Backtest

### 1. Motor Principal
**Archivo**: `strategies/backtest_engine.py`
- **Líneas 647-655**: Limitación artificial de valores a ±999,999
- **Líneas 987-1016**: Cálculo de position size (máximo 20 contratos)
- **Líneas 238-249**: Cálculo de P&L para ES (puntos × $50 × cantidad)
- **Líneas 907-915**: Cálculo de RSI

### 2. Calculadora de Métricas
**Archivo**: `strategies/metrics_calculator.py`
- Cálculo de todas las métricas de performance
- Rating de estrategias
- Cálculo de ratios (Sharpe, Sortino, etc.)

### 3. Modelos de Datos
**Archivo**: `strategies/models.py`
- Definición de Strategy, BacktestResult, Trade
- Campos de base de datos

## Problema Principal Identificado

### Limitación Artificial de Valores
```python
# En backtest_engine.py líneas 647-655
if abs(value) > 999999:
    value = 999999 if value > 0 else -999999
```

**Explicación**: El motor limita automáticamente cualquier valor mayor a ±999,999 para evitar overflow de la base de datos. Esto significa que pérdidas reales de -$1,000,000+ se muestran como -$999,999.

### Cálculo de Position Size Excesivo
```python
# En backtest_engine.py líneas 987-1016
MAX_CONTRACTS = 20  # límite de seguridad
risk_pct = 0.01  # 1% risk per trade
# Con stop loss de 2 puntos y capital de $100,000:
# 100,000 * 0.01 / (2 * 50) = 10 contratos
# Pero puede llegar hasta 20 contratos
```

### Cálculo de P&L para ES
```python
# En backtest_engine.py líneas 238-249
raw_points = (exit_price - entry_price) * side_sign
pnl = raw_points * ES_POINT_VALUE * current_position['quantity']
# P&L = puntos × $50 × cantidad
# Con 20 contratos y 100 puntos = $100,000
```

## Datos de Entrada del Backtest

### Estrategia RSI
- **Condición**: RSI 30 < 30
- **Timeframe**: 30 minutos
- **Símbolo**: ES (E-mini S&P 500)
- **Stop Loss**: 2 puntos
- **Take Profit**: 4 puntos
- **Capital inicial**: $100,000

### Parámetros de ES
- **Valor por punto**: $50
- **Tick size**: 0.25 puntos
- **Comisión**: $4 por round turn
- **Slippage**: 0.5 puntos

## Análisis de Simulación

He creado una simulación con datos realistas que muestra:
- **19 señales de entrada** en 1000 períodos (30min)
- **P&L normal**: entre -$157 y +$168 por trade
- **Retorno realista**: 0.11% en el período de prueba

## Soluciones Recomendadas

### 1. Eliminar Limitación de Valores
```python
def _safe_decimal(self, value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == float('inf') or value == float('-inf'):
            return Decimal('0')
        if np.isnan(value):
            return Decimal('0')
        # REMOVER la limitación artificial de ±999999
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, OverflowError):
        return Decimal('0')
```

### 2. Revisar Cálculo de Position Size
```python
def _position_size(self, strategy, row, entry_price):
    MAX_CONTRACTS = 5  # Reducir de 20 a 5
    risk_pct = 0.005  # Reducir de 1% a 0.5%
    
    # Validación adicional
    if stop_val <= 0 or stop_val > 50:
        return 1
```

### 3. Añadir Validación de Datos
```python
def _validate_backtest_data(self, df, strategy):
    # Validar RSI
    if 'rsi_30' in df.columns:
        rsi_values = df['rsi_30'].dropna()
        if len(rsi_values) == 0 or rsi_values.isna().all():
            raise ValueError("RSI calculation failed")
    
    # Validar precios realistas
    if df['close'].min() < 1000 or df['close'].max() > 10000:
        raise ValueError("Unrealistic price data")
```

## Archivos para Revisar

1. **`strategies/backtest_engine.py`** - Motor principal (líneas 647-655, 987-1016, 238-249)
2. **`strategies/metrics_calculator.py`** - Cálculo de métricas
3. **`strategies/models.py`** - Modelos de datos
4. **`market_data/parquet_service.py`** - Servicio de datos

## Preguntas para ChatGPT

1. **¿Por qué el motor está generando position sizes de hasta 20 contratos?**
2. **¿Cómo corregir el cálculo de P&L para evitar valores extremos?**
3. **¿Es correcto limitar valores a ±999,999 o debería usar valores reales?**
4. **¿Cómo validar que el RSI se está calculando correctamente?**
5. **¿Qué límites realistas debería tener el position size para ES?**

## Conclusión

El problema principal es que el motor está generando position sizes excesivos (hasta 20 contratos) que, combinados con movimientos de precio normales, generan P&L extremos que luego se limitan artificialmente a ±999,999. Esto crea resultados de backtest irreales e imposibles.

La solución requiere:
1. Eliminar la limitación artificial de ±999,999
2. Revisar el cálculo de position size
3. Añadir validación de datos de entrada
4. Implementar límites más realistas
